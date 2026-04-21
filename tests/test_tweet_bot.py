import os
import unittest
from datetime import datetime

from tweet_bot import (
    BotConfigurationError,
    create_twitter_clients,
    create_tweet_with_retry,
    decide_post_action,
    fetch_today_games,
    format_target_date,
    get_target_date,
    post_action,
    refresh_oauth2_access_token,
)


def make_game(iso_time, doubleheader="N"):
    return {
        "gameDate": iso_time,
        "doubleHeader": doubleheader,
    }


class DecidePostActionTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.fromisoformat("2026-03-30T10:00:00-04:00")

    def tearDown(self):
        os.environ.pop("TARGET_DATE", None)

    def test_skips_when_no_games_exist(self):
        self.assertFalse(decide_post_action(games=[], now=self.now))

    def test_skips_when_normal_day_game_exists(self):
        games = [make_game("2026-03-30T17:05:00Z")]
        self.assertFalse(decide_post_action(games=games, now=self.now))

    def test_posts_bernie_when_only_late_games_exist(self):
        games = [make_game("2026-03-30T23:10:00Z")]
        self.assertEqual(decide_post_action(games=games, now=self.now), "bernie")

    def test_posts_larry_for_early_doubleheader_makeup(self):
        games = [
            make_game("2026-03-30T17:05:00Z", doubleheader="Y"),
            make_game("2026-03-30T23:10:00Z"),
        ]
        self.assertEqual(decide_post_action(games=games, now=self.now), "larry")

    def test_normal_day_game_overrides_doubleheader_exception(self):
        games = [
            make_game("2026-03-30T17:05:00Z", doubleheader="Y"),
            make_game("2026-03-30T18:10:00Z"),
        ]
        self.assertFalse(decide_post_action(games=games, now=self.now))

    def test_exactly_four_pm_counts_as_not_early(self):
        games = [make_game("2026-03-30T20:00:00Z")]
        self.assertEqual(decide_post_action(games=games, now=self.now), "bernie")

    def test_target_date_env_overrides_now(self):
        os.environ["TARGET_DATE"] = "2026-03-31"
        self.assertEqual(get_target_date(now=self.now).isoformat(), "2026-03-31")

    def test_invalid_target_date_raises_configuration_error(self):
        os.environ["TARGET_DATE"] = "03/31/2026"
        with self.assertRaises(BotConfigurationError):
            get_target_date(now=self.now)


class FetchTodayGamesTests(unittest.TestCase):
    def test_returns_games_from_first_schedule_date(self):
        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "dates": [
                        {
                            "games": [{"gameDate": "2026-03-30T23:10:00Z", "doubleHeader": "N"}]
                        }
                    ]
                }

        class FakeSession:
            def __init__(self):
                self.last_url = None
                self.last_timeout = None

            def get(self, url, timeout):
                self.last_url = url
                self.last_timeout = timeout
                return FakeResponse()

        session = FakeSession()
        games = fetch_today_games(
            schedule_date=datetime.fromisoformat("2026-03-30T10:00:00-04:00").date(),
            session=session,
        )

        self.assertEqual(len(games), 1)
        self.assertIn("date=2026-03-30", session.last_url)
        self.assertEqual(session.last_timeout, 10)


class RetryTests(unittest.TestCase):
    def test_retries_after_temporary_twitter_error(self):
        class TwitterServerError(Exception):
            pass

        class FakeClient:
            def __init__(self):
                self.calls = 0

            def create_tweet(self, text=None, media_ids=None, user_auth=None):
                self.calls += 1
                if self.calls < 3:
                    raise TwitterServerError("temporary failure")
                return {"ok": True, "text": text, "media_ids": media_ids, "user_auth": user_auth}

        fake_client = FakeClient()

        import sys
        import types

        original_tweepy = sys.modules.get("tweepy")
        original_tweepy_errors = sys.modules.get("tweepy.errors")
        tweepy_module = types.ModuleType("tweepy")
        tweepy_errors = types.ModuleType("tweepy.errors")
        tweepy_errors.TwitterServerError = TwitterServerError
        sys.modules["tweepy"] = tweepy_module
        sys.modules["tweepy.errors"] = tweepy_errors
        try:
            result = create_tweet_with_retry(
                fake_client,
                text="hello",
                attempts=3,
                sleep_seconds=0,
            )
        finally:
            if original_tweepy is not None:
                sys.modules["tweepy"] = original_tweepy
            else:
                sys.modules.pop("tweepy", None)

            if original_tweepy_errors is not None:
                sys.modules["tweepy.errors"] = original_tweepy_errors
            else:
                sys.modules.pop("tweepy.errors", None)

        self.assertEqual(fake_client.calls, 3)
        self.assertEqual(result["text"], "hello")
        self.assertTrue(result["user_auth"])

    def test_uses_increasing_backoff_between_attempts(self):
        class TwitterServerError(Exception):
            pass

        class FakeClient:
            def create_tweet(self, text=None, media_ids=None, user_auth=None):
                raise TwitterServerError("temporary failure")

        fake_client = FakeClient()

        import sys
        import types
        from unittest.mock import patch

        original_tweepy = sys.modules.get("tweepy")
        original_tweepy_errors = sys.modules.get("tweepy.errors")
        tweepy_module = types.ModuleType("tweepy")
        tweepy_errors = types.ModuleType("tweepy.errors")
        tweepy_errors.TwitterServerError = TwitterServerError
        sys.modules["tweepy"] = tweepy_module
        sys.modules["tweepy.errors"] = tweepy_errors
        try:
            with patch("tweet_bot.sleep") as sleep_mock:
                with self.assertRaises(TwitterServerError):
                    create_tweet_with_retry(
                        fake_client,
                        text="hello",
                        attempts=3,
                        sleep_seconds=2,
                    )
        finally:
            if original_tweepy is not None:
                sys.modules["tweepy"] = original_tweepy
            else:
                sys.modules.pop("tweepy", None)

            if original_tweepy_errors is not None:
                sys.modules["tweepy.errors"] = original_tweepy_errors
            else:
                sys.modules.pop("tweepy.errors", None)

        self.assertEqual([call.args[0] for call in sleep_mock.call_args_list], [2, 4])


