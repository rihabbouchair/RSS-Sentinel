from fastapi import APIRouter, Query, Depends
from typing import Optional
import json
from threading import Thread

from database import get_conn
from auth import get_current_user
from pipeline import run_pipeline_for_user

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


@router.post("/articles/refresh")
def refresh_articles(current_user: dict = Depends(get_current_user)):
    """Trigger immediate pipeline run for the current user (async in background)"""
    def run_pipeline_async():
        run_pipeline_for_user(current_user["id"])
    
    # Run pipeline in background thread to avoid blocking response
    thread = Thread(target=run_pipeline_async, daemon=True)
    thread.start()
    
    return {"status": "refreshing", "message": "Pipeline started for your articles. Check back in a few seconds."}
