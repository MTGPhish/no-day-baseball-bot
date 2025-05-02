import tweepy
import os
import requests
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Load keys
load_dotenv()
consumer_key        = os.getenv("API_KEY")
consumer_secret     = os.getenv("API_SECRET")
access_token        = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

# Auth
auth = tweepy.OAuth1UserHandler(
    consumer_key, consumer_secret, access_token, access_token_secret
)
api = tweepy.API(auth)

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
    # upload & post ONLY the meme
    api.update_status(status="https://raw.githubusercontent.com/MTGPhish/no-day-baseball-bot/main/DayBaseball.jpg")
    print("✅ Posted meme (no text).")
else:
    print("✅ Skipped (there is day baseball today).")
