"""
database.py - SQLite Database Storage & Deduplication Engine
وكيل الرصد والذكاء الإخباري الشامل (AI & Sports Autonomous Watchdog)
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import config


class NewsDatabase:
    """Lightweight SQLite database manager for tracking processed news and audit runs."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or config.DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite connection with row factory."""
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Initializes database schema and indexes if they do not already exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Main news table storing unique processed articles
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guid_hash TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    link TEXT NOT NULL,
                    category TEXT NOT NULL,
                    sub_category TEXT,
                    source TEXT NOT NULL,
                    score REAL DEFAULT 0.0,
                    tags TEXT,
                    published_at TEXT,
                    processed_at TEXT NOT NULL
                );
            """)

            # Index for lightning-fast deduplication lookup
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_news_guid_hash ON news(guid_hash);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_news_processed_at ON news(processed_at);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_news_category ON news(category);
            """)

            # Audit log table recording execution metrics per run
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_fetched INTEGER NOT NULL,
                    new_articles INTEGER NOT NULL,
                    top_picked INTEGER NOT NULL,
                    status TEXT NOT NULL
                );
            """)
            conn.commit()

    def is_duplicate(self, guid_hash: str) -> bool:
        """Checks whether an article with the given GUID hash has already been recorded."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM news WHERE guid_hash = ? LIMIT 1;", (guid_hash,))
            return cursor.fetchone() is not None

    def save_item(
        self,
        guid_hash: str,
        title: str,
        link: str,
        category: str,
        sub_category: str,
        source: str,
        score: float,
        tags: str = "",
        published_at: str = "",
    ) -> bool:
        """
        Saves a newly processed news item.
        Returns True if inserted successfully, False if already exists (duplicate).
        """
        now_utc = datetime.now(timezone.utc).isoformat()
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO news (
                        guid_hash, title, link, category, sub_category, source, score, tags, published_at, processed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (guid_hash, title, link, category, sub_category, source, score, tags, published_at, now_utc))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            # Duplicate entry caught by UNIQUE constraint
            return False

    def record_run(
        self, total_fetched: int, new_articles: int, top_picked: int, status: str = "SUCCESS"
    ) -> int:
        """Logs execution metrics to the runs audit table."""
        now_utc = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO runs (timestamp, total_fetched, new_articles, top_picked, status)
                VALUES (?, ?, ?, ?, ?)
            """, (now_utc, total_fetched, new_articles, top_picked, status))
            conn.commit()
            return cursor.lastrowid or 0

    def get_statistics(self) -> Dict[str, Any]:
        """Retrieves global watchdog performance statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM news;")
            total_stored = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM news WHERE category = 'tech_ai';")
            total_tech = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM news WHERE category = 'sports';")
            total_sports = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM runs;")
            total_runs = cursor.fetchone()[0]

            cursor.execute("SELECT timestamp, status FROM runs ORDER BY id DESC LIMIT 1;")
            last_run = cursor.fetchone()

            return {
                "total_stored_articles": total_stored,
                "total_tech_articles": total_tech,
                "total_sports_articles": total_sports,
                "total_watchdog_runs": total_runs,
                "last_run_time": last_run[0] if last_run else "Never",
                "last_run_status": last_run[1] if last_run else "N/A",
            }

    def get_recent_news(self, category: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Returns the most recent news items, optionally filtered by category."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute(
                    "SELECT * FROM news WHERE category = ? ORDER BY id DESC LIMIT ?;",
                    (category, limit),
                )
            else:
                cursor.execute("SELECT * FROM news ORDER BY id DESC LIMIT ?;", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
