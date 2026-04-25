#!/usr/bin/env python3
from database import get_conn

conn = get_conn()
cursor = conn.cursor()

# Check if language column exists and feeds with Arabic language
print('Feeds table columns:')
cursor.execute("PRAGMA table_info(feeds)")
columns = cursor.fetchall()
for col in columns:
    print(f'  {col}')

print('\n\nFeeds with Arabic language:')
cursor.execute("SELECT id, topic, language, url FROM feeds WHERE language = 'Arabic' LIMIT 5")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f'  {dict(row)}')
else:
    print('  No Arabic feeds found')

print('\n\nTotal feeds by language:')
cursor.execute("SELECT language, COUNT(*) as count FROM feeds GROUP BY language")
rows = cursor.fetchall()
for row in rows:
    print(f'  {dict(row)}')

print('\n\nUsers and their language preferences:')
cursor.execute("SELECT id, username, language_preferences FROM users")
rows = cursor.fetchall()
for row in rows:
    print(f'  User {dict(row)["id"]} ({dict(row)["username"]}): {dict(row)["language_preferences"]}')

conn.close()
