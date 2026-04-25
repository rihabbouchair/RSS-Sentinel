#!/usr/bin/env python3
from database import get_conn
import json

conn = get_conn()
cursor = conn.cursor()

# Get user 3 (the one with Arabic selected)
cursor.execute("SELECT id, language_preferences FROM users WHERE id = 3")
user = cursor.fetchone()
if user:
    user_id = user["id"]
    lang_prefs = json.loads(user["language_preferences"])
    print(f"User {user_id} language preferences: {lang_prefs}")
    
    # Delete old Arabic feeds
    print("\nDeleting old Arabic feeds...")
    cursor.execute("DELETE FROM feeds WHERE user_id = ? AND language = 'Arabic'", (user_id,))
    deleted_feeds = cursor.rowcount
    print(f"Deleted {deleted_feeds} old Arabic feeds")
    
    # Delete articles from those deleted feeds
    print("Deleting articles from deleted feeds...")
    cursor.execute("""
        DELETE FROM articles 
        WHERE feed_id IN (
            SELECT id FROM feeds WHERE user_id = ?
        )
    """, (user_id,))
    deleted_articles = cursor.rowcount
    print(f"Deleted {deleted_articles} articles")
    
    conn.commit()

# Show remaining feeds
print("\nRemaining feeds for user 3:")
cursor.execute("SELECT id, topic, language, url FROM feeds WHERE user_id = 3 LIMIT 10")
rows = cursor.fetchall()
for row in rows:
    print(f"  {dict(row)}")

conn.close()
print("\n*** User needs to save preferences again to create new Arabic feeds ***")
