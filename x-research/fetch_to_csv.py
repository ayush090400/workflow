#!/usr/bin/env python3
"""Script to fetch tweets from multiple X accounts and save to CSV."""

import csv
import sys
from pathlib import Path
from browser_fetcher import BrowserFetcher


def main():
    """Fetch tweets and save to CSV."""
    # Account list
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

    # Output file
    output_file = Path(__file__).parent / "data" / "fetched_tweets.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Fetching tweets from {len(accounts)} accounts...")
    print(f"Target: 15-20 tweets per account")
    print(f"Output: {output_file}\n")

    # Initialize fetcher
    fetcher = BrowserFetcher()

    # Collect all tweets
    all_tweets = []

    for i, account in enumerate(accounts, 1):
        print(f"[{i}/{len(accounts)}] Fetching from {account}...")

        try:
            tweets = fetcher.fetch_account_tweets(
                account,
                count=20,  # Try to get 20 tweets
                headless=True
            )

            all_tweets.extend(tweets)
            print(f"  ✓ Got {len(tweets)} tweets")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue

    # Write to CSV
    if not all_tweets:
        print("\n❌ No tweets were fetched!")
        sys.exit(1)

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

        for tweet in all_tweets:
            writer.writerow({
                'account_handle': tweet.get('account_handle', ''),
                'tweet_url': tweet.get('tweet_url', ''),
                'tweet_text': tweet.get('tweet_text', ''),
                'likes': tweet.get('likes', ''),
                'retweets': tweet.get('retweets', ''),
                'replies': tweet.get('replies', ''),
                'posted_date': tweet.get('posted_date', ''),
                'notes': tweet.get('notes', 'Auto-fetched')
            })

    print(f"\n✅ Success! Fetched {len(all_tweets)} tweets from {len(accounts)} accounts")
    print(f"📄 Saved to: {output_file}")

    # Print summary by account
    print("\nSummary by account:")
    account_counts = {}
    for tweet in all_tweets:
        handle = tweet.get('account_handle', '')
        account_counts[handle] = account_counts.get(handle, 0) + 1

    for handle in accounts:
        count = account_counts.get(handle, 0)
        print(f"  {handle}: {count} tweets")


if __name__ == '__main__':
    main()
