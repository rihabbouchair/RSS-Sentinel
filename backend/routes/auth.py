from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from database import get_conn
from auth import hash_password, verify_password, create_access_token, get_current_user
from feed_registry import get_feed_urls
from pipeline import run_pipeline_for_user
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
    email: Optional[str] = None
    topics: List[str]
    wants_email_digest: bool = False
    language_preferences: Optional[List[str]] = None


class LoginRequest(BaseModel):
    username: str
    password: str


def serialize_user(user_row):
    topics = json.loads(user_row["topics"]) if user_row["topics"] else []
    
    # Handle language_preferences safely - might be NULL in database
    lang_prefs = None
    try:
        lang_prefs = user_row["language_preferences"]
    except (KeyError, TypeError, IndexError):
        lang_prefs = None
    
    try:
        language_preferences = json.loads(lang_prefs) if lang_prefs else ["English"]
    except (TypeError, ValueError):
        language_preferences = ["English"]
    
    return {
        "id": user_row["id"],
        "username": user_row["username"],
        "email": user_row["email"],
        "pending_email": user_row["pending_email"],
        "topics": topics,
        "language_preferences": language_preferences,
        "wants_email_digest": bool(user_row["wants_email_digest"]),
        "email_verified": bool(user_row["email_verified"]),
    }


@router.post("/auth/register")
def register(request: RegisterRequest, background_tasks: BackgroundTasks):
    conn = get_conn()
    cursor = conn.cursor()

    try:
        normalized_email = request.email.strip().lower() if request.email else None

        if normalized_email:
            existing_email = cursor.execute("""
                SELECT id FROM users
                WHERE email = ? OR pending_email = ?
            """, (normalized_email, normalized_email)).fetchone()
            if existing_email:
                raise HTTPException(status_code=400, detail="Email already exists")

        password_hash = hash_password(request.password)
        topics_json = json.dumps(request.topics)
        language_preferences = request.language_preferences or ["English"]
        language_preferences_json = json.dumps(language_preferences)

        email_verified = 0
        pending_email = None
        verification_code_hash = None
        verification_expires_at = None
        verification_sent = False

        if normalized_email:
            code = generate_verification_code()
            pending_email = normalized_email
            verification_code_hash = hash_verification_code(code)
            verification_expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
            verification_sent = send_verification_code(normalized_email, code)

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
            pending_email,
            password_hash,
            topics_json,
            language_preferences_json,
            1 if request.wants_email_digest else 0,
            email_verified,
            verification_code_hash,
            verification_expires_at,
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

        cursor.execute("""
            SELECT id, username, email, pending_email, topics, language_preferences, wants_email_digest, email_verified
            FROM users
            WHERE id = ?
        """, (user_id,))
        user = cursor.fetchone()
        conn.close()

        background_tasks.add_task(run_pipeline_for_user, user_id)
        token = create_access_token(user_id)

        return {
            "token": token,
            "user": serialize_user(user),
            "email_verification_sent": verification_sent,
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
            SELECT id, username, email, pending_email, password_hash, topics, language_preferences, wants_email_digest, email_verified
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
            SELECT id, username, email, pending_email, topics, language_preferences, wants_email_digest, email_verified
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
