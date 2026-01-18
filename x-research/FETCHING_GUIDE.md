# Tweet Fetching Guide

## Current Situation

The automated tweet fetching encountered network limitations in the current environment. The CSV file has been created at `/home/user/workflow/x-research/data/fetched_tweets.csv` with the proper header structure.

## Target Accounts

The following 15 accounts need tweets fetched:
- @phantom
- @solflare
- @baseposting
- @solana
- @luminaries
- @wallet
- @jupiterexchange
- @trustwallet
- @metamask
- @arkham
- @ondofinance
- @eigencloud
- @maplefinance
- @seinetwork
- @soniclabs

**Goal**: 15-20 recent tweets per account

## Alternative Solutions

### Option 1: Run in Environment with Network Access

The `fetch_to_csv.py` script is ready to use. Simply run it in an environment with internet access:

```bash
cd /home/user/workflow/x-research
python fetch_to_csv.py
```

**Requirements:**
- Python 3.7+
- Playwright installed: `pip install playwright`
- Browsers installed: `playwright install chromium`
- Internet access to x.com

### Option 2: Use the X Research CLI Tool

If you have the tool set up elsewhere:

```bash
# Fetch all accounts at once
python x-research.py fetch --accounts @phantom,@solflare,@baseposting,@solana,@luminaries,@wallet,@jupiterexchange,@trustwallet,@metamask,@arkham,@ondofinance,@eigencloud,@maplefinance,@seinetwork,@soniclabs --count 20

# Then export to CSV
python x-research.py export --format csv --output data/fetched_tweets.csv
```

### Option 3: Use X API (Recommended for Production)

For more reliable and scalable fetching, use the official X API:

1. Get API credentials from https://developer.x.com/
2. Use a library like `tweepy`:

```python
import tweepy
import csv

# Set up API credentials
client = tweepy.Client(bearer_token="YOUR_BEARER_TOKEN")

accounts = ["phantom", "solflare", "baseposting", ...]
tweets_data = []

for account in accounts:
    # Get recent tweets
    tweets = client.get_users_tweets(
        username=account,
        max_results=20,
        tweet_fields=['created_at', 'public_metrics']
    )

    for tweet in tweets.data:
        tweets_data.append({
            'account_handle': f'@{account}',
            'tweet_url': f'https://x.com/{account}/status/{tweet.id}',
            'tweet_text': tweet.text,
            'likes': tweet.public_metrics['like_count'],
            'retweets': tweet.public_metrics['retweet_count'],
            'replies': tweet.public_metrics['reply_count'],
            'posted_date': tweet.created_at.strftime('%Y-%m-%d'),
            'notes': 'Fetched via API'
        })

# Write to CSV
with open('data/fetched_tweets.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=[...])
    writer.writeheader()
    writer.writerows(tweets_data)
```

### Option 4: Manual Collection

If automated methods don't work:

1. Visit each account on X.com
2. Copy tweet data manually
3. Use the CSV template at `/home/user/workflow/x-research/data/fetched_tweets.csv`

**CSV Format:**
```csv
account_handle,tweet_url,tweet_text,likes,retweets,replies,posted_date,notes
@phantom,https://x.com/phantom/status/123,Tweet text here,1234,567,89,2026-01-18,Auto-fetched
```

## Next Steps

Once you have the CSV populated:

1. **Import to database:**
   ```bash
   python x-research.py add data/fetched_tweets.csv
   ```

2. **Analyze the tweets:**
   ```bash
   python x-research.py analyze
   ```

3. **Generate reports:**
   ```bash
   python x-research.py analyze --format markdown
   ```

## Troubleshooting

### "ERR_TUNNEL_CONNECTION_FAILED"
- You're in an environment without direct internet access
- Try running the script in a different environment
- Consider using a VPN or proxy

### "JavaScript is not available"
- WebFetch cannot handle JavaScript-heavy sites like X.com
- Use browser automation (Playwright) or the X API instead

### Rate Limiting
- X may rate limit aggressive scraping
- Add delays between requests
- Use the official API for better rate limits
