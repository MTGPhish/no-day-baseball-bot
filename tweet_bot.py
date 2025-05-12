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

# ─── Fetch today’s MLB games via the official API ──────────────────────────────
def fetch_today_games():
    eastern = pytz.timezone("US/Eastern")
    today_str = datetime.now(eastern).strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today_str}"
    resp = requests.get(url).json().get("dates", [])
    if not resp:
        return []
    return resp[0].get("games", [])

# ─── Decide if we should post (games exist & none before 4 PM ET) ──────────────
def should_post_meme():
    games = fetch_today_games()

    # DEBUG: log how many games fetched
    print(f"DEBUG: fetched {len(games)} game(s) for today")

    # 1) if no games at all: skip
    if not games:
        return False

    eastern = pytz.timezone("US/Eastern")
    cutoff = time(16, 0)

    # 2) if any game starts before cutoff: skip
    for g in games:
        game_dt = parser.isoparse(g["gameDate"]).astimezone(eastern)
        print(f"DEBUG: MLB game at {game_dt.strftime('%H:%M %Z')}")
        if game_dt.time() < cutoff:
            print("DEBUG: found a day game → skipping")
            return False

    # 3) else: games exist but none before cutoff → post
    print("DEBUG: no day games found → posting")
    return True

# ─── Main: post the meme if appropriate ────────────────────────────────────────
if should_post_meme():
    media = api_v1.media_upload("DayBaseball.jpg")
    try:
        client.create_tweet(media_ids=[media.media_id])
        print("✅ Posted meme image as media")
    except Forbidden as e:
        print("⚠️ Skipped (duplicate or forbidden):", e)
else:
    print("✅ Skipped (day games or no games scheduled today)")
