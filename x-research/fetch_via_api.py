#!/usr/bin/env python3
"""
Fetch tweets using the official X API (Twitter API v2).

Requirements:
    pip install tweepy

Setup:
    1. Get API credentials at https://developer.x.com/
    2. Set environment variables:
       export X_BEARER_TOKEN="your_bearer_token_here"

    Or pass the token directly in this script.
"""

import csv
import os
import sys
from pathlib import Path
from datetime import datetime

try:
    import tweepy
except ImportError:
    print("❌ Error: tweepy not installed")
    print("\nInstall with: pip install tweepy")
    sys.exit(1)


def fetch_tweets_api(bearer_token: str, accounts: list, tweets_per_account: int = 20):
    """Fetch tweets using X API v2."""

    # Initialize API client
    client = tweepy.Client(bearer_token=bearer_token)

    all_tweets = []

    for i, account in enumerate(accounts, 1):
        # Remove @ if present
        username = account.lstrip('@')

        print(f"[{i}/{len(accounts)}] Fetching from @{username}...")

        try:
            # Get user ID
            user = client.get_user(username=username)
            if not user.data:
                print(f"  ✗ User not found")
                continue

            user_id = user.data.id

            # Get user's recent tweets
            tweets = client.get_users_tweets(
                id=user_id,
                max_results=min(tweets_per_account, 100),  # API max is 100
                tweet_fields=['created_at', 'public_metrics'],
                exclude=['retweets', 'replies']  # Only original tweets
            )

            if not tweets.data:
                print(f"  ✓ No tweets found")
                continue

            # Process tweets
            for tweet in tweets.data:
                tweet_data = {
                    'account_handle': f'@{username}',
                    'tweet_url': f'https://x.com/{username}/status/{tweet.id}',
                    'tweet_text': tweet.text.replace('\n', ' ').strip(),
                    'likes': tweet.public_metrics['like_count'],
                    'retweets': tweet.public_metrics['retweet_count'],
                    'replies': tweet.public_metrics['reply_count'],
                    'posted_date': tweet.created_at.strftime('%Y-%m-%d'),
                    'notes': 'Fetched via X API'
                }
                all_tweets.append(tweet_data)

            print(f"  ✓ Got {len(tweets.data)} tweets")

        except tweepy.TweepyException as e:
            print(f"  ✗ API Error: {e}")
            continue
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue

    return all_tweets


def main():
    """Main function."""

    # Configuration
    accounts = [
        "@phantom",
        "@solflare",
        "@baseposting",
        "@solana",
        "@luminaries",
        "@wallet",
        "@jupiterexchange",
        "@trustwallet",
        "@metamask",
        "@arkham",
        "@ondofinance",
        "@eigencloud",
        "@maplefinance",
        "@seinetwork",
        "@soniclabs"
    ]

    tweets_per_account = 20
    output_file = Path(__file__).parent / "data" / "fetched_tweets.csv"

    # Get API credentials
    bearer_token = os.environ.get('X_BEARER_TOKEN')

    if not bearer_token:
        print("❌ Error: X_BEARER_TOKEN environment variable not set")
        print("\nGet your bearer token at: https://developer.x.com/")
        print("Then set it with: export X_BEARER_TOKEN='your_token_here'")
        print("\nOr edit this script and set the bearer_token variable directly.")
        sys.exit(1)

    print(f"Fetching tweets from {len(accounts)} accounts via X API...")
    print(f"Target: {tweets_per_account} tweets per account")
    print(f"Output: {output_file}\n")

    # Fetch tweets
    all_tweets = fetch_tweets_api(bearer_token, accounts, tweets_per_account)

    if not all_tweets:
        print("\n❌ No tweets were fetched!")
        sys.exit(1)

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    print(f"\n📝 Writing {len(all_tweets)} tweets to CSV...")

    fieldnames = [
        'account_handle',
        'tweet_url',
        'tweet_text',
        'likes',
        'retweets',
        'replies',
        'posted_date',
        'notes'
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_tweets)

    print(f"\n✅ Success! Fetched {len(all_tweets)} tweets from {len(accounts)} accounts")
    print(f"📄 Saved to: {output_file}")

    # Print summary
    print("\nSummary by account:")
    account_counts = {}
    for tweet in all_tweets:
        handle = tweet['account_handle']
        account_counts[handle] = account_counts.get(handle, 0) + 1

    for account in accounts:
        count = account_counts.get(account, 0)
        print(f"  {account}: {count} tweets")


if __name__ == '__main__':
    main()
