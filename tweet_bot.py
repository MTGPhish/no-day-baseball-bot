import os
import requests
from datetime import datetime, time
import pytz
from dateutil import parser
from dotenv import load_dotenv
import tweepy
from tweepy.errors import Forbidden

# ─── Load your Twitter credentials from .env ──────────────────────────────────
load_dotenv()
consumer_key        = os.getenv("API_KEY")
consumer_secret     = os.getenv("API_SECRET")
access_token        = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

# ─── Set up Tweepy v2 client for posting tweets ───────────────────────────────
client = tweepy.Client(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret,
)

# ─── Set up Tweepy v1.1 API for media upload ─────────────────────────────────
auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, access_token, access_token_secret)
api_v1 = tweepy.API(auth)

# ─── Helper: returns True if NO MLB games start before 4PM ET today ───────────
def no_day_baseball():
    scoreboard = requests.get(
        "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
    ).json()

    eastern = pytz.timezone("US/Eastern")
    today   = datetime.now(eastern).date()

    for event in scoreboard.get("events", []):
        # parse the UTC ISO timestamp (with trailing “Z”) correctly
        game_dt = parser.isoparse(event["date"]).astimezone(eastern)
        # if any game starts before 16:00 ET, that's day baseball
        if game_dt.date() == today and game_dt.time() < time(16, 0):
            return False

    return True

# ─── Main: upload & tweet the meme if there’s no day baseball ────────────────
if no_day_baseball():
    media = api_v1.media_upload("DayBaseball.jpg")
    try:
        client.create_tweet(media_ids=[media.media_id])
        print("✅ Posted meme image as media")
    except Forbidden as e:
        print("⚠️ Skipped posting (duplicate or forbidden):", e)
else:
    print("✅ Skipped (there is day baseball today)")
