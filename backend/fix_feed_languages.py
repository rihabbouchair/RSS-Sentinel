#!/usr/bin/env python3
from database import get_conn

conn = get_conn()
cursor = conn.cursor()

print("Fixing feed language labels...\n")

# Map URL patterns to correct language
def get_language_for_url(url):
    """Infer language from feed URL"""
    if 'bbci.co.uk/arabic' in url or 'echorouk.dz' in url or 'ennaharonline.com' in url or 'alarabiya.net' in url:
        return 'Arabic'
    elif 'hl=fr' in url or 'tsa-algerie.com' in url:
        return 'French'
    else:
        return 'English'

# Get all feeds and fix their language
cursor.execute("SELECT id, url FROM feeds")
feeds = cursor.fetchall()

updates = {'English': 0, 'Arabic': 0, 'French': 0}

for feed in feeds:
    feed_id = feed['id']
    url = feed['url']
    correct_language = get_language_for_url(url)
    
    cursor.execute("UPDATE feeds SET language = ? WHERE id = ?", (correct_language, feed_id))
    updates[correct_language] += 1

conn.commit()

print(f"Fixed feed language labels:")
print(f"  English: {updates['English']} feeds")
print(f"  Arabic: {updates['Arabic']} feeds")
print(f"  French: {updates['French']} feeds")

print("\nFeeds for user 3 after fix:")
cursor.execute("SELECT id, topic, language, url FROM feeds WHERE user_id = 3 ORDER BY topic, language LIMIT 20")
rows = cursor.fetchall()
for row in rows:
    r = dict(row)
    print(f"  {r['topic']:12} {r['language']:8} {r['url'][:50]}")

# Show article counts by language
print("\n\nArticles by language for user 3:")
cursor.execute("""
    SELECT a.language, COUNT(*) as count
    FROM articles a
    INNER JOIN feeds f ON a.feed_id = f.id
    WHERE f.user_id = 3
    GROUP BY a.language
""")
rows = cursor.fetchall()
for row in rows:
    print(f"  {dict(row)}")

conn.close()
