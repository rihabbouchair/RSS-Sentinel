#!/usr/bin/env python3
"""Prewarm the database with analyzed articles for popular topics.

Usage:
  python scripts/prewarm_demo.py --user-id 0 --per-language 2 --delay 1.0

Notes:
- This script will create feeds for the user if they don't exist.
- Analysis uses `pipeline.analyze_with_ollama` which requires Ollama running on localhost:11434.
"""
import argparse
import time
from datetime import datetime
import os
import sys
import json

# Add parent directory to path so we can import backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_conn
from pipeline import build_article_candidate, analyze_with_ollama
from feed_registry import get_feed_urls
import feedparser


POPULAR_TOPICS = [
    'AI', 'Tech', 'Politics', 'Sport', 'Economy', 'Science',
    'Health',
    
    'Education',
]


def ensure_feed(conn, user_id: int, url: str, topic: str, language: str):
    cur = conn.cursor()
    row = cur.execute("SELECT id FROM feeds WHERE user_id = ? AND url = ?", (user_id, url)).fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO feeds (user_id, url, topic, language, last_fetched_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, url, topic, language, None))
    conn.commit()
    return cur.lastrowid


def insert_article(conn, feed_id: int, candidate: dict, analysis: dict):
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT OR IGNORE INTO articles
            (feed_id, title, url, summary, sentiment, confidence_score, topic, language, inference_log, published_at, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            feed_id,
            candidate["title"],
            candidate["url"],
            candidate["excerpt"],
            analysis.get("sentiment"),
            analysis.get("confidence_score"),
            analysis.get("topic"),
            candidate.get("language", "English"),
            analysis.get("inference_log") if isinstance(analysis.get("inference_log"), str) else None,
            candidate.get("published_at"),
            datetime.utcnow().isoformat(),
        ))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        print("Failed inserting article:", e)
        return False


def prewarm_user(user_id: int, per_language: int = 2, delay: float = 1.0, languages=None):
    if languages is None:
        languages = ["English", "French", "Arabic"]

    conn = get_conn()
    added_counts = {}

    for topic in POPULAR_TOPICS:
        print(f"\nPrewarming topic: {topic}")
        for lang in languages:
            added = 0
            urls = [u for u, l in get_feed_urls(topic, languages=[lang]) if l == lang]
            if not urls:
                print(f"  No feed urls for {topic} / {lang}")
                continue

            for feed_url in urls:
                if added >= per_language:
                    break
                feed_id = ensure_feed(conn, user_id, feed_url, topic, lang)
                parsed = feedparser.parse(feed_url)
                entries = parsed.get("entries", [])
                for entry in entries:
                    if added >= per_language:
                        break
                    candidate = build_article_candidate(entry, topic)
                    if not candidate:
                        continue
                    # Force language tag when feed is language-specific
                    candidate["language"] = lang
                    print(f"    Analyzing candidate: {candidate['title'][:80]}")
                    try:
                        analysis = analyze_with_ollama(candidate)
                    except Exception as e:
                        print("      Analysis failed:", e)
                        continue

                    success = insert_article(conn, feed_id, candidate, analysis)
                    if success:
                        added += 1
                        print(f"      Inserted ({added}/{per_language}) for {lang}")
                    else:
                        print("      Skipped (duplicate or insert failed)")

                    time.sleep(delay)

            added_counts[f"{topic}:{lang}"] = added

    conn.close()
    print("\nPrewarm complete. Summary:")
    for k, v in added_counts.items():
        print(f"  {k} -> {v}")


def distribute_seed_articles_to_all_users():
    """Copy seed articles from user_id=0 to all existing users for their subscribed topics."""
    from pipeline import copy_seed_articles_to_user
    
    conn = get_conn()
    existing_users = conn.execute("SELECT id, topics FROM users WHERE id != 0").fetchall()
    conn.close()
    
    if not existing_users:
        print("\nNo existing users to distribute seed articles to.")
        return
    
    print(f"\nDistributing seed articles to {len(existing_users)} existing users...")
    for user in existing_users:
        user_id = user["id"]
        try:
            topics = json.loads(user["topics"]) if user["topics"] else []
        except:
            topics = []
        
        if topics:
            print(f"  User {user_id}: copying articles for topics {topics}")
            copy_seed_articles_to_user(user_id, topics)
        else:
            print(f"  User {user_id}: no topics subscribed, skipping")
    
    print("Distribution complete.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, default=0, help="Target user id to seed feeds/articles for (default: 0 = seed user)")
    parser.add_argument("--per-language", type=int, default=2, help="Articles per language per topic")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds to wait between analysis calls")
    args = parser.parse_args()

    print("Starting prewarm — USER_ID=", args.user_id)
    prewarm_user(args.user_id, per_language=args.per_language, delay=args.delay)
    
    # If seeding the seed user, distribute articles to all existing users
    if args.user_id == 0:
        distribute_seed_articles_to_all_users()


if __name__ == '__main__':
    main()
