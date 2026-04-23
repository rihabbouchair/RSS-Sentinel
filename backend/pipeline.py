import feedparser
import json
import os
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from database import get_conn
from email_service import send_digest

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "45"))

ARTICLES_PER_FEED = int(os.getenv("ARTICLES_PER_FEED", "5"))
TARGET_READY_ARTICLES_PER_TOPIC = int(os.getenv("TARGET_READY_ARTICLES_PER_TOPIC", "5"))
MAX_ARTICLES_PER_TOPIC = int(os.getenv("MAX_ARTICLES_PER_TOPIC", "10"))
MAX_ANALYSIS_CHARS = int(os.getenv("MAX_ANALYSIS_CHARS", "1400"))


def clean_html(html_text: str) -> str:
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def extract_analysis_excerpt(text: str, max_sentences: int = 4) -> str:
    if not text:
        return ""

    normalized = " ".join(text.split())
    sentences = re.split(r"(?<=[.!?؟])\s+", normalized)
    excerpt = " ".join(sentence.strip() for sentence in sentences[:max_sentences] if sentence.strip())

    if not excerpt:
        excerpt = normalized

    return excerpt[:MAX_ANALYSIS_CHARS].strip()


def detect_language(text: str) -> str:
    if re.search(r"[\u0600-\u06FF]", text):
        return "Arabic"
    if re.search(r"[éèàùâêîôûçëïüœ]", text.lower()):
        return "French"
    return "English"


def infer_sentiment_fallback(title: str, excerpt: str) -> str:
    text = f"{title} {excerpt}".lower()

    negative_keywords = [
        "war", "attack", "killed", "death", "dead", "injured", "crash", "accident",
        "fraud", "theft", "lawsuit", "accuses", "accused", "conflict", "drop",
        "decline", "fall", "loss", "layoff", "layoffs", "risk", "crisis", "scandal",
        "strike", "sanction", "warning", "earthquake", "flood", "fire",
        "وفاة", "مقتل", "قتلى", "إصابة", "انقلاب", "حرب", "أزمة", "فضيحة", "تحذير",
    ]
    positive_keywords = [
        "win", "won", "success", "successful", "growth", "record", "launch", "breakthrough",
        "approved", "approval", "improve", "improved", "recovery", "recover", "partnership",
        "raises", "expands", "expansion", "award", "profit", "profits", "surge",
        "فوز", "نجاح", "نمو", "إطلاق", "ارتفاع", "تحسن", "تعاف", "إنجاز",
    ]

    if any(word in text for word in negative_keywords):
        return "Negative"
    if any(word in text for word in positive_keywords):
        return "Positive"
    return "Neutral"


def infer_topic_fallback(title: str) -> str:
    cleaned = re.sub(r"[^\w\s\-]", " ", title, flags=re.UNICODE)
    words = [word for word in cleaned.split() if len(word.strip()) > 2][:4]
    return " ".join(words) if words else "Untitled Topic"


def normalize_evidence_keywords(raw_keywords, candidate: dict) -> list[str]:
    if isinstance(raw_keywords, list):
        keywords = [str(item).strip() for item in raw_keywords if str(item).strip()]
    else:
        keywords = []

    if not keywords:
        combined = f"{candidate['title']} {candidate['excerpt']}"
        tokens = re.findall(r"[\w\u0600-\u06FF\-]{4,}", combined, flags=re.UNICODE)
        seen = set()
        fallback = []
        for token in tokens:
            lower = token.lower()
            if lower in seen:
                continue
            seen.add(lower)
            fallback.append(token)
            if len(fallback) >= 8:
                break
        keywords = fallback

    deduped = []
    seen = set()
    for keyword in keywords:
        cleaned = re.sub(r"\s+", " ", keyword).strip()[:32]
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped.append(cleaned)
        if len(deduped) >= 8:
            break

    return deduped


