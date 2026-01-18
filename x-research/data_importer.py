"""Data import module for X Research tool."""

import csv
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import os


class DataImporter:
    """Handles importing tweet data from CSV and JSON files."""

    @staticmethod
    def normalize_account_handle(handle: str) -> str:
        """Ensure account handle starts with @."""
        handle = handle.strip()
        if not handle.startswith('@'):
            return f'@{handle}'
        return handle

    @staticmethod
    def parse_date(date_str: str) -> str:
        """
        Parse date string and return in ISO format (YYYY-MM-DD).
        Supports various formats.
        """
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')

        date_str = date_str.strip()

        # Common formats to try
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue

        # If nothing works, return today's date
        return datetime.now().strftime('%Y-%m-%d')

    @staticmethod
    def parse_int(value: Any) -> Optional[int]:
        """Safely parse integer values."""
        if value is None or value == '':
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def validate_tweet_data(tweet: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate required fields are present.
        Returns (is_valid, error_message).
        """
        required_fields = ['account_handle', 'tweet_text', 'posted_date']

        for field in required_fields:
            if field not in tweet or not tweet[field]:
                return False, f"Missing required field: {field}"

        return True, ""

    @staticmethod
    def import_csv(file_path: str) -> List[Dict[str, Any]]:
        """Import tweets from CSV file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        tweets = []
        errors = []

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for i, row in enumerate(reader, start=2):  # Start at 2 (line 1 is header)
                try:
                    tweet = {
                        'account_handle': DataImporter.normalize_account_handle(
                            row.get('account_handle', '')
                        ),
                        'tweet_url': row.get('tweet_url', '').strip() or None,
                        'tweet_text': row.get('tweet_text', '').strip(),
                        'likes': DataImporter.parse_int(row.get('likes')),
                        'retweets': DataImporter.parse_int(row.get('retweets')),
                        'replies': DataImporter.parse_int(row.get('replies')),
                        'posted_date': DataImporter.parse_date(row.get('posted_date', '')),
                        'notes': row.get('notes', '').strip() or None,
                    }

                    is_valid, error = DataImporter.validate_tweet_data(tweet)
                    if not is_valid:
                        errors.append(f"Line {i}: {error}")
                        continue

                    tweets.append(tweet)

                except Exception as e:
                    errors.append(f"Line {i}: {str(e)}")

        if errors:
            error_msg = "\n".join(errors)
            raise ValueError(f"Errors found while parsing CSV:\n{error_msg}")

        return tweets

    @staticmethod
    def import_json(file_path: str) -> List[Dict[str, Any]]:
        """Import tweets from JSON file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("JSON file must contain an array of tweet objects")

        tweets = []
        errors = []

        for i, item in enumerate(data):
            try:
                tweet = {
                    'account_handle': DataImporter.normalize_account_handle(
                        item.get('account_handle', '')
                    ),
                    'tweet_url': item.get('tweet_url', '').strip() or None,
                    'tweet_text': item.get('tweet_text', '').strip(),
                    'likes': DataImporter.parse_int(item.get('likes')),
                    'retweets': DataImporter.parse_int(item.get('retweets')),
                    'replies': DataImporter.parse_int(item.get('replies')),
                    'posted_date': DataImporter.parse_date(item.get('posted_date', '')),
                    'notes': item.get('notes', '').strip() or None,
                }

                is_valid, error = DataImporter.validate_tweet_data(tweet)
                if not is_valid:
                    errors.append(f"Item {i}: {error}")
                    continue

                tweets.append(tweet)

            except Exception as e:
                errors.append(f"Item {i}: {str(e)}")

        if errors:
            error_msg = "\n".join(errors)
            raise ValueError(f"Errors found while parsing JSON:\n{error_msg}")

        return tweets

    @staticmethod
    def import_file(file_path: str) -> List[Dict[str, Any]]:
        """
        Auto-detect file type and import tweets.
        Supports .csv and .json files.
        """
        _, ext = os.path.splitext(file_path.lower())

        if ext == '.csv':
            return DataImporter.import_csv(file_path)
        elif ext == '.json':
            return DataImporter.import_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}. Use .csv or .json")
