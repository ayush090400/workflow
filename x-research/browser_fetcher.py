"""Browser-based tweet fetching using Playwright."""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time


class BrowserFetcher:
    """Fetches tweets using browser automation (Playwright)."""

    def __init__(self):
        """Initialize the browser fetcher."""
        self.browser = None
        self.context = None
        self.page = None

    def _ensure_playwright(self):
        """Ensure playwright is installed."""
        try:
            from playwright.sync_api import sync_playwright
            return sync_playwright
        except ImportError:
            raise ImportError(
                "Playwright not installed. Install with:\n"
                "  pip install playwright\n"
                "  playwright install chromium"
            )

    @staticmethod
    def normalize_handle(handle: str) -> str:
        """Normalize account handle."""
        handle = handle.strip()
        if handle.startswith('@'):
            handle = handle[1:]
        return handle

    @staticmethod
    def parse_relative_date(date_str: str) -> str:
        """
        Convert relative dates like '2h', '1d', 'Jan 15' to ISO format.
        """
        now = datetime.now()

        date_str = date_str.strip().lower()

        # Handle hours/minutes/seconds ago
        if 'h' in date_str or 'm' in date_str or 's' in date_str:
            return now.strftime('%Y-%m-%d')

        # Handle days ago
        if 'd' in date_str or 'day' in date_str:
            match = re.search(r'(\d+)', date_str)
            if match:
                days = int(match.group(1))
                date = now - timedelta(days=days)
                return date.strftime('%Y-%m-%d')
            return now.strftime('%Y-%m-%d')

        # Handle "Jan 15" or "January 15" format
        month_day_match = re.search(r'([A-Za-z]{3,9})\s+(\d{1,2})', date_str)
        if month_day_match:
            try:
                month_str = month_day_match.group(1)
                day_str = month_day_match.group(2)

                # Try full month name first, then abbreviated
                for fmt in ["%B %d %Y", "%b %d %Y"]:
                    try:
                        date = datetime.strptime(
                            f"{month_str} {day_str} {now.year}", fmt
                        )
                        # If date is in future, use last year
                        if date > now:
                            date = datetime.strptime(
                                f"{month_str} {day_str} {now.year - 1}", fmt
                            )
                        return date.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
            except:
                pass

        # Default to today
        return now.strftime('%Y-%m-%d')

    def fetch_account_tweets(
        self,
        account_handle: str,
        count: int = 20,
        headless: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent tweets from an X account using browser automation.

        Args:
            account_handle: X username (with or without @)
            count: Target number of tweets to fetch
            headless: Run browser in headless mode (no GUI)

        Returns:
            List of tweet dictionaries
        """
        sync_playwright = self._ensure_playwright()
        handle = self.normalize_handle(account_handle)
        url = f"https://x.com/{handle}"

        tweets = []

        with sync_playwright() as p:
            try:
                # Launch browser
                browser = p.chromium.launch(headless=headless)
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()

                # Navigate to profile
                page.goto(url, wait_until='networkidle', timeout=30000)

                # Wait for tweets to load
                time.sleep(3)

                # Scroll a few times to load more tweets
                for _ in range(3):
                    page.evaluate('window.scrollBy(0, window.innerHeight)')
                    time.sleep(1)

                # Extract tweets
                tweet_elements = page.query_selector_all('article[data-testid="tweet"]')

                for elem in tweet_elements[:count]:
                    try:
                        tweet_data = self._extract_tweet_data(elem, handle)
                        if tweet_data and tweet_data.get('tweet_text'):
                            tweets.append(tweet_data)
                    except Exception as e:
                        print(f"  Warning: Failed to parse tweet: {e}")
                        continue

                browser.close()

            except Exception as e:
                print(f"  Error fetching from @{handle}: {e}")
                if browser:
                    browser.close()

        return tweets

    def _extract_tweet_data(self, element, handle: str) -> Optional[Dict[str, Any]]:
        """Extract data from a tweet element."""
        try:
            # Extract tweet text
            text_elem = element.query_selector('[data-testid="tweetText"]')
            tweet_text = text_elem.inner_text() if text_elem else None

            if not tweet_text:
                return None

            # Extract timestamp
            time_elem = element.query_selector('time')
            posted_date = datetime.now().strftime('%Y-%m-%d')
            if time_elem:
                datetime_attr = time_elem.get_attribute('datetime')
                if datetime_attr:
                    try:
                        dt = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                        posted_date = dt.strftime('%Y-%m-%d')
                    except:
                        # Fallback to parsing title/aria-label
                        title = time_elem.get_attribute('title')
                        if title:
                            posted_date = self.parse_relative_date(title)

            # Extract engagement metrics
            likes = self._extract_metric(element, 'like')
            retweets = self._extract_metric(element, 'retweet')
            replies = self._extract_metric(element, 'reply')

            # Try to extract tweet URL
            tweet_url = None
            link_elem = element.query_selector('a[href*="/status/"]')
            if link_elem:
                href = link_elem.get_attribute('href')
                if href:
                    tweet_url = f"https://x.com{href}"

            return {
                'account_handle': f'@{handle}',
                'tweet_text': tweet_text.strip(),
                'tweet_url': tweet_url,
                'likes': likes,
                'retweets': retweets,
                'replies': replies,
                'posted_date': posted_date,
                'notes': 'Auto-fetched via browser'
            }

        except Exception as e:
            return None

    def _extract_metric(self, element, metric_type: str) -> Optional[int]:
        """Extract engagement metric (likes, retweets, replies)."""
        try:
            # Try to find the metric button/element
            selector = f'[data-testid="{metric_type}"]'
            metric_elem = element.query_selector(selector)

            if metric_elem:
                aria_label = metric_elem.get_attribute('aria-label')
                if aria_label:
                    # Extract number from aria-label
                    match = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?[KMB]?)', aria_label)
                    if match:
                        num_str = match.group(1)
                        return self._parse_number_string(num_str)

            return None

        except:
            return None

    def _parse_number_string(self, num_str: str) -> int:
        """Parse number strings like '1.2K', '3M', '500'."""
        num_str = num_str.strip().replace(',', '')

        # Handle K, M, B suffixes
        multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}

        for suffix, multiplier in multipliers.items():
            if num_str.endswith(suffix):
                try:
                    base = float(num_str[:-1])
                    return int(base * multiplier)
                except ValueError:
                    return 0

        # Plain number
        try:
            return int(float(num_str))
        except ValueError:
            return 0

    def fetch_multiple_accounts(
        self,
        account_handles: List[str],
        tweets_per_account: int = 20,
        headless: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch tweets from multiple accounts.

        Args:
            account_handles: List of X usernames
            tweets_per_account: How many tweets to fetch per account
            headless: Run browser in headless mode

        Returns:
            Dictionary mapping account handles to their tweets
        """
        results = {}

        for handle in account_handles:
            normalized = self.normalize_handle(handle)
            print(f"Fetching tweets from @{normalized}...")

            tweets = self.fetch_account_tweets(
                handle,
                count=tweets_per_account,
                headless=headless
            )

            results[f'@{normalized}'] = tweets
            print(f"  ✓ Found {len(tweets)} tweets")

            # Small delay between accounts
            time.sleep(2)

        return results