def build_article_candidate(entry: dict, broad_topic: str) -> dict | None:
    title = entry.get("title", "Untitled")
    url = entry.get("link", "")
    if not url:
        return None

    content = entry.get("summary", entry.get("description", ""))
    if "content" in entry and entry["content"]:
        content = entry["content"][0].get("value", content)

    cleaned_text = clean_html(content) or title
    excerpt = extract_analysis_excerpt(cleaned_text)
    published_at = entry.get("published", entry.get("updated", ""))
    source_host = urlparse(url).netloc or "unknown"

    return {
        "title": title,
        "url": url,
        "excerpt": excerpt,
        "published_at": published_at,
        "broad_topic": broad_topic,
        "source_host": source_host,
        "language": detect_language(f"{title} {excerpt}"),
    }


def normalize_analysis(raw_analysis: dict, candidate: dict, fallback_used: bool) -> dict:
    sentiment = str(raw_analysis.get("sentiment", "")).strip().capitalize()
    if sentiment not in {"Positive", "Negative", "Neutral"}:
        sentiment = infer_sentiment_fallback(candidate["title"], candidate["excerpt"])

    try:
        confidence_score = float(raw_analysis.get("confidence_score", 0.5))
    except (TypeError, ValueError):
        confidence_score = 0.5
    confidence_score = max(0.0, min(1.0, confidence_score))

    topic = str(raw_analysis.get("topic", "")).strip()
    if not topic or topic.lower() in {"general", "general news", "news", "other"}:
        topic = infer_topic_fallback(candidate["title"])

    reasoning_summary = str(raw_analysis.get("reasoning_summary", "")).strip()
    if not reasoning_summary:
        reasoning_summary = f"Topic inferred from the article title and excerpt in {candidate['language']}."

    evidence_keywords = normalize_evidence_keywords(raw_analysis.get("evidence_keywords"), candidate)

    inference_log = {
        "model": OLLAMA_MODEL,
        "timestamp_utc": datetime.utcnow().isoformat(),
        "broad_topic": candidate["broad_topic"],
        "language": candidate["language"],
        "source_host": candidate["source_host"],
        "title": candidate["title"],
        "excerpt": candidate["excerpt"],
        "sentiment": sentiment,
        "topic": topic,
        "confidence_score": confidence_score,
        "reasoning_summary": reasoning_summary,
        "evidence_keywords": evidence_keywords,
        "fallback_used": fallback_used,
    }

    return {
        "sentiment": sentiment,
        "confidence_score": confidence_score,
        "topic": topic,
        "inference_log": json.dumps(inference_log, ensure_ascii=False),
    }


def analyze_with_ollama(candidate: dict) -> dict:
    prompt = (
        "You are an expert multilingual news analyst.\n"
        "The article may be in English, French, or Arabic.\n"
        "Understand the text semantically, then classify the specific real-world topic and sentiment.\n"
        "Do not force the result to match the user's selected broad topic.\n"
        "Return the topic and reasoning summary in English even if the article is Arabic or French.\n\n"
        "Sentiment rules:\n"
        "- Positive: progress, wins, launches, approvals, breakthroughs, growth, recovery.\n"
        "- Negative: war, conflict, accusations, crashes, deaths, injuries, layoffs, risks, losses.\n"
        "- Neutral: purely factual reporting with no clearly positive or negative development.\n"
        "- Avoid overusing Neutral if the event clearly has positive or negative impact.\n\n"
        "Topic rules:\n"
        "- Return a concise specific topic label of 2 to 5 words.\n"
        "- Good examples: 'US Tariff Policy', 'Tesla Earnings', 'Champions League', 'Breast Cancer Research'.\n"
        "- Never return vague topics like 'General News', 'Other', or 'News'.\n\n"
        "Evidence rules:\n"
        "- Provide 3 to 8 short evidence keywords found in the title/text that justify the topic/sentiment.\n"
        "- Keep keywords concise and verbatim where possible.\n\n"
        "Return ONLY valid JSON with exactly these keys:\n"
        "{\"sentiment\":\"Positive|Negative|Neutral\",\"confidence_score\":0.0,\"topic\":\"Specific Topic\",\"reasoning_summary\":\"Short explanation in under 20 words\",\"evidence_keywords\":[\"keyword1\",\"keyword2\"]}\n\n"
        f"User broad topic: {candidate['broad_topic']}\n"
        f"Detected article language: {candidate['language']}\n"
        f"Title: {candidate['title']}\n"
        f"Text: {candidate['excerpt']}\n"
    )

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                },
            },
            timeout=OLLAMA_TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
        response_text = result.get("response", "")
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1

        if start_idx != -1 and end_idx > start_idx:
            parsed = json.loads(response_text[start_idx:end_idx])
            return normalize_analysis(parsed, candidate, fallback_used=False)

        raise ValueError("No JSON found in Ollama response")
    except Exception as e:
        print(f"Ollama analysis failed: {e}")
        fallback = {
            "sentiment": infer_sentiment_fallback(candidate["title"], candidate["excerpt"]),
            "confidence_score": 0.35,
            "topic": infer_topic_fallback(candidate["title"]),
            "reasoning_summary": "Fallback heuristics used because the model request failed.",
            "evidence_keywords": normalize_evidence_keywords(None, candidate),
        }
        return normalize_analysis(fallback, candidate, fallback_used=True)


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


