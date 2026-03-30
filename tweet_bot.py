import os
from datetime import datetime, time
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")


def get_today_eastern(now=None):
    current_time = now or datetime.now(EASTERN)
    return current_time.astimezone(EASTERN).date()


def get_target_date(now=None, schedule_date=None):
    if schedule_date is not None:
        return schedule_date

    target_date = os.getenv("TARGET_DATE")
    if target_date:
        return datetime.fromisoformat(target_date).date()

    return get_today_eastern(now)


def parse_game_time(game, timezone=EASTERN):
    game_date = game["gameDate"].replace("Z", "+00:00")
    return datetime.fromisoformat(game_date).astimezone(timezone)


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


def decide_post_action(games=None, now=None):
    target_date = get_target_date(now)
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
    import tweepy

    load_dotenv()
    consumer_key = os.getenv("API_KEY")
    consumer_secret = os.getenv("API_SECRET")
    access_token = os.getenv("ACCESS_TOKEN")
    access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

    client = tweepy.Client(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )
    auth = tweepy.OAuth1UserHandler(
        consumer_key,
        consumer_secret,
        access_token,
        access_token_secret,
    )
    api_v1 = tweepy.API(auth)
    return client, api_v1


def post_action(action, client, api_v1):
    from tweepy.errors import Forbidden

    if action == "larry":
        caption = "Day baseball? I'm conflicted."
        gif_url = "https://tenor.com/view/larry-david-unsure-uncertain-cant-decide-undecided-gif-3529136"
        tweet_text = f"{caption} {gif_url}"
        try:
            client.create_tweet(text=tweet_text)
            print("Posted Larry David GIF with caption")
        except Forbidden as error:
            print("Skipped (duplicate or forbidden):", error)
        return

    if action == "bernie":
        try:
            media = api_v1.media_upload("DayBaseball.jpg")
            client.create_tweet(media_ids=[media.media_id])
            print("Posted Bernie meme as media")
        except Forbidden as error:
            print("Skipped (duplicate or forbidden):", error)
        return

    print("Skipped (day games or no games scheduled today)")


def main():
    action = decide_post_action()
    if os.getenv("DRY_RUN") == "1":
        print(f"Dry run action: {action}")
        return

    if not action:
        print("Skipped (day games or no games scheduled today)")
        return

    client, api_v1 = create_twitter_clients()
    post_action(action, client, api_v1)


if __name__ == "__main__":
    main()