class OAuth2RefreshTests(unittest.TestCase):
    def test_refresh_oauth2_access_token_uses_basic_auth_header(self):
        import base64
        from unittest.mock import patch

        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {"access_token": "new-access-token"}

        with patch("requests.post", return_value=FakeResponse()) as post_mock:
            access_token = refresh_oauth2_access_token("client-id", "client-secret", "refresh-token")

        self.assertEqual(access_token, "new-access-token")
        _, kwargs = post_mock.call_args
        self.assertEqual(kwargs["data"]["grant_type"], "refresh_token")
        self.assertEqual(kwargs["data"]["refresh_token"], "refresh-token")
        self.assertEqual(kwargs["timeout"], 30)
        expected_basic = base64.b64encode(b"client-id:client-secret").decode("utf-8")
        self.assertEqual(kwargs["headers"]["Authorization"], f"Basic {expected_basic}")
        self.assertEqual(
            kwargs["headers"]["Content-Type"],
            "application/x-www-form-urlencoded",
        )


class PostActionTests(unittest.TestCase):
    def test_post_action_skips_final_twitter_server_error(self):
        class Forbidden(Exception):
            pass

        class TwitterServerError(Exception):
            pass

        class FakeClient:
            def create_tweet(self, text=None, media_ids=None, user_auth=None):
                raise TwitterServerError("still unavailable")

        class FakeMedia:
            media_id = 123

        class FakeApiV1WithMedia:
            def media_upload(self, path, media_category=None):
                return FakeMedia()

        import sys
        import types

        original_tweepy = sys.modules.get("tweepy")
        original_tweepy_errors = sys.modules.get("tweepy.errors")
        tweepy_module = types.ModuleType("tweepy")
        tweepy_errors = types.ModuleType("tweepy.errors")
        tweepy_errors.Forbidden = Forbidden
        tweepy_errors.TwitterServerError = TwitterServerError
        sys.modules["tweepy"] = tweepy_module
        sys.modules["tweepy.errors"] = tweepy_errors
        try:
            post_action("bernie", FakeClient(), FakeApiV1WithMedia())
        finally:
            if original_tweepy is not None:
                sys.modules["tweepy"] = original_tweepy
            else:
                sys.modules.pop("tweepy", None)

            if original_tweepy_errors is not None:
                sys.modules["tweepy.errors"] = original_tweepy_errors
            else:
                sys.modules.pop("tweepy.errors", None)

    def test_post_action_includes_date_in_bernie_tweet_text(self):
        class Forbidden(Exception):
            pass

        class TwitterServerError(Exception):
            pass

        class FakeClient:
            def __init__(self):
                self.text = None
                self.media_ids = None
                self.user_auth = None

            def create_tweet(self, text=None, media_ids=None, user_auth=None):
                self.text = text
                self.media_ids = media_ids
                self.user_auth = user_auth
                return {"ok": True}

        class FakeMedia:
            media_id = 123

        class FakeApiV1WithMedia:
            def media_upload(self, path, media_category=None):
                self.path = path
                self.media_category = media_category
                return FakeMedia()

        import sys
        import types

        original_tweepy = sys.modules.get("tweepy")
        original_tweepy_errors = sys.modules.get("tweepy.errors")
        tweepy_module = types.ModuleType("tweepy")
        tweepy_errors = types.ModuleType("tweepy.errors")
        tweepy_errors.Forbidden = Forbidden
        tweepy_errors.TwitterServerError = TwitterServerError
        sys.modules["tweepy"] = tweepy_module
        sys.modules["tweepy.errors"] = tweepy_errors
        try:
            fake_client = FakeClient()
            fake_api_v1 = FakeApiV1WithMedia()
            post_action(
                "bernie",
                fake_client,
                fake_api_v1,
                target_date=datetime.fromisoformat("2026-04-21T08:00:00-04:00").date(),
            )
        finally:
            if original_tweepy is not None:
                sys.modules["tweepy"] = original_tweepy
            else:
                sys.modules.pop("tweepy", None)

            if original_tweepy_errors is not None:
                sys.modules["tweepy.errors"] = original_tweepy_errors
            else:
                sys.modules.pop("tweepy.errors", None)

        self.assertEqual(fake_client.text, "No day baseball on April 21, 2026.")
        self.assertEqual(fake_client.media_ids, [123])
        self.assertTrue(fake_client.user_auth)
        self.assertEqual(fake_api_v1.media_category, "tweet_image")


class FormattingTests(unittest.TestCase):
    def test_format_target_date_uses_readable_month_day_year(self):
        target_date = datetime.fromisoformat("2026-04-21T08:00:00-04:00").date()
        self.assertEqual(format_target_date(target_date), "April 21, 2026")


class ConfigurationTests(unittest.TestCase):
    def tearDown(self):
        for name in ("API_KEY", "API_SECRET", "ACCESS_TOKEN", "ACCESS_TOKEN_SECRET"):
            os.environ.pop(name, None)

    def test_create_twitter_clients_requires_all_credentials(self):
        with self.assertRaises(BotConfigurationError) as context:
            create_twitter_clients()

        self.assertIn("Missing Twitter credentials", str(context.exception))


if __name__ == "__main__":
    unittest.main()
