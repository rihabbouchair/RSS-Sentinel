from fastapi import APIRouter, Query, Depends, Body
from typing import Optional, List
import json
from threading import Thread
from fastapi import Query
from pydantic import BaseModel

from database import get_conn
from auth import get_current_user
from pipeline import run_pipeline_for_user, run_pipeline_for_user_topic

class SubscribeFeedRequest(BaseModel):
    feed_id: int

router = APIRouter()


@router.get("/articles")
def get_articles(
    feed_topic: Optional[str] = None,
    sentiment: Optional[str] = None,
    limit: int = Query(20, le=100),
    show_read: bool = Query(False),
    current_user: dict = Depends(get_current_user)
):
    conn = get_conn()
    cursor = conn.cursor()
    
    # Get user's language preferences
    user_row = cursor.execute("SELECT language_preferences FROM users WHERE id = ?", (current_user["id"],)).fetchone()
    language_preferences = []
    if user_row and user_row[0]:
        try:
            language_preferences = json.loads(user_row[0])
        except:
            language_preferences = ["English"]
    else:
        language_preferences = ["English"]

    query = """
        SELECT a.*, f.topic AS feed_topic
        FROM articles a
        INNER JOIN feeds f ON a.feed_id = f.id
        WHERE f.user_id = ?
          AND a.fetched_at >= datetime('now', '-24 hours')
    """
    params = [current_user["id"]]

    if feed_topic:
        query += " AND f.topic = ?"
        params.append(feed_topic)

    if sentiment:
        query += " AND a.sentiment = ?"
        params.append(sentiment)
    
    # Hide read articles by default
    if not show_read:
        query += " AND a.is_read = 0"
    
    # Filter by language preferences
    if language_preferences:
        placeholders = ", ".join("?" * len(language_preferences))
        query += f" AND a.language IN ({placeholders})"
        params.extend(language_preferences)

    query += " ORDER BY a.fetched_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    articles = [dict(row) for row in cursor.fetchall()]
    conn.close()
    # If a topic was requested but no fresh articles exist, return a small fallback pool
    # and trigger an async topic refresh in background.
    if feed_topic and len(articles) == 0:
        # Fetch recent articles across the user's feeds as a fallback
        conn2 = get_conn()
        cursor2 = conn2.cursor()
        cursor2.execute("""
            SELECT a.*, f.topic AS feed_topic
            FROM articles a
            INNER JOIN feeds f ON a.feed_id = f.id
            WHERE f.user_id = ?
            ORDER BY a.fetched_at DESC
            LIMIT 5
        """, (current_user["id"],))
        fallback = [dict(row) for row in cursor2.fetchall()]
        conn2.close()

        # mark fallback articles so frontend can detect and trigger polling if desired
        for a in fallback:
            a["is_fallback"] = True

        # Trigger async topic refresh (non-blocking)
        def run_topic_async():
            from pipeline import prioritize_user_pipeline
            prioritize_user_pipeline(current_user["id"])
            run_pipeline_for_user_topic(current_user["id"], feed_topic)

        thread = Thread(target=run_topic_async, daemon=True)
        thread.start()

        return fallback

    return articles


