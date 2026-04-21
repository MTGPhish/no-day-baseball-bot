import os
from datetime import datetime, time
from time import sleep
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")
REQUIRED_TWITTER_ENV_VARS = (
    "API_KEY",
    "API_SECRET",
    "ACCESS_TOKEN",
    "ACCESS_TOKEN_SECRET",
)
OPTIONAL_OAUTH2_ENV_VARS = (
    "OAUTH2_CLIENT_ID",
    "OAUTH2_CLIENT_SECRET",
    "OAUTH2_REFRESH_TOKEN",
)


class BotConfigurationError(RuntimeError):
    pass


def get_today_eastern(now=None):
    current_time = now or datetime.now(EASTERN)
    return current_time.astimezone(EASTERN).date()


def get_target_date(now=None, schedule_date=None):
    if schedule_date is not None:
        return schedule_date

    target_date = os.getenv("TARGET_DATE")
    if target_date:
        try:
            return datetime.fromisoformat(target_date).date()
        except ValueError as error:
            raise BotConfigurationError(
                f"Invalid TARGET_DATE value {target_date!r}; expected YYYY-MM-DD"
            ) from error

    return get_today_eastern(now)


def parse_game_time(game, timezone=EASTERN):
    game_date = game["gameDate"].replace("Z", "+00:00")
    return datetime.fromisoformat(game_date).astimezone(timezone)


def format_target_date(target_date):
    return f"{target_date.strftime('%B')} {target_date.day}, {target_date.year}"


def fetch_today_games(schedule_date=None, session=None):
    import requests

    target_date = schedule_date or get_today_eastern()
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={target_date.isoformat()}"
    http = session or requests
    response = http.get(url, timeout=10)
    response.raise_for_status()
    dates = response.json().get("dates", [])
    if not dates:
        return []
    return dates[0].get("games", [])


def decide_post_action(games=None, now=None, target_date=None):
    target_date = target_date or get_target_date(now)
    todays_games = games if games is not None else fetch_today_games(schedule_date=target_date)
    cutoff = time(16, 0)

    if not todays_games:
        return False

    early_makeup = False
    for game in todays_games:
        game_dt = parse_game_time(game)
        print(
            f"DEBUG: MLB game at {game_dt.strftime('%H:%M %Z')} "
            f"(doubleHeader={game.get('doubleHeader')})"
        )

        if game_dt.date() == target_date and game_dt.time() < cutoff:
            if game.get("doubleHeader") == "Y":
                early_makeup = True
            else:
                return False

    if early_makeup:
        return "larry"

    return "bernie"


def create_twitter_clients():
    from dotenv import load_dotenv

    load_dotenv()
    credentials = {name: os.getenv(name) for name in REQUIRED_TWITTER_ENV_VARS}
    missing = [name for name, value in credentials.items() if not value]
    if missing:
        raise BotConfigurationError(
            "Missing Twitter credentials: " + ", ".join(missing)
        )

    consumer_key = credentials["API_KEY"]
    consumer_secret = credentials["API_SECRET"]
    access_token = credentials["ACCESS_TOKEN"]
    access_token_secret = credentials["ACCESS_TOKEN_SECRET"]
    oauth2_client_id = os.getenv("OAUTH2_CLIENT_ID")
    oauth2_client_secret = os.getenv("OAUTH2_CLIENT_SECRET")
    oauth2_refresh_token = os.getenv("OAUTH2_REFRESH_TOKEN")

    import tweepy

    if all((oauth2_client_id, oauth2_client_secret, oauth2_refresh_token)):
        client = tweepy.Client(
            bearer_token=refresh_oauth2_access_token(
                oauth2_client_id,
                oauth2_client_secret,
                oauth2_refresh_token,
            )
        )
        client_user_auth = False
    else:
        client = tweepy.Client(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )
        client_user_auth = True

    auth = tweepy.OAuth1UserHandler(
        consumer_key,
        consumer_secret,
        access_token,
        access_token_secret,
    )
    api_v1 = tweepy.API(auth)
    return client, client_user_auth, api_v1


