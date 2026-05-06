from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from database import get_conn
from auth import hash_password, verify_password, create_access_token, get_current_user
from feed_registry import get_feed_urls
from pipeline import run_pipeline_for_user, prioritize_user_pipeline, set_logged_in_user, copy_seed_articles_to_user
from email_service import (
    generate_verification_code,
    hash_verification_code,
    send_verification_code,
)
import json

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    password: str
    topics: List[str]
    wants_email_digest: bool = False
    language_preferences: Optional[List[str]] = None


class LoginRequest(BaseModel):
    username: str
    password: str


def serialize_user(user_row):
    topics = json.loads(user_row["topics"]) if user_row["topics"] else []
    
    # Handle language_preferences safely
    lang_prefs = None
    try:
        lang_prefs = user_row["language_preferences"]
    except (KeyError, TypeError, IndexError):
        lang_prefs = None
    
    try:
        language_preferences = json.loads(lang_prefs) if lang_prefs else ["English"]
    except (TypeError, ValueError):
        language_preferences = ["English"]
    
    articles_per_topic = None
    try:
        articles_per_topic = user_row["articles_per_topic"]
    except (KeyError, TypeError):
        articles_per_topic = None
    
    return {
        "id": user_row["id"],
        "username": user_row["username"],
        "email": user_row["email"],
        "pending_email": user_row["pending_email"],
        "topics": topics,
        "language_preferences": language_preferences,
        "wants_email_digest": bool(user_row["wants_email_digest"]),
        "email_verified": bool(user_row["email_verified"]),
        "articles_per_topic": articles_per_topic or 3,
    }


@router.post("/auth/register")
def register(request: RegisterRequest, background_tasks: BackgroundTasks):
    conn = get_conn()
    cursor = conn.cursor()

    try:
        password_hash = hash_password(request.password)
        topics_json = json.dumps(request.topics)
        language_preferences = request.language_preferences or ["English"]
        language_preferences_json = json.dumps(language_preferences)

        cursor.execute("""
            INSERT INTO users (
                username,
                email,
                pending_email,
                password_hash,
                topics,
                language_preferences,
                wants_email_digest,
                email_verified,
                email_verification_code_hash,
                email_verification_expires_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.username,
            None,
            None,
            password_hash,
            topics_json,
            language_preferences_json,
            0,
            0,
            None,
            None,
        ))

        user_id = cursor.lastrowid

        for topic in request.topics:
            feed_urls_with_langs = get_feed_urls(topic, language_preferences)
            for feed_url, language in feed_urls_with_langs:
                cursor.execute("""
                    INSERT INTO feeds (user_id, url, topic, language)
                    VALUES (?, ?, ?, ?)
                """, (user_id, feed_url, topic, language))

        conn.commit()
        
        # Copy pre-seeded articles to new user for instant display
        copy_seed_articles_to_user(user_id, request.topics)

        cursor.execute("""
            SELECT id, username, email, pending_email, topics, language_preferences, wants_email_digest, email_verified, articles_per_topic
            FROM users
            WHERE id = ?
        """, (user_id,))
        user = cursor.fetchone()
        conn.close()

        set_logged_in_user(user_id)
        prioritize_user_pipeline(user_id)
        background_tasks.add_task(run_pipeline_for_user, user_id)
        token = create_access_token(user_id)

        return {
            "token": token,
            "user": serialize_user(user),
        }

    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.close()
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="Username or email already exists")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auth/login")
def login(request: LoginRequest, background_tasks: BackgroundTasks):
    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, username, email, pending_email, password_hash, topics, language_preferences, wants_email_digest, email_verified, articles_per_topic
            FROM users
            WHERE username = ?
        """, (request.username,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not verify_password(request.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token(user["id"])
        set_logged_in_user(user["id"])
        prioritize_user_pipeline(user["id"])
        background_tasks.add_task(run_pipeline_for_user, user["id"])

        return {
            "token": token,
            "user": serialize_user(user),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, username, email, pending_email, topics, language_preferences, wants_email_digest, email_verified, articles_per_topic
            FROM users
            WHERE id = ?
        """, (current_user["id"],))
        user = cursor.fetchone()
        conn.close()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return serialize_user(user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
