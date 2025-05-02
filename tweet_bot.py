import os
import requests
from datetime import datetime
import pytz
from dotenv import load_dotenv
import tweepy

load_dotenv()

# Load your keys / tokens
consumer_key        = os.getenv("API_KEY")
consumer_secret     = os.getenv("API_SECRET")
access_token        = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

# Use Tweepy Client (v2)
client = tweepy.Client(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret,
)

def no_day_baseball():
    url = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
    resp = requests.get(url).json()
    eastern = pytz.timezone('US/Eastern')
    today = datetime.now(eastern).date()

    for game in resp.get("events", []):
        game_dt = datetime.fromisoformat(game["date"]).astimezone(eastern)
        if game_dt.date() == today and game_dt.time() < datetime.strptime("16:00", "%H:%M").time():
            return False
    return True

if no_day_baseball():
    # Post only the raw.githubusercontent.com image URL
    client.create_tweet(
        text="https://raw.githubusercontent.com/MTGPhish/no-day-baseball-bot/main/DayBaseball.jpg"
    )
    print("✅ Posted meme link via v2")
else:
    print("✅ Skipped (there is day baseball today)")
