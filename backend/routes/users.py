from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from database import get_conn
from feed_registry import get_feed_urls
from auth import get_current_user
from pipeline import run_pipeline_for_user
from email_service import (
    generate_verification_code,
    hash_verification_code,
    send_verification_code,
)
import json

router = APIRouter()


class PreferencesRequest(BaseModel):
    topics: List[str]
    email: Optional[str] = None
    wants_email_digest: bool = False


class VerifyEmailCodeRequest(BaseModel):
    code: str


@router.put("/users/preferences")
def update_preferences(
    request: PreferencesRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    conn = get_conn()
    cursor = conn.cursor()

    try:
        topics_json = json.dumps(request.topics)
        normalized_email = request.email.strip().lower() if request.email else None

        current_user_row = cursor.execute("""
            SELECT email, pending_email, email_verified
            FROM users
            WHERE id = ?
        """, (current_user["id"],)).fetchone()

        if not current_user_row:
            raise HTTPException(status_code=404, detail="User not found")

        verified_email = current_user_row["email"]
        existing_pending_email = current_user_row["pending_email"]
        email_verified = bool(current_user_row["email_verified"])

        email_verification_sent = False
        message = "preferences updated"

        if normalized_email:
            conflict = cursor.execute("""
                SELECT id FROM users
                WHERE id != ? AND (email = ? OR pending_email = ?)
            """, (current_user["id"], normalized_email, normalized_email)).fetchone()

            if conflict:
                raise HTTPException(status_code=400, detail="Email already in use")

            same_as_verified = email_verified and verified_email == normalized_email
            same_as_pending = existing_pending_email == normalized_email

            if not same_as_verified:
                if not same_as_pending:
                    code = generate_verification_code()
                    code_hash = hash_verification_code(code)
                    expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
                    email_verification_sent = send_verification_code(normalized_email, code)

                    cursor.execute("""
                        UPDATE users
                        SET topics = ?,
                            pending_email = ?,
                            email_verified = 0,
                            email_verification_code_hash = ?,
                            email_verification_expires_at = ?,
                            wants_email_digest = ?
                        WHERE id = ?
                    """, (
                        topics_json,
                        normalized_email,
                        code_hash,
                        expires_at,
                        1 if request.wants_email_digest else 0,
                        current_user["id"]
                    ))
                    message = "preferences updated, verification code sent"
                else:
                    cursor.execute("""
                        UPDATE users
                        SET topics = ?, wants_email_digest = ?
                        WHERE id = ?
                    """, (
                        topics_json,
                        1 if request.wants_email_digest else 0,
                        current_user["id"]
                    ))
            else:
                cursor.execute("""
                    UPDATE users
                    SET topics = ?, wants_email_digest = ?
                    WHERE id = ?
                """, (
                    topics_json,
                    1 if request.wants_email_digest else 0,
                    current_user["id"]
                ))
        else:
            cursor.execute("""
                UPDATE users
                SET topics = ?,
                    email = NULL,
                    pending_email = NULL,
                    email_verified = 0,
                    email_verification_code_hash = NULL,
                    email_verification_expires_at = NULL,
                    wants_email_digest = ?
                WHERE id = ?
            """, (
                topics_json,
                1 if request.wants_email_digest else 0,
                current_user["id"]
            ))

        cursor.execute("SELECT url FROM feeds WHERE user_id = ?", (current_user["id"],))
        existing_urls = {row["url"] for row in cursor.fetchall()}

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

        background_tasks.add_task(run_pipeline_for_user, current_user["id"])

        return {
            "message": message,
            "feeds_created": feeds_created,
            "email_verification_sent": email_verification_sent,
        }

    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/email/request-verification")
def request_email_verification(current_user: dict = Depends(get_current_user)):
    conn = get_conn()
    cursor = conn.cursor()

    try:
        user = cursor.execute("""
            SELECT pending_email FROM users WHERE id = ?
        """, (current_user["id"],)).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user["pending_email"]:
            raise HTTPException(status_code=400, detail="No pending email to verify")

        code = generate_verification_code()
        code_hash = hash_verification_code(code)
        expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()

        sent = send_verification_code(user["pending_email"], code)

        cursor.execute("""
            UPDATE users
            SET email_verification_code_hash = ?,
                email_verification_expires_at = ?
            WHERE id = ?
        """, (code_hash, expires_at, current_user["id"]))

        conn.commit()
        conn.close()

        return {
            "message": "verification code sent" if sent else "verification email could not be sent",
            "email_verification_sent": sent,
        }

    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/email/verify")
def verify_email_code(
    request: VerifyEmailCodeRequest,
    current_user: dict = Depends(get_current_user)
):
    conn = get_conn()
    cursor = conn.cursor()

    try:
        user = cursor.execute("""
            SELECT email, pending_email, email_verification_code_hash, email_verification_expires_at
            FROM users
            WHERE id = ?
        """, (current_user["id"],)).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user["pending_email"]:
            raise HTTPException(status_code=400, detail="No pending email to verify")

        if not user["email_verification_code_hash"] or not user["email_verification_expires_at"]:
            raise HTTPException(status_code=400, detail="No active verification code")

        expires_at = datetime.fromisoformat(user["email_verification_expires_at"])
        if datetime.utcnow() > expires_at:
            raise HTTPException(status_code=400, detail="Verification code expired")

        submitted_hash = hash_verification_code(request.code.strip())
        if submitted_hash != user["email_verification_code_hash"]:
            raise HTTPException(status_code=400, detail="Invalid verification code")

        cursor.execute("""
            UPDATE users
            SET email = pending_email,
                pending_email = NULL,
                email_verified = 1,
                email_verification_code_hash = NULL,
                email_verification_expires_at = NULL
            WHERE id = ?
        """, (current_user["id"],))

        conn.commit()

        updated_user = cursor.execute("""
            SELECT id, username, email, pending_email, topics, wants_email_digest, email_verified
            FROM users
            WHERE id = ?
        """, (current_user["id"],)).fetchone()

        conn.close()

        return {
            "message": "email verified successfully",
            "user": {
                "id": updated_user["id"],
                "username": updated_user["username"],
                "email": updated_user["email"],
                "pending_email": updated_user["pending_email"],
                "topics": json.loads(updated_user["topics"]),
                "wants_email_digest": bool(updated_user["wants_email_digest"]),
                "email_verified": bool(updated_user["email_verified"]),
            }
        }

    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
