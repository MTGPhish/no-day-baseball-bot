import os
import requests
from datetime import datetime
import pytz
from dotenv import load_dotenv
import tweepy
from tweepy.errors import Forbidden

# ─── load your secrets from .env ───────────────────────────────────────────────
load_dotenv()
CK  = os.getenv("API_KEY")
CS  = os.getenv("API_SECRET")
AT  = os.getenv("ACCESS_TOKEN")
ATS = os.getenv("ACCESS_TOKEN_SECRET")

# ─── v2 client (for posting) ─────────────────────────────────────────────────
client = tweepy.Client(
    consumer_key=CK,
    consumer_secret=CS,
    access_token=AT,
    access_token_secret=ATS,
)

# ─── v1.1 API (for media_upload) ──────────────────────────────────────────────
# OAuth1UserHandler is the new name in Tweepy v4 for the old OAuthHandler
auth = tweepy.OAuth1UserHandler(CK, CS, AT, ATS)
api_v1 = tweepy.API(auth)

# ─── helper to check for day games ────────────────────────────────────────────
def no_day_baseball():
    url = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
    data = requests.get(url).json()
    eastern = pytz.timezone("US/Eastern")
    today = datetime.now(eastern).date()

    for ev in data.get("events", []):
        gd = datetime.fromisoformat(ev["date"]).astimezone(eastern)
        # any game before 4 PM ET is a “day” game
        if gd.date()==today and gd.time() < datetime.strptime("16:00","%H:%M").time():
            return False
    return True

# ─── main ─────────────────────────────────────────────────────────────────────
if no_day_baseball():
    # upload the image in your repo root
    # make sure DayBaseball.jpg is committed in your repo
    media = api_v1.media_upload("DayBaseball.jpg")

    try:
        # post a tweet **with** that media, no text needed
        client.create_tweet(media_ids=[media.media_id])
        print("✅ Posted meme image as media")
    except Forbidden as e:
        print("⚠️ Skipped (duplicate or forbidden):", e)
else:
    print("✅ Skipped (there is day baseball today)")
