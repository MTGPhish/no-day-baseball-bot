import os
import requests
from datetime import datetime
import pytz
from dotenv import load_dotenv
import tweepy
from tweepy.errors import Forbidden

# Load credentials from .env
load_dotenv()
consumer_key        = os.getenv("API_KEY")
consumer_secret     = os.getenv("API_SECRET")
access_token        = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

# Initialize Tweepy v2 client
client = tweepy.Client(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret,
)

def no_day_baseball():
    """Return True if no MLB games start before 4 PM ET today."""
    data = requests.get(
        "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
    ).json()
    eastern = pytz.timezone("US/Eastern")
    today = datetime.now(eastern).date()

    for evt in data.get("events", []):
        game_dt = datetime.fromisoformat(evt["date"]).astimezone(eastern)
        if (game_dt.date() == today
            and game_dt.time() < datetime.strptime("16:00", "%H:%M").time()):
            return False
    return True

if no_day_baseball():
    # Append the date so Twitter treats each URL as unique
    eastern = pytz.timezone("US/Eastern")
    suffix = datetime.now(eastern).strftime("%Y%m%d")

    # <-- Your Imgur direct link, must end in .jpeg -->
    base_imgur = "https://i.imgur.com/iwCKCxC.jpeg"
    tweet_url  = f"{base_imgur}?d={suffix}"

    try:
        client.create_tweet(text=tweet_url)
        print("✅ Posted meme link via v2 (Imgur)")
    except Forbidden as e:
        print("⚠️ Skipped posting (duplicate or forbidden):", e)
else:
    print("✅ Skipped (there is day baseball today)")