def refresh_oauth2_access_token(client_id, client_secret, refresh_token):
    import base64
    import requests

    token_url = "https://api.x.com/2/oauth2/token"
    basic_token = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode(
        "utf-8"
    )
    response = requests.post(
        token_url,
        headers={
            "Authorization": f"Basic {basic_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    response.raise_for_status()
    refreshed_token = response.json()

    rotated_refresh_token = refreshed_token.get("refresh_token")
    if rotated_refresh_token and rotated_refresh_token != refresh_token:
        print(
            "NOTICE: OAUTH2_REFRESH_TOKEN rotated. "
            "Update the GitHub secret to keep future runs healthy."
        )

    return refreshed_token["access_token"]


def create_tweet_with_retry(
    client,
    *,
    text=None,
    media_ids=None,
    attempts=5,
    sleep_seconds=5,
    user_auth=True,
):
    from tweepy.errors import TwitterServerError

    for attempt in range(1, attempts + 1):
        try:
            return client.create_tweet(text=text, media_ids=media_ids, user_auth=user_auth)
        except TwitterServerError as error:
            if attempt == attempts:
                raise
            print(f"Temporary Twitter error on attempt {attempt}/{attempts}: {error}")
            sleep(sleep_seconds * attempt)


def post_action(action, client, api_v1, *, target_date=None, client_user_auth=True):
    from tweepy.errors import Forbidden, TwitterServerError

    formatted_target_date = format_target_date(target_date or get_target_date())

    if action == "larry":
        caption = f"Day baseball? I'm conflicted on {formatted_target_date}."
        gif_url = "https://tenor.com/view/larry-david-unsure-uncertain-cant-decide-undecided-gif-3529136"
        tweet_text = f"{caption} {gif_url}"
        try:
            create_tweet_with_retry(client, text=tweet_text, user_auth=client_user_auth)
            print("Posted Larry David GIF with caption")
        except Forbidden as error:
            print("Skipped (duplicate or forbidden):", error)
        except TwitterServerError as error:
            print("Skipped (Twitter server unavailable after retries):", error)
        return

    if action == "bernie":
        tweet_text = f"No day baseball on {formatted_target_date}."
        try:
            media = api_v1.media_upload("DayBaseball.jpg", media_category="tweet_image")
            create_tweet_with_retry(
                client,
                text=tweet_text,
                media_ids=[media.media_id],
                user_auth=client_user_auth,
            )
            print("Posted Bernie meme as media")
        except Forbidden as error:
            print("Skipped (duplicate or forbidden):", error)
        except TwitterServerError as error:
            print("Skipped (Twitter server unavailable after retries):", error)
        return

    print("Skipped (day games or no games scheduled today)")


def get_runtime_error_types():
    runtime_errors = [BotConfigurationError]

    try:
        import requests

        runtime_errors.append(requests.RequestException)
    except ImportError:
        pass

    try:
        from tweepy.errors import TweepyException

        runtime_errors.append(TweepyException)
    except ImportError:
        pass

    return tuple(runtime_errors)


def main():
    try:
        target_date = get_target_date()
        games = fetch_today_games(schedule_date=target_date)
        action = decide_post_action(games=games, target_date=target_date)
        if os.getenv("DRY_RUN") == "1":
            print(f"Dry run action: {action}")
            return

        if not action:
            print("Skipped (day games or no games scheduled today)")
            return

        client, client_user_auth, api_v1 = create_twitter_clients()
        post_action(
            action,
            client,
            api_v1,
            target_date=target_date,
            client_user_auth=client_user_auth,
        )
    except get_runtime_error_types() as error:
        print(f"Skipped (external dependency or configuration issue: {error})")


if __name__ == "__main__":
    main()
