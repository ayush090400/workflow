#!/usr/bin/env python3
"""
X Research - Automated X (Twitter) account research and analysis tool.
"""

import argparse
import sys
import os
from datetime import datetime
from pathlib import Path
import json
import csv

from database import Database
from data_importer import DataImporter
from analyzer import Analyzer
from browser_fetcher import BrowserFetcher


class XResearch:
    """Main CLI application for X Research tool."""

    def __init__(self):
        """Initialize the application."""
        self.base_dir = Path(__file__).parent
        self.db_path = self.base_dir / "database.db"
        self.reports_dir = self.base_dir / "reports"
        self.db = Database(str(self.db_path))

    def cmd_add(self, args):
        """Add tweets from a file to the database."""
        print(f"📥 Importing data from: {args.file}")

        try:
            tweets = DataImporter.import_file(args.file)
            print(f"✓ Parsed {len(tweets)} tweets from file")

            added, duplicates = self.db.add_tweets_bulk(tweets)

            print(f"\n✅ Import complete!")
            print(f"   • Added: {added} new tweets")
            print(f"   • Skipped: {duplicates} duplicates")

            if added > 0:
                print(f"\n💡 Run 'python x-research.py analyze' to generate insights")

        except FileNotFoundError as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
        except ValueError as e:
            print(f"❌ Error parsing file:\n{e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            sys.exit(1)

    def cmd_fetch(self, args):
        """Fetch tweets from X accounts automatically."""
        print("🌐 Fetching tweets from X accounts...\n")

        # Parse account list
        if args.accounts:
            accounts = [a.strip() for a in args.accounts.split(',')]
        else:
            print("❌ Error: No accounts specified")
            print("\nUsage: python x-research.py fetch --accounts @user1,@user2")
            sys.exit(1)

        # Parse count
        count = args.count if args.count else 20

        try:
            # Initialize browser fetcher
            fetcher = BrowserFetcher()

            # Fetch tweets
            results = fetcher.fetch_multiple_accounts(
                accounts,
                tweets_per_account=count,
                headless=not args.show_browser
            )

            # Add all fetched tweets to database
            total_added = 0
            total_duplicates = 0

            for account, tweets in results.items():
                if tweets:
                    added, duplicates = self.db.add_tweets_bulk(tweets)
                    total_added += added
                    total_duplicates += duplicates

            print(f"\n✅ Fetch complete!")
            print(f"   • Added: {total_added} new tweets")
            print(f"   • Skipped: {total_duplicates} duplicates")

            if total_added > 0:
                print(f"\n💡 Run 'python x-research.py analyze' to generate insights")

        except ImportError as e:
            print(f"❌ {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Fetch failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    def cmd_analyze(self, args):
        """Analyze tweets and generate insights."""
        print("🔍 Analyzing tweets...\n")

        # Get API key
        api_key = self.db.get_config('anthropic_api_key')
        if not api_key:
            api_key = os.environ.get('ANTHROPIC_API_KEY')

        if not api_key:
            print("❌ Error: Anthropic API key not found.")
            print("\nSet it using one of these methods:")
            print("  1. Run: python x-research.py config")
            print("  2. Set environment variable: export ANTHROPIC_API_KEY='your-key'")
            sys.exit(1)

        # Parse accounts filter if provided
        accounts = None
        if args.accounts:
            accounts = [a.strip() for a in args.accounts.split(',')]
            accounts = [DataImporter.normalize_account_handle(a) for a in accounts]

        # Get tweets
        tweets = self.db.get_tweets(
            accounts=accounts,
            days=args.days,
            since_last_analysis=args.since_last
        )

        if not tweets:
            print("❌ No tweets found with the specified filters.")
            print("\nTry:")
            print("  • Adding data first: python x-research.py add <file>")
            print("  • Removing filters: python x-research.py analyze")
            sys.exit(1)

        print(f"Found {len(tweets)} tweets to analyze")

        # Get previous insights if analyzing since last
        previous_insights = None
        if args.since_last:
            # TODO: Could load last analysis for context
            pass

        # Run analysis
        try:
            analyzer = Analyzer(api_key)
            print("⏳ Sending to Claude for analysis...")

            insights = analyzer.analyze_tweets(tweets, previous_insights)

            if 'error' in insights:
                print(f"❌ Analysis failed: {insights['error']}")
                sys.exit(1)

            # Count new tweets if using since_last
            new_count = len(tweets) if args.since_last else 0

            # Output based on format
            if args.format == 'json':
                output = json.dumps(insights, indent=2)
                print(output)
            elif args.format == 'markdown':
                output = analyzer.format_for_markdown(insights, new_count)
                print(output)
            else:  # terminal (default)
                output = analyzer.format_for_terminal(insights, new_count)
                print(output)

            # Save to reports directory
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
            if args.format == 'json':
                report_file = self.reports_dir / f"analysis_{timestamp}.json"
                with open(report_file, 'w') as f:
                    json.dump(insights, f, indent=2)
            else:  # markdown for both markdown and terminal
                report_file = self.reports_dir / f"analysis_{timestamp}.md"
                md_content = analyzer.format_for_markdown(insights, new_count)
                with open(report_file, 'w') as f:
                    f.write(md_content)

            print(f"Report saved to: {report_file}")

            # Save analysis to database
            self.db.save_analysis(len(tweets), insights)

        except ImportError:
            print("❌ Error: anthropic library not installed")
            print("\nInstall with: pip install anthropic")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    def cmd_stats(self, args):
        """Show database statistics."""
        stats = self.db.get_stats()

        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                     Database Statistics                     ║")
        print("╚══════════════════════════════════════════════════════════════╝\n")

        print(f"Total tweets: {stats['total_tweets']}")
        print(f"Accounts tracked: {stats['total_accounts']}")

        if stats['min_date'] and stats['max_date']:
            print(f"Date range: {stats['min_date']} - {stats['max_date']}")

        if stats['last_analysis']:
            last = datetime.fromisoformat(stats['last_analysis'])
            days_ago = (datetime.now() - last).days
            print(f"Last analysis: {last.strftime('%b %d, %Y')} ({days_ago} days ago)")

        print(f"Total analyses run: {stats['total_analyses']}")

        if stats['top_accounts']:
            print("\nTop Accounts by Volume:")
            for i, account in enumerate(stats['top_accounts'][:10], 1):
                print(f"  {i}. {account['account_handle']} - {account['tweet_count']} tweets")

    def cmd_accounts(self, args):
        """List all tracked accounts."""
        accounts = self.db.get_accounts()

        if not accounts:
            print("No accounts tracked yet.")
            print("\nAdd data with: python x-research.py add <file>")
            return

        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                      Tracked Accounts                        ║")
        print("╚══════════════════════════════════════════════════════════════╝\n")

        for account in accounts:
            last_tweet = account.get('last_tweet', 'unknown')
            print(f"{account['account_handle']} ({account['tweet_count']} tweets, last: {last_tweet})")

    def cmd_export(self, args):
        """Export all tweets to a file."""
        tweets = self.db.export_all_tweets()

        if not tweets:
            print("No tweets to export.")
            return

        # Determine output file
        if args.output:
            output_file = args.output
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ext = 'json' if args.format == 'json' else 'csv'
            output_file = f"export_{timestamp}.{ext}"

        try:
            if args.format == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(tweets, f, indent=2, default=str)
            else:  # csv
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    if tweets:
                        fieldnames = tweets[0].keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(tweets)

            print(f"✅ Exported {len(tweets)} tweets to: {output_file}")

        except Exception as e:
            print(f"❌ Export failed: {e}")
            sys.exit(1)

    def cmd_config(self, args):
        """Configure the tool (API key, preferences)."""
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                    Configuration Setup                       ║")
        print("╚══════════════════════════════════════════════════════════════╝\n")

        # Check for existing API key
        existing_key = self.db.get_config('anthropic_api_key')
        if existing_key:
            print("✓ Anthropic API key is already configured")
            response = input("\nDo you want to update it? (y/N): ")
            if response.lower() != 'y':
                print("Configuration unchanged.")
                return

        print("\n📝 Anthropic API Key Setup")
        print("\nYou need an Anthropic API key to use the analysis feature.")
        print("Get your API key at: https://console.anthropic.com/")
        print("\nThe key will be stored locally in the database.")

        api_key = input("\nEnter your Anthropic API key: ").strip()

        if not api_key:
            print("❌ No API key provided. Configuration cancelled.")
            return

        # Validate key format (basic check)
        if not api_key.startswith('sk-ant-'):
            print("⚠️  Warning: API key doesn't match expected format (should start with 'sk-ant-')")
            response = input("Save anyway? (y/N): ")
            if response.lower() != 'y':
                print("Configuration cancelled.")
                return

        # Save to database
        self.db.set_config('anthropic_api_key', api_key)
        print("\n✅ API key saved successfully!")
        print("\nYou're all set! Try running:")
        print("  python x-research.py analyze")

    def run(self):
        """Run the CLI application."""
        parser = argparse.ArgumentParser(
            description='X Research - Automated X account research and analysis',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        subparsers = parser.add_subparsers(dest='command', help='Commands')

        # Add command
        add_parser = subparsers.add_parser('add', help='Add tweets from a file')
        add_parser.add_argument('file', help='CSV or JSON file to import')

        # Fetch command
        fetch_parser = subparsers.add_parser('fetch', help='Fetch tweets automatically from X accounts')
        fetch_parser.add_argument('--accounts', required=True,
                                 help='Comma-separated list of accounts to fetch (e.g., @sama,@levelsio)')
        fetch_parser.add_argument('--count', type=int, default=20,
                                 help='Number of tweets to fetch per account (default: 20)')
        fetch_parser.add_argument('--show-browser', action='store_true',
                                 help='Show browser window (default: headless mode)')

        # Analyze command
        analyze_parser = subparsers.add_parser('analyze', help='Analyze tweets and generate insights')
        analyze_parser.add_argument('--accounts', help='Comma-separated list of accounts to analyze')
        analyze_parser.add_argument('--days', type=int, help='Only analyze tweets from last N days')
        analyze_parser.add_argument('--since-last', action='store_true',
                                   help='Only analyze new tweets since last analysis')
        analyze_parser.add_argument('--format', choices=['terminal', 'markdown', 'json'],
                                   default='terminal', help='Output format')

        # Stats command
        subparsers.add_parser('stats', help='Show database statistics')

        # Accounts command
        subparsers.add_parser('accounts', help='List all tracked accounts')

        # Export command
        export_parser = subparsers.add_parser('export', help='Export all tweets to a file')
        export_parser.add_argument('--format', choices=['csv', 'json'], default='csv',
                                  help='Export format')
        export_parser.add_argument('--output', help='Output filename')

        # Config command
        subparsers.add_parser('config', help='Configure API key and preferences')

        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            sys.exit(1)

        # Route to appropriate command
        command_map = {
            'add': self.cmd_add,
            'fetch': self.cmd_fetch,
            'analyze': self.cmd_analyze,
            'stats': self.cmd_stats,
            'accounts': self.cmd_accounts,
            'export': self.cmd_export,
            'config': self.cmd_config,
        }

        handler = command_map.get(args.command)
        if handler:
            handler(args)
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)


def main():
    """Entry point for the application."""
    app = XResearch()
    app.run()


if __name__ == '__main__':
    main()
