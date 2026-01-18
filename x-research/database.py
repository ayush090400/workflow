"""Database module for X Research tool."""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any
import json


class Database:
    """Handles all database operations for the X Research tool."""

    def __init__(self, db_path: str = "database.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        cursor = self.conn.cursor()

        # Tweets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tweets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_handle TEXT NOT NULL,
                tweet_url TEXT,
                tweet_text TEXT NOT NULL,
                likes INTEGER,
                retweets INTEGER,
                replies INTEGER,
                posted_date TEXT NOT NULL,
                ingested_date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_account_handle
            ON tweets(account_handle)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_posted_date
            ON tweets(posted_date)
        """)

        # Analyses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_date TEXT NOT NULL,
                tweets_analyzed INTEGER NOT NULL,
                insights_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Config table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        self.conn.commit()

    def add_tweet(self, tweet_data: Dict[str, Any]) -> bool:
        """
        Add a tweet to the database.
        Returns True if added, False if duplicate.
        """
        cursor = self.conn.cursor()

        # Check for duplicate (same account and text)
        cursor.execute("""
            SELECT id FROM tweets
            WHERE account_handle = ? AND tweet_text = ?
        """, (tweet_data['account_handle'], tweet_data['tweet_text']))

        if cursor.fetchone():
            return False  # Duplicate

        # Insert tweet
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO tweets (
                account_handle, tweet_url, tweet_text, likes, retweets,
                replies, posted_date, ingested_date, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tweet_data['account_handle'],
            tweet_data.get('tweet_url'),
            tweet_data['tweet_text'],
            tweet_data.get('likes'),
            tweet_data.get('retweets'),
            tweet_data.get('replies'),
            tweet_data['posted_date'],
            now,
            tweet_data.get('notes'),
            now
        ))

        self.conn.commit()
        return True

    def add_tweets_bulk(self, tweets: List[Dict[str, Any]]) -> tuple:
        """
        Add multiple tweets to the database.
        Returns (added_count, duplicate_count).
        """
        added = 0
        duplicates = 0

        for tweet in tweets:
            if self.add_tweet(tweet):
                added += 1
            else:
                duplicates += 1

        return added, duplicates

    def get_tweets(
        self,
        accounts: Optional[List[str]] = None,
        days: Optional[int] = None,
        since_last_analysis: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieve tweets from database with optional filters.
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM tweets WHERE 1=1"
        params = []

        if accounts:
            placeholders = ','.join('?' * len(accounts))
            query += f" AND account_handle IN ({placeholders})"
            params.extend(accounts)

        if days:
            query += " AND posted_date >= date('now', '-' || ? || ' days')"
            params.append(days)

        if since_last_analysis:
            last_analysis = self.get_last_analysis_date()
            if last_analysis:
                query += " AND ingested_date > ?"
                params.append(last_analysis)

        query += " ORDER BY posted_date DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        cursor = self.conn.cursor()

        # Total tweets
        cursor.execute("SELECT COUNT(*) as count FROM tweets")
        total_tweets = cursor.fetchone()['count']

        # Unique accounts
        cursor.execute("SELECT COUNT(DISTINCT account_handle) as count FROM tweets")
        total_accounts = cursor.fetchone()['count']

        # Date range
        cursor.execute("""
            SELECT MIN(posted_date) as min_date, MAX(posted_date) as max_date
            FROM tweets
        """)
        date_range = cursor.fetchone()

        # Last analysis
        cursor.execute("""
            SELECT analysis_date FROM analyses
            ORDER BY created_at DESC LIMIT 1
        """)
        last_analysis = cursor.fetchone()

        # Total analyses
        cursor.execute("SELECT COUNT(*) as count FROM analyses")
        total_analyses = cursor.fetchone()['count']

        # Top accounts by volume
        cursor.execute("""
            SELECT account_handle, COUNT(*) as tweet_count
            FROM tweets
            GROUP BY account_handle
            ORDER BY tweet_count DESC
            LIMIT 10
        """)
        top_accounts = cursor.fetchall()

        return {
            'total_tweets': total_tweets,
            'total_accounts': total_accounts,
            'min_date': date_range['min_date'] if date_range else None,
            'max_date': date_range['max_date'] if date_range else None,
            'last_analysis': last_analysis['analysis_date'] if last_analysis else None,
            'total_analyses': total_analyses,
            'top_accounts': [dict(row) for row in top_accounts]
        }

    def get_accounts(self) -> List[Dict[str, Any]]:
        """Get list of all tracked accounts with stats."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                account_handle,
                COUNT(*) as tweet_count,
                MAX(posted_date) as last_tweet
            FROM tweets
            GROUP BY account_handle
            ORDER BY tweet_count DESC
        """)

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def save_analysis(self, tweets_analyzed: int, insights: Dict[str, Any]) -> int:
        """Save an analysis to the database. Returns analysis ID."""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO analyses (analysis_date, tweets_analyzed, insights_json, created_at)
            VALUES (?, ?, ?, ?)
        """, (now, tweets_analyzed, json.dumps(insights), now))

        self.conn.commit()
        return cursor.lastrowid

    def get_last_analysis_date(self) -> Optional[str]:
        """Get the date of the last analysis."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT analysis_date FROM analyses
            ORDER BY created_at DESC LIMIT 1
        """)
        result = cursor.fetchone()
        return result['analysis_date'] if result else None

    def set_config(self, key: str, value: str):
        """Set a configuration value."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO config (key, value)
            VALUES (?, ?)
        """, (key, value))
        self.conn.commit()

    def get_config(self, key: str) -> Optional[str]:
        """Get a configuration value."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        result = cursor.fetchone()
        return result['value'] if result else None

    def export_all_tweets(self) -> List[Dict[str, Any]]:
        """Export all tweets from the database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tweets ORDER BY posted_date DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def close(self):
        """Close the database connection."""
        self.conn.close()
