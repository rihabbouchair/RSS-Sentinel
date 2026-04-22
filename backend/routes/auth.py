from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional
from database import get_conn
from auth import hash_password, verify_password, create_access_token, get_current_user
from feed_registry import get_feed_urls
from pipeline import run_pipeline_for_user
import json

router = APIRouter()

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    topics: List[str]
    wants_email_digest: bool = False

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/auth/register")
def register(request: RegisterRequest, background_tasks: BackgroundTasks):
    """Register a new user and create feeds for their topics"""
    conn = get_conn()
    cursor = conn.cursor()

    try:
        password_hash = hash_password(request.password)
        topics_json = json.dumps(request.topics)

        cursor.execute("""
            INSERT INTO users (username, email, password_hash, topics, wants_email_digest)
            VALUES (?, ?, ?, ?, ?)
        """, (
            request.username,
            request.email,
            password_hash,
            topics_json,
            1 if request.wants_email_digest else 0
        ))

        user_id = cursor.lastrowid

        for topic in request.topics:
            feed_urls = get_feed_urls(topic)
            for feed_url in feed_urls:
                cursor.execute("""
                    INSERT INTO feeds (user_id, url, topic)
                    VALUES (?, ?, ?)
                """, (user_id, feed_url, topic))

        conn.commit()

        cursor.execute("""
            SELECT id, username, email, topics, wants_email_digest
            FROM users WHERE id = ?
        """, (user_id,))
        user = dict(cursor.fetchone())
        conn.close()

        background_tasks.add_task(run_pipeline_for_user, user_id)

        token = create_access_token(user_id)

        return {
            "token": token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "topics": json.loads(user["topics"]),
                "wants_email_digest": bool(user["wants_email_digest"])
            }
        }

    except Exception as e:
        conn.close()
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="Username or email already exists")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auth/login")
def login(request: LoginRequest):
    """Login user and return JWT token"""
    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, username, email, password_hash, topics, wants_email_digest
            FROM users WHERE username = ?
        """, (request.username,))

        user = cursor.fetchone()
        conn.close()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not verify_password(request.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token(user["id"])

        return {
            "token": token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "topics": json.loads(user["topics"]),
                "wants_email_digest": bool(user["wants_email_digest"])
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info from token"""
    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, username, email, topics, wants_email_digest
            FROM users WHERE id = ?
        """, (current_user["id"],))

        user = cursor.fetchone()
        conn.close()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "topics": json.loads(user["topics"]),
            "wants_email_digest": bool(user["wants_email_digest"])
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))