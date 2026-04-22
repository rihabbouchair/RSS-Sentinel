import feedparser
import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup
from database import get_conn
from email_service import send_digest
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
ARTICLES_PER_FEED = 5

def clean_html(html_text: str) -> str:
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def extract_first_three_sentences(text: str) -> str:
    if not text:
        return ""
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    return '. '.join(sentences[:3]) + '.'

def analyze_with_ollama(title: str, first_three_sentences: str) -> dict:
    prompt = (
        f"You are a news classifier. Analyze this article and respond ONLY with a valid JSON object.\n\n"
        f"Title: {title}\n"
        f"Text: {first_three_sentences}\n\n"
        f"Return JSON with exactly two keys:\n"
        f"1. 'sentiment': must be exactly 'Positive', 'Negative', or 'Neutral'\n"
        f"2. 'confidence_score': a float between 0 and 1 representing your certainty.\n"
        f"3. 'topic': a specific 2-4 word label describing what this article is about.\n"
        f"   - Be specific: 'Algerian Football', 'Gaza War', 'Stock Market Crash', 'Cancer Research', 'French Elections'\n"
        f"   - If article is in Arabic or French, still write the topic label in English\n"
        f"   - Never use vague labels like 'News', 'General', 'Other', 'World News'\n"
        f"   - For sports: always mention the specific sport or team, e.g. 'NBA Basketball', 'Algerian Football'\n"
        f"   - For politics: mention the country or region, e.g. 'US Politics', 'Middle East Conflict'\n\n"
        f"Example: {{\"sentiment\": \"Positive\", \"topic\": \"Algerian Football\"}}"
    )
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "gemma3:4b",
                "prompt": prompt,
                "stream": False,
                "format": "json"
            },
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        response_text = result.get("response", "")
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        if start_idx != -1 and end_idx > start_idx:
            return json.loads(response_text[start_idx:end_idx])
        raise ValueError("No JSON found")
    except Exception as e:
        print(f"Ollama analysis failed: {e}")
        return {"sentiment": "Neutral", "confidence_score": 0.5, "topic": "General News"}

def map_to_category(llm_topic: str, user_topics: list) -> str:
    """Map LLM free topic to user's selected broad category"""
    t = llm_topic.lower().strip()

    topic_keywords = {
        "AI":       ["ai", "artificial intelligence", "machine learning", "neural", "llm", "chatgpt", "openai", "robot", "automation", "deep learning", "generative ai"],
        "Tech":     ["tech", "software", "hardware", "cyber", "digital", "computer", "internet", "app", "semiconductor", "smartphone", "gadget"],
        "Politics": ["politic", "government", "election", "president", "minister", "law", "policy", "vote", "diplomacy", "war", "conflict", "military", "senate", "congress", "parliament"],
        "Sport":    ["sport", "football", "basketball", "tennis", "soccer", "olympic", "athlete", "championship", "league", "match", "tournament", "player", "coach", "club", "team", "fifa", "uefa", "nba", "nfl", "formula", "racing", "algerian football", "كرة", "رياضة"],
        "Economy":  ["economy", "economic", "market", "stock", "finance", "trade", "gdp", "inflation", "bank", "investment", "oil", "price", "budget", "currency", "business", "company", "earnings"],
        "Science":  ["science", "research", "space", "nasa", "biology", "physics", "chemistry", "discovery", "experiment", "astronomy"],
        "Health":   ["health", "disease", "hospital", "medicine", "treatment", "epidemic", "virus", "cancer", "vaccine", "medical", "doctor"],
        "Culture":  ["culture", "art", "cinema", "music", "film", "religion", "social", "literature", "festival", "entertainment"],
        "Environment": ["environment", "climate", "global warming", "pollution", "renewable", "energy", "ecology"],
    }

    # Direct match first (e.g. LLM returns "Sport" exactly)
    for user_topic in user_topics:
        if t == user_topic.lower():
            return user_topic

    # Keyword match
    for user_topic in user_topics:
        keywords = topic_keywords.get(user_topic, [user_topic.lower()])
        if any(kw in t for kw in keywords):
            return user_topic

    # Default to first user topic
    return user_topics[0] if user_topics else "General"

def cleanup_old_articles(user_id: int):
    conn = get_conn()
    conn.execute("""
        DELETE FROM articles
        WHERE feed_id IN (SELECT id FROM feeds WHERE user_id = ?)
        AND fetched_at < datetime('now', '-24 hours')
    """, (user_id,))
    conn.commit()
    deleted = conn.execute("SELECT changes()").fetchone()[0]
    conn.close()
    print(f"  Cleaned up {deleted} old articles for user {user_id}")

def get_feed_article_count(feed_id: int) -> int:
    conn = get_conn()
    count = conn.execute(
        "SELECT COUNT(*) FROM articles WHERE feed_id = ?", (feed_id,)
    ).fetchone()[0]
    conn.close()
    return count

