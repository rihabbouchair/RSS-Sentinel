#!/usr/bin/env python3
"""
Final cleanup: Guide user to refresh Arabic feeds
"""
from database import get_conn
import json

conn = get_conn()
cursor = conn.cursor()

print("=" * 70)
print("ARABIC FEEDS FIX SUMMARY")
print("=" * 70)

print("\n✓ FIXES COMPLETED:")
print("  1. Removed non-working Al Jazeera RSS feeds")
print("  2. Added Alarabiya.net as Arabic news source")
print("  3. Fixed feed language labels (BBC/Ennahar now correctly marked as Arabic)")
print("  4. Fixed feed language labels (TSA now correctly marked as French)")

print("\n" + "=" * 70)
print("WHAT YOU NEED TO DO NOW:")
print("=" * 70)

# Get user with Arabic
cursor.execute("SELECT id, username, language_preferences FROM users WHERE language_preferences LIKE '%Arabic%'")
users_with_arabic = cursor.fetchall()

if users_with_arabic:
    print(f"\nFound {len(users_with_arabic)} user(s) with Arabic selected:")
    for user in users_with_arabic:
        user_id = user['id']
        username = user['username']
        print(f"\n  USER: {username} (ID: {user_id})")
        
        # Count current feeds
        cursor.execute("SELECT COUNT(*) as count FROM feeds WHERE user_id = ?", (user_id,))
        feed_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT language, COUNT(*) as count FROM feeds WHERE user_id = ? GROUP BY language", (user_id,))
        langs = cursor.fetchall()
        
        print(f"    Current feeds: {feed_count} total")
        for lang_row in langs:
            print(f"      - {lang_row['language']}: {lang_row['count']} feeds")
        
        print(f"\n    ACTION: Go to Subscribe page and SAVE PREFERENCES")
        print(f"            (This will create feeds with correct new Arabic sources)")

print("\n" + "=" * 70)
print("ARABIC SOURCES NOW AVAILABLE:")
print("=" * 70)
print("\n  Primary Arabic sources:")
print("    • BBC Arabic (English-language coverage of Arabic topics)")
print("    • Ennahar Online (Algeria - Arabic content)")
print("    • Echourouk (Algeria - Arabic content)")  
print("    • Alarabiya.net (New - International Arabic news)")

print("\n" + "=" * 70)

conn.close()
