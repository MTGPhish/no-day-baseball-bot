import os

import tweepy


SCOPES = ["tweet.read", "users.read", "tweet.write", "offline.access"]


def main():
    client_id = os.getenv("OAUTH2_CLIENT_ID")
    client_secret = os.getenv("OAUTH2_CLIENT_SECRET")
    redirect_uri = os.getenv("OAUTH2_REDIRECT_URI")

    missing = [
        name
        for name, value in (
            ("OAUTH2_CLIENT_ID", client_id),
            ("OAUTH2_CLIENT_SECRET", client_secret),
            ("OAUTH2_REDIRECT_URI", redirect_uri),
        )
        if not value
    ]
    if missing:
        missing_list = ", ".join(missing)
        raise SystemExit(f"Missing required environment variables: {missing_list}")

    oauth2_user_handler = tweepy.OAuth2UserHandler(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=SCOPES,
        client_secret=client_secret,
    )
    authorization_url = oauth2_user_handler.get_authorization_url()
    print("Open this URL in your browser and authorize the bot account:\n")
    print(authorization_url)
    print("\nPaste the full redirect URL after authorization:")
    authorization_response = input().strip()
    token = oauth2_user_handler.fetch_token(authorization_response)

    print("\nSave these as GitHub Actions secrets:")
    print(f"OAUTH2_CLIENT_ID={client_id}")
    print(f"OAUTH2_CLIENT_SECRET={client_secret}")
    print(f"OAUTH2_REFRESH_TOKEN={token['refresh_token']}")


if __name__ == "__main__":
    main()