def get_topic_article_count(user_id: int, broad_topic: str, language: str = None) -> int:
    """Count articles for a topic, optionally filtered by language"""
    conn = get_conn()
    try:
        if language:
            return conn.execute("""
                SELECT COUNT(*)
                FROM articles
                WHERE feed_id IN (
                    SELECT id FROM feeds WHERE user_id = ? AND topic = ? AND language = ?
                )
            """, (user_id, broad_topic, language)).fetchone()[0]
        else:
            return conn.execute("""
                SELECT COUNT(*)
                FROM articles
                WHERE feed_id IN (
                    SELECT id FROM feeds WHERE user_id = ? AND topic = ?
                )
            """, (user_id, broad_topic)).fetchone()[0]
    finally:
        conn.close()


def get_existing_urls(urls: list[str]) -> set[str]:
    if not urls:
        return set()
    conn = get_conn()
    try:
        placeholders = ",".join("?" for _ in urls)
        rows = conn.execute(
            f"SELECT url FROM articles WHERE url IN ({placeholders})",
            urls,
        ).fetchall()
        return {row["url"] for row in rows}
    finally:
        conn.close()


def process_feed(feed: dict, user_id: int) -> int:
    feed_id = feed["id"]
    feed_url = feed["url"]
    broad_topic = feed["topic"]
    feed_language = feed.get("language", "English")
    added = 0

    print(f"\nProcessing feed: {broad_topic} ({feed_language}) ({feed_url})")

    try:
        # Count articles for this topic in this specific language
        language_topic_count = get_topic_article_count(user_id, broad_topic, feed_language)
        if language_topic_count >= MAX_ARTICLES_PER_TOPIC:
            print(f"  Topic '{broad_topic}' ({feed_language}) already reached the cap of {MAX_ARTICLES_PER_TOPIC}, skipping.")
            return 0

        desired_new_articles = min(
            ARTICLES_PER_FEED,
            TARGET_READY_ARTICLES_PER_TOPIC - language_topic_count if language_topic_count < TARGET_READY_ARTICLES_PER_TOPIC else 0,
            MAX_ARTICLES_PER_TOPIC - language_topic_count,
        )

        if desired_new_articles <= 0:
            print(f"  Topic '{broad_topic}' ({feed_language}) already has at least {TARGET_READY_ARTICLES_PER_TOPIC} ready articles.")
            return 0

        parsed = feedparser.parse(feed_url)
        entries = parsed.get("entries", [])
        print(f"  Found {len(entries)} entries, need {desired_new_articles} more articles")

        candidates = []
        for entry in entries:
            candidate = build_article_candidate(entry, broad_topic)
            if candidate:
                candidates.append(candidate)

        if not candidates:
            print("  No valid entries found.")
            return 0

        existing_urls = get_existing_urls([candidate["url"] for candidate in candidates])
        fresh_candidates = [candidate for candidate in candidates if candidate["url"] not in existing_urls]
        fresh_candidates = fresh_candidates[:desired_new_articles]

        for candidate in fresh_candidates:
            try:
                print(f"    Analyzing: {candidate['title'][:60]}...")
                analysis = analyze_with_ollama(candidate)

                conn_insert = get_conn()
                try:
                    conn_insert.execute("""
                        INSERT OR IGNORE INTO articles
                        (feed_id, title, url, summary, sentiment, confidence_score, topic, language, inference_log, published_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        feed_id,
                        candidate["title"],
                        candidate["url"],
                        candidate["excerpt"],
                        analysis["sentiment"],
                        analysis["confidence_score"],
                        analysis["topic"],
                        candidate["language"],
                        analysis["inference_log"],
                        candidate["published_at"],
                    ))
                    conn_insert.commit()

                    if conn_insert.total_changes > 0:
                        added += 1
                        print(
                            f"    Added [{broad_topic} > {analysis['topic']}] "
                            f"({analysis['sentiment']}, {analysis['confidence_score']:.2f})"
                        )
                finally:
                    conn_insert.close()
            except Exception as e:
                print(f"    Failed article: {e}")
                continue

        conn_upd = get_conn()
        conn_upd.execute(
            "UPDATE feeds SET last_fetched_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), feed_id),
        )
        conn_upd.commit()
        conn_upd.close()
    except Exception as e:
        print(f"  Failed feed: {e}")

    return added


def run_pipeline_for_user(user_id: int):
    print(f"\n=== Pipeline started for user {user_id} at {datetime.utcnow()} UTC ===")

    conn = get_conn()
    feeds = [dict(feed) for feed in conn.execute(
        "SELECT * FROM feeds WHERE user_id = ? ORDER BY topic, id",
        (user_id,),
    ).fetchall()]
    conn.close()

    if not feeds:
        print(f"  No feeds found for user {user_id}, skipping.")
        return

    cleanup_old_articles(user_id)

    articles_added = 0
    for feed in feeds:
        articles_added += process_feed(feed, user_id)

    print(f"\n=== Pipeline complete for user {user_id}: {articles_added} new articles ===")


def run_pipeline():
    print(f"\n=== Global pipeline started at {datetime.utcnow()} UTC ===")
    conn = get_conn()
    users = [dict(user) for user in conn.execute("SELECT id FROM users").fetchall()]
    conn.close()

    print(f"Found {len(users)} users to process")
    for user in users:
        run_pipeline_for_user(user["id"])

    print(f"=== Global pipeline complete at {datetime.utcnow()} UTC ===\n")


def send_daily_digest_for_user(user_id: int):
    conn = get_conn()
    user = conn.execute("""
        SELECT id, email, wants_email_digest, email_verified, last_digest_sent_at
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if not user:
        conn.close()
        return

    if not user["email"] or user["wants_email_digest"] != 1 or user["email_verified"] != 1:
        conn.close()
        return

    today_utc = datetime.utcnow().date()
    if user["last_digest_sent_at"]:
        try:
            last_sent_date = datetime.fromisoformat(user["last_digest_sent_at"]).date()
            if last_sent_date == today_utc:
                conn.close()
                print(f"Digest already sent today for user {user_id}")
                return
        except Exception:
            pass

    since_24h = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    articles_for_digest = [dict(row) for row in conn.execute("""
        SELECT a.title, a.url, a.summary, a.sentiment, a.confidence_score, a.topic, f.topic AS feed_topic, a.published_at
        FROM articles a
        INNER JOIN feeds f ON a.feed_id = f.id
        WHERE f.user_id = ?
          AND a.fetched_at >= ?
        ORDER BY a.fetched_at DESC
        LIMIT 20
    """, (user_id, since_24h)).fetchall()]

    if not articles_for_digest:
        conn.close()
        print(f"No fresh articles for user {user_id}, skipping digest")
        return

    sent = send_digest(user["email"], articles_for_digest)
    if sent:
        conn.execute("""
            UPDATE users
            SET last_digest_sent_at = ?
            WHERE id = ?
        """, (datetime.utcnow().isoformat(), user_id))
        conn.commit()
        print(f"Daily digest sent for user {user_id}")

    conn.close()


def send_daily_digests():
    print(f"\n=== Daily digest job started at {datetime.utcnow()} UTC ===")
    conn = get_conn()
    users = [dict(user) for user in conn.execute("""
        SELECT id
        FROM users
        WHERE wants_email_digest = 1
          AND email_verified = 1
          AND email IS NOT NULL
    """).fetchall()]
    conn.close()

    print(f"Found {len(users)} users eligible for daily digest")
    for user in users:
        send_daily_digest_for_user(user["id"])

    print(f"=== Daily digest job complete at {datetime.utcnow()} UTC ===\n")
