from fastapi import APIRouter, Depends
from database import get_conn
from auth import get_current_user

router = APIRouter()

@router.get("/feeds")
def get_feeds(current_user: dict = Depends(get_current_user)):
    """Get feeds for current user"""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT f.*, u.email as user_email
        FROM feeds f
        LEFT JOIN users u ON f.user_id = u.id
        WHERE f.user_id = ?
        ORDER BY f.id DESC
    """, (current_user["id"],))

    feeds = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return feeds
