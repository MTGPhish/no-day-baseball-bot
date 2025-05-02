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
    url = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
    resp = requests.get(url).json()
    eastern = pytz.timezone("US/Eastern")
    today = datetime.now(eastern).date()

    for game in resp.get("events", []):
        game_dt = datetime.fromisoformat(game["date"]).astimezone(eastern)
        if game_dt.date() == today and game_dt.time() < datetime.strptime("16:00", "%H:%M").time():
            return False
    return True

if no_day_baseball():
    # Build a unique URL by appending today’s date as a query‑string
    eastern = pytz.timezone("US/Eastern")
    suffix = datetime.now(eastern).strftime("%Y%m%d")
    url = (
        "https://raw.githubusercontent.com/"
        "MTGPhish/no-day-baseball-bot/main/DayBaseball.jpg"
        f"?d={suffix}"
    )

    try:
        client.create_tweet(text=url)
        print("✅ Posted meme link via v2")
    except Forbidden as e:
        # In the extremely unlikely event it still trips duplicate-filter,
        # we catch it so the Action doesn’t fail.
        print("⚠️ Skipped posting (duplicate or forbidden):", e)
else:
    print("✅ Skipped (there is day baseball today)")
