"""Analysis module using Claude API for X Research tool."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json


class Analyzer:
    """Handles tweet analysis using Claude API."""

    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-20241022"):
        """Initialize analyzer with API key."""
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError(
                "anthropic library not installed. "
                "Install with: pip install anthropic"
            )

        self.client = Anthropic(api_key=api_key)
        self.model = model

    def _build_analysis_prompt(
        self,
        tweets: List[Dict[str, Any]],
        previous_insights: Optional[Dict] = None
    ) -> str:
        """Build the prompt for Claude with tweet data."""

        # Group tweets by account
        accounts_data = {}
        for tweet in tweets:
            handle = tweet['account_handle']
            if handle not in accounts_data:
                accounts_data[handle] = []
            accounts_data[handle].append(tweet)

        # Build tweet data section
        tweet_data_section = ""
        for account, account_tweets in accounts_data.items():
            tweet_data_section += f"\n## {account} ({len(account_tweets)} tweets)\n\n"
            for i, tweet in enumerate(account_tweets, 1):
                tweet_data_section += f"### Tweet {i}\n"
                tweet_data_section += f"**Posted:** {tweet['posted_date']}\n"
                tweet_data_section += f"**Text:** {tweet['tweet_text']}\n"

                if tweet.get('likes') is not None:
                    tweet_data_section += f"**Engagement:** {tweet['likes']} likes, "
                    tweet_data_section += f"{tweet.get('retweets', 0)} retweets, "
                    tweet_data_section += f"{tweet.get('replies', 0)} replies\n"

                if tweet.get('notes'):
                    tweet_data_section += f"**Notes:** {tweet['notes']}\n"

                if tweet.get('tweet_url'):
                    tweet_data_section += f"**URL:** {tweet['tweet_url']}\n"

                tweet_data_section += "\n"

        # Build the main prompt
        prompt = f"""You are analyzing X (Twitter) content to identify patterns, trends, and tactical insights.

# TWEET DATA

{tweet_data_section}

# YOUR TASK

Analyze the tweets above and provide insights in the following structure:

## 1. TOP PATTERNS & TRENDS
Identify 3-5 major patterns across the accounts. For each pattern:
- Describe what you're seeing
- Quantify it where possible (percentages, frequencies)
- Cite specific examples with account names
- Explain why it matters

## 2. WHAT'S WORKING
List specific tactics/approaches that are getting strong engagement:
- Be specific (not "be authentic" but "personal stories with specific data points")
- Include examples from the data
- Note which accounts are doing this well

## 3. WHAT'S NOT WORKING
Identify approaches with consistently lower engagement:
- Be specific about what's falling flat
- Include examples if present in the data

## 4. TACTICAL TAKEAWAYS
Provide 3-5 concrete, actionable tactics the user can implement:
- Each should be specific and testable
- Should be based on patterns in the data
- Focus on things they can do in their next few tweets

## 5. NEW & EMERGING
Highlight anything that appears to be new, experimental, or changing:
- New formats being tested
- Shifts in approach or tone
- Topics gaining traction

# IMPORTANT GUIDELINES

- Be specific and data-driven. Cite actual tweets when making points.
- Quantify observations when possible ("5 out of 8 accounts", "40% of high-performing tweets")
- Focus on actionable insights, not generic advice
- Compare across accounts to find commonalities among top performers
- Highlight what's NEW or CHANGING, not just what's consistent
- Keep your analysis concise but insightful

Provide your analysis now."""

        if previous_insights:
            prompt += f"\n\n# PREVIOUS ANALYSIS CONTEXT\n\nFor reference, here are insights from the last analysis:\n{json.dumps(previous_insights, indent=2)}\n\nFocus on what's NEW or CHANGED since then."

        return prompt

    def analyze_tweets(
        self,
        tweets: List[Dict[str, Any]],
        previous_insights: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze tweets using Claude API.
        Returns structured insights.
        """
        if not tweets:
            return {
                'error': 'No tweets to analyze',
                'summary': {},
                'analysis': 'No data available for analysis.'
            }

        prompt = self._build_analysis_prompt(tweets, previous_insights)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            analysis_text = response.content[0].text

            # Calculate summary stats
            unique_accounts = len(set(t['account_handle'] for t in tweets))
            dates = [t['posted_date'] for t in tweets if t.get('posted_date')]
            date_range = {
                'start': min(dates) if dates else None,
                'end': max(dates) if dates else None
            }

            return {
                'analysis_text': analysis_text,
                'summary': {
                    'total_tweets': len(tweets),
                    'unique_accounts': unique_accounts,
                    'date_range': date_range,
                    'model_used': self.model
                },
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': str(e),
                'summary': {},
                'analysis': f'Error during analysis: {str(e)}'
            }

    def format_for_terminal(self, insights: Dict[str, Any], new_tweets: int = 0) -> str:
        """Format insights for terminal display."""
        if 'error' in insights:
            return f"Error: {insights['error']}"

        summary = insights.get('summary', {})
        analysis_text = insights.get('analysis_text', 'No analysis available')

        # Build header
        output = "╔══════════════════════════════════════════════════════════════╗\n"
        output += f"║           X RESEARCH INSIGHTS - {datetime.now().strftime('%b %d, %Y')}                 ║\n"
        output += "╚══════════════════════════════════════════════════════════════╝\n\n"

        # Data summary
        output += "📊 DATA SUMMARY\n"
        output += "─────────────────────────────────────────────────────────────\n"
        output += f"• Total tweets analyzed: {summary.get('total_tweets', 0)}\n"
        output += f"• Accounts tracked: {summary.get('unique_accounts', 0)}\n"

        date_range = summary.get('date_range', {})
        if date_range.get('start') and date_range.get('end'):
            output += f"• Date range: {date_range['start']} - {date_range['end']}\n"

        if new_tweets > 0:
            output += f"• New tweets since last analysis: {new_tweets}\n"

        output += "\n"

        # Main analysis
        output += analysis_text

        output += "\n\n─────────────────────────────────────────────────────────────\n"

        return output

    def format_for_markdown(self, insights: Dict[str, Any], new_tweets: int = 0) -> str:
        """Format insights as markdown file."""
        summary = insights.get('summary', {})
        analysis_text = insights.get('analysis_text', 'No analysis available')

        output = f"# X Research Insights - {datetime.now().strftime('%B %d, %Y')}\n\n"

        # Data summary
        output += "## 📊 Data Summary\n\n"
        output += f"- **Total tweets analyzed:** {summary.get('total_tweets', 0)}\n"
        output += f"- **Accounts tracked:** {summary.get('unique_accounts', 0)}\n"

        date_range = summary.get('date_range', {})
        if date_range.get('start') and date_range.get('end'):
            output += f"- **Date range:** {date_range['start']} to {date_range['end']}\n"

        if new_tweets > 0:
            output += f"- **New tweets since last analysis:** {new_tweets}\n"

        output += f"\n---\n\n"
        output += analysis_text
        output += f"\n\n---\n\n"
        output += f"*Analysis generated on {insights.get('timestamp', 'unknown')}*\n"
        output += f"*Model: {summary.get('model_used', 'unknown')}*\n"

        return output
