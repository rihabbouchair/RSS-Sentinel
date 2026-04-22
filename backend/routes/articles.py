from fastapi import APIRouter, Query, Depends
from typing import Optional
from database import get_conn
from auth import get_current_user

router = APIRouter()

@router.get("/articles")
def get_articles(
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
    limit: int = Query(20, le=100),
    current_user: dict = Depends(get_current_user)
):
    conn = get_conn()
    cursor = conn.cursor()

    query = """
        SELECT a.* FROM articles a
        INNER JOIN feeds f ON a.feed_id = f.id
        WHERE f.user_id = ?
    """
    params = [current_user["id"]]

    if category:
        query += " AND a.category = ?"
        params.append(category)

    if sentiment:
        query += " AND a.sentiment = ?"
        params.append(sentiment)

    query += " ORDER BY a.fetched_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    articles = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return articles

@router.get("/articles/topics")
def get_topics(current_user: dict = Depends(get_current_user)):
    """Get distinct categories (user's broad topics) for sidebar"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT a.category FROM articles a
        INNER JOIN feeds f ON a.feed_id = f.id
        WHERE f.user_id = ? AND a.category IS NOT NULL
        ORDER BY a.category
    """, (current_user["id"],))
    topics = [row["category"] for row in cursor.fetchall()]
    conn.close()
    return {"topics": topics}