@router.get("/articles/topics")
def get_topics(current_user: dict = Depends(get_current_user)):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT topic
        FROM feeds
        WHERE user_id = ?
        ORDER BY topic
    """, (current_user["id"],))
    topics = [row["topic"] for row in cursor.fetchall()]
    conn.close()
    return {"topics": topics}


@router.get("/articles/topic-counts")
def get_topic_counts(current_user: dict = Depends(get_current_user)):
    conn = get_conn()
    cursor = conn.cursor()

    user_row = cursor.execute(
        "SELECT language_preferences FROM users WHERE id = ?",
        (current_user["id"],),
    ).fetchone()
    language_preferences = []
    if user_row and user_row[0]:
        try:
            language_preferences = json.loads(user_row[0])
        except Exception:
            language_preferences = ["English"]
    else:
        language_preferences = ["English"]

    query = """
        SELECT f.topic, COUNT(a.id) AS count, SUM(CASE WHEN a.is_read = 0 THEN 1 ELSE 0 END) AS unread
        FROM feeds f
        LEFT JOIN articles a ON a.feed_id = f.id
           AND a.fetched_at >= datetime('now', '-24 hours')
    """

    params = []
    if language_preferences:
        placeholders = ", ".join("?" * len(language_preferences))
        query += f" AND a.language IN ({placeholders})"
        params.extend(language_preferences)

    query += """
        WHERE f.user_id = ?
        GROUP BY f.topic
        ORDER BY f.topic
    """
    params.append(current_user["id"])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    counts = {row["topic"]: {"total": row["count"], "unread": row["unread"] or 0} for row in rows}
    return {"counts": counts}


@router.post("/articles/refresh")
def refresh_articles(current_user: dict = Depends(get_current_user)):
    """Trigger immediate pipeline run for the current user (async in background)"""
    def run_pipeline_async():
        run_pipeline_for_user(current_user["id"])
    
    # Run pipeline in background thread to avoid blocking response
    thread = Thread(target=run_pipeline_async, daemon=True)
    thread.start()
    
    return {"status": "refreshing", "message": "Pipeline started for your articles. Check back in a few seconds."}


@router.post("/articles/refresh-topic")
def refresh_topic(topic: str = Query(...), current_user: dict = Depends(get_current_user)):
    """Trigger an immediate pipeline run only for feeds matching `topic` for the current user."""
    def run_topic_async():
        from pipeline import prioritize_user_pipeline
        prioritize_user_pipeline(current_user["id"])
        run_pipeline_for_user_topic(current_user["id"], topic)

    thread = Thread(target=run_topic_async, daemon=True)
    thread.start()

    return {"status": "refreshing", "message": f"Refreshing topic {topic} for your feeds."}


# ── Read/Unread Tracking ──────────────────────────────────────────────────────
@router.post("/articles/{article_id}/mark-read")
def mark_article_read(article_id: int, current_user: dict = Depends(get_current_user)):
    """Mark a single article as read."""
    conn = get_conn()
    try:
        # Verify article belongs to user
        article = conn.execute("""
            SELECT a.id FROM articles a
            INNER JOIN feeds f ON a.feed_id = f.id
            WHERE a.id = ? AND f.user_id = ?
        """, (article_id, current_user["id"])).fetchone()
        
        if not article:
            conn.close()
            return {"error": "Article not found"}, 404
        
        from datetime import datetime
        conn.execute(
            "UPDATE articles SET is_read = 1, read_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), article_id)
        )
        conn.commit()
    finally:
        conn.close()
    
    return {"status": "ok", "message": "Article marked as read"}


@router.post("/articles/{article_id}/mark-unread")
def mark_article_unread(article_id: int, current_user: dict = Depends(get_current_user)):
    """Mark a single article as unread."""
    conn = get_conn()
    try:
        # Verify article belongs to user
        article = conn.execute("""
            SELECT a.id FROM articles a
            INNER JOIN feeds f ON a.feed_id = f.id
            WHERE a.id = ? AND f.user_id = ?
        """, (article_id, current_user["id"])) .fetchone()

        if not article:
            conn.close()
            return {"error": "Article not found"}, 404

        conn.execute(
            "UPDATE articles SET is_read = 0, read_at = NULL WHERE id = ?",
            (article_id,)
        )
        conn.commit()
    finally:
        conn.close()

    return {"status": "ok", "message": "Article marked as unread"}


@router.post("/articles/mark-all-read")
def mark_all_articles_read(topic: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Mark all articles as read, optionally for a specific topic."""
    conn = get_conn()
    try:
        from datetime import datetime
        now = datetime.utcnow().isoformat()
        
        if topic:
            conn.execute("""
                UPDATE articles SET is_read = 1, read_at = ?
                WHERE feed_id IN (SELECT id FROM feeds WHERE user_id = ? AND topic = ?)
            """, (now, current_user["id"], topic))
        else:
            conn.execute("""
                UPDATE articles SET is_read = 1, read_at = ?
                WHERE feed_id IN (SELECT id FROM feeds WHERE user_id = ?)
            """, (now, current_user["id"]))
        
        conn.commit()
        count = conn.total_changes
    finally:
        conn.close()
    
    return {"status": "ok", "marked": count, "message": f"Marked {count} articles as read"}


