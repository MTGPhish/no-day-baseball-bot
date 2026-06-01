# No Day Baseball Bot

No Day Baseball is an automated Twitter/X bot that complains when MLB schedules a full day of games without any true day baseball.

Hosted with GitHub Actions, it runs daily at `15:17 UTC`, with a fallback run at `17:47 UTC`, and:

1. Queries MLB's public schedule API for today's games.
2. Checks whether any game starts before `4:00 PM` Eastern.
3. Posts the Bernie meme image when games exist but none start before `4:00 PM` Eastern.
4. Skips posting when there is a normal early game or no games at all.
5. Posts a Larry David message when the only early game appears to be a doubleheader makeup game.

Posting failures are treated as workflow failures. Duplicate-content reruns are skipped, but invalid credentials, expired tokens, X API errors, and MLB API errors should make the GitHub Actions run fail so the bot does not silently miss Bernie days.

## Behavior Notes

- `4:00 PM Eastern` is treated as not early. The bot only counts starts before `4:00 PM`.
- The scheduled workflow times are fixed in UTC. During Eastern Daylight Time, the primary run targets `11:17 AM` and the fallback targets `1:47 PM`.
- GitHub scheduled workflows can start later than their cron time or occasionally miss a run. The `17:47 UTC` fallback gives the bot another chance before the `4:00 PM Eastern` no-day-game cutoff.
- Successful posts are recorded in `.posted_actions.json`, so fallback or delayed runs skip when the same action has already posted for that date.

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
   - `OAUTH2_CLIENT_ID`
   - `OAUTH2_CLIENT_SECRET`
   - `OAUTH2_REFRESH_TOKEN`
   - `OAUTH2_REFRESH_TOKEN_KEY`
3. Run the bot with:

```bash
python tweet_bot.py
```

The scheduled bot uses OAuth2 for X API v2 post creation after uploading the image with OAuth1 credentials. X requires the posting app to be attached to a Project; standalone OAuth1 app credentials fail with `403 Client Forbidden`, and the legacy v1.1 status endpoint has returned `404 Not Found` in scheduled runs. When X rotates the OAuth2 refresh token, the workflow encrypts the rotated token into `.oauth2_refresh_token.enc` and commits that file back to the repo. `OAUTH2_REFRESH_TOKEN_KEY` is the GitHub Actions secret used to decrypt that file on future runs.
