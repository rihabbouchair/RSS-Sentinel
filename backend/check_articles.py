#!/usr/bin/env python3
from database import get_conn

conn = get_conn()
cursor = conn.cursor()

print('Total articles in database:')
cursor.execute('SELECT COUNT(*) as count FROM articles')
print(f"  {cursor.fetchone()['count']}")

print('\nArticles by language:')
cursor.execute('SELECT language, COUNT(*) as count FROM articles GROUP BY language')
for row in cursor.fetchall():
    print(f"  {dict(row)}")

print('\nSample articles:')
cursor.execute('SELECT id, title, language FROM articles LIMIT 5')
for row in cursor.fetchall():
    r = dict(row)
    print(f"  {r['id']}: {r['title'][:60]} ({r['language']})")

conn.close()
