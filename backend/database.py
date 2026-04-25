import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "sentinel.db"


def get_conn():
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def init_db():
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            pending_email TEXT,
            password_hash TEXT NOT NULL,
            topics TEXT DEFAULT '[]',
            language_preferences TEXT DEFAULT '["English"]',
            wants_email_digest INTEGER DEFAULT 0,
            email_verified INTEGER DEFAULT 0,
            email_verification_code_hash TEXT,
            email_verification_expires_at TEXT,
            last_digest_sent_at TEXT,
            articles_per_topic INTEGER DEFAULT 3,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            url TEXT,
            topic TEXT,
            language TEXT DEFAULT 'English',
            last_fetched_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    try:
        cursor.execute("ALTER TABLE feeds ADD COLUMN language TEXT DEFAULT 'English'")
    except Exception:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feed_id INTEGER,
            title TEXT,
            url TEXT UNIQUE,
            summary TEXT,
            sentiment TEXT,
            confidence_score REAL,
            topic TEXT,
            language TEXT DEFAULT 'English',
            inference_log TEXT,
            published_at TEXT,
            fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (feed_id) REFERENCES feeds(id)
        )
    """)

    try:
        cursor.execute("ALTER TABLE articles ADD COLUMN confidence_score REAL")
    except Exception:
        pass

    try:
        cursor.execute("ALTER TABLE articles ADD COLUMN inference_log TEXT")
    except Exception:
        pass

    try:
        cursor.execute("ALTER TABLE articles ADD COLUMN language TEXT DEFAULT 'English'")
    except Exception:
        pass


    try:
        cursor.execute("ALTER TABLE users ADD COLUMN language_preferences TEXT DEFAULT '[\"English\"]'")
    except Exception:
        pass

    # Add missing columns for existing databases first
    columns_to_add = [
        ("pending_email", "TEXT"),
        ("email_verified", "INTEGER DEFAULT 0"),
        ("email_verification_code_hash", "TEXT"),
        ("email_verification_expires_at", "TEXT"),
        ("last_digest_sent_at", "TEXT"),
        ("wants_email_digest", "INTEGER DEFAULT 0"),
        ("articles_per_topic", "INTEGER DEFAULT 3"),
    ]

    for column_name, column_def in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}")
        except Exception:
            pass

    # Create index only after pending_email definitely exists
    try:
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_pending_email_unique
            ON users(pending_email)
            WHERE pending_email IS NOT NULL
        """)
    except Exception:
        pass

    conn.commit()
    conn.close()
    print("Database initialized successfully")