@router.get("/articles/unread-counts")
def get_unread_counts(current_user: dict = Depends(get_current_user)):
    """Get unread article counts per topic."""
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT f.topic, COUNT(a.id) AS unread_count
            FROM feeds f
            LEFT JOIN articles a ON a.feed_id = f.id
                AND a.is_read = 0
                AND a.fetched_at >= datetime('now', '-24 hours')
            WHERE f.user_id = ?
            GROUP BY f.topic
            ORDER BY f.topic
        """, (current_user["id"],)).fetchall()
        
        counts = {row["topic"]: row["unread_count"] for row in rows}
    finally:
        conn.close()
    
    return {"unread_counts": counts}


# ── Feed Discovery & Recommendations ───────────────────────────────────────────
@router.get("/feeds/discover")
def discover_feeds(
    topic: Optional[str] = None,
    topics: Optional[List[str]] = Query(None),
    limit: int = Query(10, le=50),
):
    """Browse recommended and popular feeds, optionally filtered by one or more topics."""
    conn = get_conn()
    try:
        query = """
            SELECT id, url, topic, language, is_recommended
            FROM feeds
            WHERE user_id = 0
        """
        params = []

        selected_topics = []
        if topics:
            selected_topics.extend([t for t in topics if t])
        if topic:
            selected_topics.append(topic)

        # preserve order while removing duplicates
        selected_topics = list(dict.fromkeys(selected_topics))

        if selected_topics:
            placeholders = ", ".join("?" * len(selected_topics))
            query += f" AND topic IN ({placeholders})"
            params.extend(selected_topics)
        
        query += " ORDER BY is_recommended DESC LIMIT ?"
        params.append(limit)
        
        rows = conn.execute(query, params).fetchall()
        feeds = [dict(row) for row in rows]
    finally:
        conn.close()
    
    return {"feeds": feeds}


@router.get("/feeds/discover/topics")
def discover_feed_topics():
    """Get list of all available topics in the feed discovery catalog."""
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT DISTINCT topic FROM feeds WHERE user_id = 0 ORDER BY topic
        """).fetchall()
        topics = [row["topic"] for row in rows]
    finally:
        conn.close()
    
    return {"topics": topics}


@router.post("/feeds/subscribe")
def subscribe_to_feed(request: SubscribeFeedRequest, current_user: dict = Depends(get_current_user)):
    """Subscribe to a discovered feed (add it to user's feeds)."""
    feed_id = request.feed_id
    conn = get_conn()
    try:
        # Get the original feed
        original_feed = conn.execute(
            "SELECT url, topic, language FROM feeds WHERE id = ? AND user_id = 0",
            (feed_id,)
        ).fetchone()
        
        if not original_feed:
            conn.close()
            return {"error": "Feed not found"}, 404
        
        # Check if user already subscribed
        existing = conn.execute(
            "SELECT id FROM feeds WHERE user_id = ? AND url = ?",
            (current_user["id"], original_feed["url"])
        ).fetchone()
        
        if existing:
            conn.close()
            return {"error": "Already subscribed to this feed"}, 400
        
        # Create user's copy of the feed
        conn.execute(
            "INSERT INTO feeds (user_id, url, topic, language) VALUES (?, ?, ?, ?)",
            (current_user["id"], original_feed["url"], original_feed["topic"], original_feed["language"])
        )
        
        conn.commit()
    finally:
        conn.close()
    
    return {"status": "ok", "message": "Successfully subscribed to feed"}
