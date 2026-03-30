import os
import unittest
from datetime import datetime

from tweet_bot import decide_post_action, fetch_today_games, get_target_date


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


if __name__ == "__main__":
    unittest.main()
