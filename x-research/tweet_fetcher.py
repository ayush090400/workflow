"""Tweet fetching module using WebFetch for X Research tool."""

import re
from typing import List, Dict, Any
from datetime import datetime, timedelta
import json


class TweetFetcher:
    """Fetches tweets from X accounts using web scraping."""

    def __init__(self, webfetch_func):
        """
        Initialize with a webfetch function.

        Args:
            webfetch_func: Function that takes (url, prompt) and returns text response
        """
        self.webfetch = webfetch_func

    @staticmethod
    def normalize_handle(handle: str) -> str:
        """Normalize account handle."""
        handle = handle.strip()
        # Remove @ if present
        if handle.startswith('@'):
            handle = handle[1:]
        return handle

    @staticmethod
    def parse_relative_date(date_str: str) -> str:
        """
        Convert relative dates like '2h', '1d', 'Jan 15' to ISO format.

        Args:
            date_str: Relative date string from tweet

        Returns:
            ISO formatted date string (YYYY-MM-DD)
        """
        now = datetime.now()

        # Handle hours ago (2h, 3h, etc)
        if re.match(r'^\d+h$', date_str):
            hours = int(date_str[:-1])
            date = now - timedelta(hours=hours)
            return date.strftime('%Y-%m-%d')

        # Handle minutes ago (30m, 45m, etc)
        if re.match(r'^\d+m$', date_str):
            return now.strftime('%Y-%m-%d')

        # Handle days ago (1d, 2d, etc)
        if re.match(r'^\d+d$', date_str):
            days = int(date_str[:-1])
            date = now - timedelta(days=days)
            return date.strftime('%Y-%m-%d')

        # Handle "Jan 15" format
        if re.match(r'^[A-Z][a-z]{2}\s+\d{1,2}$', date_str):
            try:
                # Assume current year
                month_day = date_str
                date = datetime.strptime(f"{month_day} {now.year}", "%b %d %Y")

                # If date is in future, assume it's from last year
                if date > now:
                    date = datetime.strptime(f"{month_day} {now.year - 1}", "%b %d %Y")

                return date.strftime('%Y-%m-%d')
            except:
                pass

        # Default to today if can't parse
        return now.strftime('%Y-%m-%d')

    def fetch_account_tweets(
        self,
        account_handle: str,
        count: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent tweets from an X account.

        Args:
            account_handle: X username (with or without @)
            count: Target number of tweets to fetch (may get fewer)

        Returns:
            List of tweet dictionaries
        """
        handle = self.normalize_handle(account_handle)
        url = f"https://x.com/{handle}"

        prompt = f"""Extract the most recent tweets from this X profile page.

For each tweet, provide the following information:
- The full tweet text
- Engagement metrics if visible (likes, retweets, replies)
- When it was posted (relative time like "2h" or "Jan 15")
- Tweet URL if available

Please return the data as a JSON array with this structure:
[
  {{
    "tweet_text": "Full tweet content here",
    "likes": 123,
    "retweets": 45,
    "replies": 12,
    "posted_date": "2h",
    "tweet_url": "https://x.com/user/status/123456"
  }}
]

Extract up to {count} of the most recent tweets. If engagement metrics aren't visible, omit those fields.
Only include actual tweets from the account, not retweets or replies unless they have significant content.

Return ONLY the JSON array, no other text."""

        try:
            response = self.webfetch(url, prompt)

            # Try to extract JSON from response
            tweets_data = self._extract_json_from_response(response)

            if not tweets_data:
                # Fallback: parse response manually
                return self._parse_fallback_response(response, handle)

            # Process and normalize the tweets
            processed_tweets = []
            for tweet in tweets_data[:count]:
                processed = {
                    'account_handle': f'@{handle}',
                    'tweet_text': tweet.get('tweet_text', '').strip(),
                    'tweet_url': tweet.get('tweet_url'),
                    'likes': tweet.get('likes'),
                    'retweets': tweet.get('retweets'),
                    'replies': tweet.get('replies'),
                    'posted_date': self.parse_relative_date(
                        tweet.get('posted_date', '')
                    ),
                    'notes': 'Auto-fetched'
                }

                # Only add if we have tweet text
                if processed['tweet_text']:
                    processed_tweets.append(processed)

            return processed_tweets

        except Exception as e:
            print(f"Error fetching tweets from @{handle}: {e}")
            return []

    def _extract_json_from_response(self, response: str) -> List[Dict]:
        """Try to extract JSON array from response text."""
        try:
            # Try direct JSON parse
            return json.loads(response)
        except:
            pass

        # Try to find JSON array in response
        json_match = re.search(r'\[\s*\{.*\}\s*\]', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass

        return None

    def _parse_fallback_response(
        self,
        response: str,
        handle: str
    ) -> List[Dict[str, Any]]:
        """
        Fallback parser if JSON extraction fails.
        Parse response text to extract tweet information.
        """
        tweets = []

        # Split by common separators
        lines = response.split('\n')

        current_tweet = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for tweet text patterns
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                # Save previous tweet if exists
                if current_tweet.get('tweet_text'):
                    tweets.append(current_tweet)

                # Start new tweet
                current_tweet = {
                    'account_handle': f'@{handle}',
                    'tweet_text': line.lstrip('-•* '),
                    'posted_date': datetime.now().strftime('%Y-%m-%d'),
                    'notes': 'Auto-fetched'
                }

        # Add last tweet
        if current_tweet.get('tweet_text'):
            tweets.append(current_tweet)

        return tweets

    def fetch_multiple_accounts(
        self,
        account_handles: List[str],
        tweets_per_account: int = 20
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch tweets from multiple accounts.

        Args:
            account_handles: List of X usernames
            tweets_per_account: How many tweets to fetch per account

        Returns:
            Dictionary mapping account handles to their tweets
        """
        results = {}

        for handle in account_handles:
            print(f"Fetching tweets from {handle}...")
            tweets = self.fetch_account_tweets(handle, tweets_per_account)
            results[handle] = tweets
            print(f"  ✓ Found {len(tweets)} tweets")

        return results
