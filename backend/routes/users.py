from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from database import get_conn
from feed_registry import get_feed_urls
from auth import get_current_user
from pipeline import run_pipeline_for_user
import json

router = APIRouter()

class PreferencesRequest(BaseModel):
    topics: List[str]
    email: Optional[str] = None
    wants_email_digest: bool = False

@router.put("/users/preferences")
def update_preferences(request: PreferencesRequest, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Update user preferences and rebuild feeds"""
    conn = get_conn()
    cursor = conn.cursor()

    try:
        topics_json = json.dumps(request.topics)

        # Update user preferences
        cursor.execute("""
            UPDATE users
            SET topics = ?, email = ?, wants_email_digest = ?
            WHERE id = ?
        """, (
            topics_json,
            request.email,
            1 if request.wants_email_digest else 0,
            current_user["id"]
        ))

        # Get existing feed URLs to avoid duplicates
        cursor.execute("SELECT url FROM feeds WHERE user_id = ?", (current_user["id"],))
        existing_urls = {row["url"] for row in cursor.fetchall()}

        # Only insert feeds for NEW topics, don't delete existing ones
        feeds_created = 0
        for topic in request.topics:
            feed_urls = get_feed_urls(topic)
            for feed_url in feed_urls:
                if feed_url not in existing_urls:
                    cursor.execute("""
                        INSERT INTO feeds (user_id, url, topic)
                        VALUES (?, ?, ?)
                    """, (current_user["id"], feed_url, topic))
                    feeds_created += 1

        conn.commit()
        conn.close()

        # Trigger pipeline for this user in background
        background_tasks.add_task(run_pipeline_for_user, current_user["id"])

        return {
            "message": "preferences updated",
            "feeds_created": feeds_created
        }

    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))