def process_feed(feed: dict, user_topics: list) -> int:
    feed_id = feed["id"]
    feed_url = feed["url"]
    feed_topic = feed["topic"]
    added = 0

    print(f"\nProcessing feed: {feed_topic} ({feed_url})")
    try:
        existing_count = get_feed_article_count(feed_id)
        slots_available = ARTICLES_PER_FEED - existing_count
        if slots_available <= 0:
            print(f"  Feed already has {existing_count} articles, skipping.")
            return 0

        parsed = feedparser.parse(feed_url)
        entries = parsed.get("entries", [])
        print(f"  Found {len(entries)} entries, slots available: {slots_available}")

        for entry in entries:
            if added >= slots_available:
                break
            try:
                title = entry.get("title", "Untitled")
                url = entry.get("link", "")
                if not url:
                    continue

                conn_check = get_conn()
                existing = conn_check.execute(
                    "SELECT id FROM articles WHERE url = ?", (url,)
                ).fetchone()
                conn_check.close()
                if existing:
                    continue

                content = entry.get("summary", entry.get("description", ""))
                if "content" in entry and entry["content"]:
                    content = entry["content"][0].get("value", content)

                cleaned_text = clean_html(content) or title
                first_three = extract_first_three_sentences(cleaned_text)
                published_at = entry.get("published", entry.get("updated", ""))

                print(f"    Analyzing: {title[:50]}...")
                analysis = analyze_with_ollama(title, first_three)

                specific_topic = analysis.get("topic", "General News")
                confidence = analysis.get("confidence_score", 0.0)
                category = map_to_category(specific_topic, user_topics)

                conn_insert = get_conn()
                try:
                    conn_insert.execute("""
                        INSERT OR IGNORE INTO articles
                        (feed_id, title, url, summary, sentiment, topic, category, published_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        feed_id, title, url, first_three,
                        analysis.get("sentiment", "Neutral"),
                        confidence,
                        specific_topic,
                        category,
                        published_at
                    ))
                    conn_insert.commit()
                    added += 1
                    print(f"    ✓ Added [{category} > {specific_topic}]: {title[:40]}...")
                finally:
                    conn_insert.close()

            except Exception as e:
                print(f"    ✗ Failed article: {e}")
                continue

        conn_upd = get_conn()
        conn_upd.execute(
            "UPDATE feeds SET last_fetched_at = ? WHERE id = ?",
            (datetime.now().isoformat(), feed_id)
        )
        conn_upd.commit()
        conn_upd.close()

    except Exception as e:
        print(f"  ✗ Failed feed: {e}")

    return added

def run_pipeline_for_user(user_id: int):
    print(f"\n=== Pipeline started for user {user_id} at {datetime.now()} ===")

    conn = get_conn()
    user_row = conn.execute("SELECT topics FROM users WHERE id = ?", (user_id,)).fetchone()
    user_topics = json.loads(user_row["topics"]) if user_row else []
    feeds = [dict(f) for f in conn.execute(
        "SELECT * FROM feeds WHERE user_id = ?", (user_id,)
    ).fetchall()]
    conn.close()

    if not feeds:
        print(f"  No feeds found for user {user_id}, skipping.")
        return

    print(f"Found {len(feeds)} feeds, topics: {user_topics}")
    cleanup_old_articles(user_id)

    articles_added = 0
    with ThreadPoolExecutor(max_workers=max(1, len(feeds))) as executor:
        futures = [executor.submit(process_feed, feed, user_topics) for feed in feeds]
        for future in as_completed(futures):
            articles_added += future.result()

    print(f"\n=== Pipeline complete for user {user_id}: {articles_added} new articles ===")

    conn_email = get_conn()
    user = conn_email.execute(
        "SELECT email, wants_email_digest FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if user and user["wants_email_digest"] == 1 and user["email"]:
        articles_for_digest = [dict(r) for r in conn_email.execute("""
            SELECT title, url, summary, sentiment, confidence_score,topic, category, published_at
            FROM articles
            WHERE feed_id IN (SELECT id FROM feeds WHERE user_id = ?)
            ORDER BY fetched_at DESC LIMIT 20
        """, (user_id,)).fetchall()]
        conn_email.close()
        if articles_for_digest:
            send_digest(user["email"], articles_for_digest)
    else:
        conn_email.close()

def run_pipeline():
    print(f"\n=== Global pipeline started at {datetime.now()} ===")
    conn = get_conn()
    users = [dict(u) for u in conn.execute("SELECT id FROM users").fetchall()]
    conn.close()
    print(f"Found {len(users)} users to process")
    for user in users:
        run_pipeline_for_user(user["id"])
    print(f"=== Global pipeline complete at {datetime.now()} ===\n")