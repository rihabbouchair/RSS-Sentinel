from fastapi import APIRouter, Query, Depends
from typing import Optional
import json
from threading import Thread
from fastapi import Query

from database import get_conn
from auth import get_current_user
from pipeline import run_pipeline_for_user, run_pipeline_for_user_topic

router = APIRouter()


@router.get("/articles")
def get_articles(
    feed_topic: Optional[str] = None,
    sentiment: Optional[str] = None,
    limit: int = Query(20, le=100),
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
        SELECT f.topic, COUNT(a.id) AS count
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

    counts = {row["topic"]: row["count"] for row in rows}
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
        run_pipeline_for_user_topic(current_user["id"], topic)

    thread = Thread(target=run_topic_async, daemon=True)
    thread.start()

    return {"status": "refreshing", "message": f"Refreshing topic {topic} for your feeds."}
