import os
import requests
from datetime import datetime, time
import pytz
from dateutil import parser
from dotenv import load_dotenv
import tweepy
from tweepy.errors import Forbidden

# ─── Load Twitter creds from .env ──────────────────────────────────────────────
load_dotenv()
CK  = os.getenv("API_KEY")
CS  = os.getenv("API_SECRET")
AT  = os.getenv("ACCESS_TOKEN")
ATS = os.getenv("ACCESS_TOKEN_SECRET")

# ─── Setup Tweepy clients ──────────────────────────────────────────────────────
client = tweepy.Client(
    consumer_key=CK,
    consumer_secret=CS,
    access_token=AT,
    access_token_secret=ATS,
)
auth = tweepy.OAuth1UserHandler(CK, CS, AT, ATS)
api_v1 = tweepy.API(auth)

# ─── Check scoreboard ──────────────────────────────────────────────────────────
def no_day_baseball_but_some_games():
    data = requests.get(
        "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
    ).json().get("events", [])

    eastern = pytz.timezone("US/Eastern")
    today   = datetime.now(eastern).date()

    # Skip if truly no games at all (off‑season, All‑Star, etc.)
    if not data:
        return False

    # If any game starts before 16:00 ET today, that's day baseball → skip
    for ev in data:
        game_dt = parser.isoparse(ev["date"]).astimezone(eastern)
        if game_dt.date() == today and game_dt.time() < time(16, 0):
            return False

    # There are games, but none before 4 PM ET
    return True

# ─── Main routine ─────────────────────────────────────────────────────────────
if no_day_baseball_but_some_games():
    media = api_v1.media_upload("DayBaseball.jpg")
    try:
        client.create_tweet(media_ids=[media.media_id])
        print("✅ Posted meme image as media")
    except Forbidden as e:
        print("⚠️ Skipped posting (duplicate or forbidden):", e)
else:
    print("✅ Skipped (day games or no games scheduled today)")
