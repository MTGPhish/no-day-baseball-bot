import os
import requests
from datetime import datetime
import pytz
from dotenv import load_dotenv
import tweepy
from tweepy.errors import Forbidden

# Load your API credentials from .env
load_dotenv()
consumer_key        = os.getenv("API_KEY")
consumer_secret     = os.getenv("API_SECRET")
access_token        = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

# Initialize the Tweepy v2 client
client = tweepy.Client(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret,
)

def no_day_baseball():
    """Return True if there are NO MLB games starting before 4 PM ET today."""
    scoreboard = requests.get(
        "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
    ).json()
    eastern = pytz.timezone("US/Eastern")
    today = datetime.now(eastern).date()

    for event in scoreboard.get("events", []):
        game_dt = datetime.fromisoformat(event["date"]).astimezone(eastern)
        if game_dt.date() == today and game_dt.time() < datetime.strptime("16:00", "%H:%M").time():
            return False
    return True

if no_day_baseball():
    # Append ?d=YYYYMMDD to dodge duplicate‑content, but raw.githack.com will still serve
    suffix = datetime.now(pytz.timezone("US/Eastern")).strftime("%Y%m%d")
    url = (
        "https://raw.githack.com/"
        "MTGPhish/no-day-baseball-bot/main/DayBaseball.jpg"
        f"?d={suffix}"
    )
    try:
        client.create_tweet(text=url)
        print("✅ Posted meme link via v2 (raw.githack.com)")
    except Forbidden as e:
        print("⚠️ Skipped posting (duplicate or forbidden):", e)
else:
    print("✅ Skipped (there is day baseball today)")
