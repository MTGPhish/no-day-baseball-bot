# No Day Baseball Bot

No Day Baseball is an automated Twitter/X bot that complains when MLB schedules a full day of games without any true day baseball.

Hosted with GitHub Actions, it runs daily at `12:00 UTC` and:

1. Queries MLB's public schedule API for today's games.
2. Checks whether any game starts before `4:00 PM` Eastern.
3. Posts the Bernie meme image when games exist but none start before `4:00 PM` Eastern.
4. Skips posting when there is a normal early game or no games at all.
5. Posts a Larry David message when the only early game appears to be a doubleheader makeup game.

## Behavior Notes

- `4:00 PM Eastern` is treated as not early. The bot only counts starts before `4:00 PM`.
- The scheduled workflow time is fixed in UTC. During Eastern Daylight Time that is `8:00 AM`, and during Eastern Standard Time that is `7:00 AM`.

## Testing

The repo includes unit tests for the posting decision logic and the MLB schedule fetch behavior.

Run them with:

```bash
python -m unittest discover -s tests -v
```

You can also dry-run the bot for a specific Eastern date without posting:

```bash
TARGET_DATE=2026-03-31 DRY_RUN=1 python tweet_bot.py
```

## Setup

1. Create a Twitter developer app with read and write permissions.
2. Provide these environment variables locally or as GitHub Actions secrets:
   - `API_KEY`
   - `API_SECRET`
   - `ACCESS_TOKEN`
   - `ACCESS_TOKEN_SECRET`
3. Run the bot with:

```bash
python tweet_bot.py
```
