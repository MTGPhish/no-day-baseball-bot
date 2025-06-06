import os
import requests
from datetime import datetime, time
import pytz
from dateutil import parser
from dotenv import load_dotenv
import tweepy
from tweepy.errors import Forbidden

# ─── Load Twitter credentials from .env ─────────────────────────────────────────
load_dotenv()
CK  = os.getenv("API_KEY")
CS  = os.getenv("API_SECRET")
AT  = os.getenv("ACCESS_TOKEN")
ATS = os.getenv("ACCESS_TOKEN_SECRET")

# ─── Setup Tweepy clients ───────────────────────────────────────────────────────
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
    data = requests.get(url).json().get("dates", [])
    if not data:
        return []
    return data[0].get("games", [])

# ─── Decide action: “larry” for early makeup, “bernie” for no early games, False otherwise ────────────────
def decide_post_action():
    games = fetch_today_games()
    eastern = pytz.timezone("US/Eastern")
    today = datetime.now(eastern).date()
    cutoff = time(16, 0)

    # 1) No games scheduled at all (off-season, etc.) → skip
    if not games:
        return False

    early_makeup = False
    for g in games:
        # Parse the actual UTC start time into ET
        game_dt = parser.isoparse(g["gameDate"]).astimezone(eastern)
        print(f"DEBUG: MLB game at {game_dt.strftime('%H:%M %Z')} (doubleHeader={g.get('doubleHeader')})")

        # If it’s a pre-4 PM ET start
        if game_dt.date() == today and game_dt.time() < cutoff:
            # If it’s part of a doubleheader, this is almost certainly a makeup day game
            if g.get("doubleHeader") == "Y":
                early_makeup = True
            else:
                # It was originally scheduled as a day game → skip posting
                return False

    # 2) If any pre-4 PM ET game was part of a doubleheader → Larry David
    if early_makeup:
        return "larry"

    # 3) Otherwise, games exist but none start before 4 PM ET → Bernie
    return "bernie"

# ─── Main: post based on decision ────────────────────────────────────────────────
action = decide_post_action()

if action == "larry":
    caption = "Day baseball? I'm conflicted."
    gif_url = "https://tenor.com/view/larry-david-unsure-uncertain-cant-decide-undecided-gif-3529136"
    tweet_text = f"{caption} {gif_url}"
    try:
        client.create_tweet(text=tweet_text)
        print("✅ Posted Larry David GIF with caption")
    except Forbidden as e:
        print("⚠️ Skipped (duplicate or forbidden):", e)

elif action == "bernie":
    media = api_v1.media_upload("DayBaseball.jpg")
    try:
        client.create_tweet(media_ids=[media.media_id])
        print("✅ Posted Bernie meme as media")
    except Forbidden as e:
        print("⚠️ Skipped (duplicate or forbidden):", e)

else:
    print("✅ Skipped (day games or no games scheduled today)")
