import feedparser
import json
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
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
OLLAMA_RETRIES = int(os.getenv("OLLAMA_RETRIES", "1"))

ARTICLES_PER_FEED = int(os.getenv("ARTICLES_PER_FEED", "5"))
TARGET_READY_ARTICLES_PER_TOPIC = int(os.getenv("TARGET_READY_ARTICLES_PER_TOPIC", "5"))
MAX_ARTICLES_PER_TOPIC = int(os.getenv("MAX_ARTICLES_PER_TOPIC", "10"))
MAX_ANALYSIS_CHARS = int(os.getenv("MAX_ANALYSIS_CHARS", "1400"))
FEED_PIPELINE_WORKERS = int(os.getenv("FEED_PIPELINE_WORKERS", "2"))

VAGUE_TOPIC_LABELS = {
    "general",
    "general news",
    "news",
    "other",
    "update",
    "breaking",
    "latest",
    "story",
}

TOPIC_STOPWORDS = {
    "the", "a", "an", "and", "or", "for", "with", "from", "into", "about", "after", "before",
    "over", "under", "between", "amid", "amidst", "near", "new", "today", "live", "video",
    "this", "that", "these", "those", "its", "their", "his", "her", "our", "your",
    "les", "des", "une", "un", "et", "ou", "pour", "avec", "dans", "sur", "apres", "avant",
    "ce", "cet", "cette", "ces", "son", "sa", "ses", "leur", "leurs", "plus", "moins",
    "من", "الى", "إلى", "على", "في", "عن", "مع", "بعد", "قبل", "هذا", "هذه", "ذلك", "تلك",
    "هناك", "حول", "عند", "ضمن", "بين", "كانت", "كان", "يكون", "تكون", "أجل", "اليوم",
}


_pipeline_state_lock = threading.Lock()
_priority_user_ids: list[int] = []
_running_user_ids: set[int] = set()


def prioritize_user_pipeline(user_id: int):
    """Mark a user to be processed first in the next global pipeline pass."""
    with _pipeline_state_lock:
        if user_id in _priority_user_ids:
            _priority_user_ids.remove(user_id)
        _priority_user_ids.insert(0, user_id)


def _claim_user_pipeline_slot(user_id: int) -> bool:
    """Prevent concurrent duplicate runs for the same user."""
    with _pipeline_state_lock:
        if user_id in _running_user_ids:
            return False
        _running_user_ids.add(user_id)
        return True


def _release_user_pipeline_slot(user_id: int):
    with _pipeline_state_lock:
        _running_user_ids.discard(user_id)


def calculate_language_distribution(articles_per_topic: int, language_preferences: list) -> dict:
    """
    Calculate how many articles per language based on user preferences.
    English gets priority when distribution is uneven.
    
    Example:
    - 5 articles, [English, Arabic]: 3 English, 2 Arabic
    - 5 articles, [English, Arabic, French]: 2 English, 2 Arabic, 1 French
      (English gets priority for remainder)
    
    Returns: {"English": 3, "Arabic": 2, ...}
    """
    if not language_preferences:
        language_preferences = ["English"]
    
    # Start with base count for each language
    base_count = articles_per_topic // len(language_preferences)
    remainder = articles_per_topic % len(language_preferences)
    
    distribution = {}
    for i, lang in enumerate(language_preferences):
        distribution[lang] = base_count
    
    # Distribute remainder, with English getting priority
    for i in range(remainder):
        # Give extra articles to English first, then Arabic, then French
        if "English" in distribution:
            distribution["English"] += 1
        elif "Arabic" in distribution:
            distribution["Arabic"] += 1
        elif "French" in distribution:
            distribution["French"] += 1
        else:
            # Fallback: distribute to the first language
            distribution[language_preferences[i % len(language_preferences)]] += 1
    
    return distribution


def _get_global_user_order(default_user_ids: list[int]) -> list[int]:
    with _pipeline_state_lock:
        priority = [uid for uid in _priority_user_ids if uid in default_user_ids]
        _priority_user_ids.clear()

    if not priority:
        return default_user_ids

    seen = set(priority)
    remainder = [uid for uid in default_user_ids if uid not in seen]
    return priority + remainder


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


def derive_topic_from_title(title: str, max_words: int = 4) -> str:
    cleaned = re.sub(r"[^\w\s\-\u0600-\u06FF]", " ", title, flags=re.UNICODE)
    raw_tokens = [token.strip("-_") for token in cleaned.split() if token.strip("-_")]

    tokens = []
    for token in raw_tokens:
        lower = token.lower()
        if lower in TOPIC_STOPWORDS:
            continue
        if re.fullmatch(r"\d+", token):
            continue

        is_arabic = bool(re.search(r"[\u0600-\u06FF]", token))
        if not is_arabic and len(token) < 3:
            continue

        tokens.append(token)
        if len(tokens) >= max_words:
            break

    if not tokens:
        return ""

    return " ".join(tokens)


def normalize_topic_label(raw_topic: str, candidate: dict, confidence_score: float) -> str:
    topic = re.sub(r"\s+", " ", (raw_topic or "")).strip(" .,-")
    broad_topic = str(candidate.get("broad_topic", "")).strip()

    title_based_topic = derive_topic_from_title(candidate.get("title", ""))
    fallback_topic = infer_topic_fallback(
        candidate.get("title", ""),
        candidate.get("excerpt", ""),
        broad_topic,
    )

    if not topic:
        return fallback_topic

    topic_lower = topic.lower()
    broad_lower = broad_topic.lower()
    one_word_topic = len(topic.split()) <= 1

    if topic_lower in VAGUE_TOPIC_LABELS:
        return fallback_topic

    if one_word_topic and topic_lower in {
        "politics", "economy", "technology", "science", "health", "education", "sports",
        "tech", "sport", "business", "world", "climate", "crypto", "travel", "gaming", "ai",
    }:
        return title_based_topic or fallback_topic

    if broad_lower and topic_lower == broad_lower:
        return title_based_topic or fallback_topic

    if confidence_score < 0.40 and title_based_topic:
        return title_based_topic

    return topic


def infer_sentiment_fallback(title: str, excerpt: str) -> str:
    text = f"{title} {excerpt}".lower()

    # Weighted multilingual lexicon reduces overuse of Neutral when model fallback is used.
    negative_keywords = [
        "war", "attack", "killed", "death", "dead", "injured", "crash", "accident",
        "fraud", "theft", "lawsuit", "accuses", "accused", "conflict", "drop",
        "decline", "fall", "loss", "layoff", "layoffs", "risk", "crisis", "scandal",
        "strike", "sanction", "warning", "earthquake", "flood", "fire", "missile",
        "murder", "blast", "explosion", "fatal", "hostage", "raid", "arrest",
        "guerre", "attaque", "mort", "morts", "bless", "crise", "chute", "perte",
        "sanction", "alerte", "incendie", "inondation", "explosion", "conflit",
        "وفاة", "مقتل", "قتلى", "قتيل", "إصابة", "جرحى", "انقلاب", "حرب", "أزمة", "فضيحة",
        "تحذير", "قصف", "هجوم", "انفجار", "خسارة", "تراجع", "انخفاض", "توتر", "اشتباكات",
        "عقوبات", "اعتقال", "فساد", "إغلاق",
    ]
    positive_keywords = [
        "win", "won", "success", "successful", "growth", "record", "launch", "breakthrough",
        "approved", "approval", "improve", "improved", "recovery", "recover", "partnership",
        "raises", "expands", "expansion", "award", "profit", "profits", "surge", "deal",
        "agreement", "ceasefire", "stability", "boost", "innovation", "funding",
        "victory", "qualify", "qualified", "advance", "advanced", "comeback", "clean sheet",
        "victoire", "succes", "croissance", "record", "lancement", "accord", "reprise",
        "amelior", "hausse", "benefice", "partenariat", "innovation",
        "فوز", "نجاح", "نمو", "إطلاق", "ارتفاع", "تحسن", "تعاف", "إنجاز", "اتفاق",
        "هدنة", "استقرار", "تقدم", "افتتاح", "أرباح", "ربح", "انتعاش", "تمويل",
    ]

    mild_negative_cues = [
        "no plan", "rejected", "fails", "failure", "concern", "concerns", "tension", "uncertainty",
        "injury", "injured", "ban", "banned", "suspended", "suspension", "controversy", "criticized",
        "knocked out", "eliminated", "defeat", "lost", "loss",
    ]
    mild_positive_cues = [
        "beats", "beat", "tops", "title", "champion", "champions", "breaks record", "record high",
        "secures", "secure", "backed", "backing", "green light", "approved",
    ]

    positive_score = sum(1 for word in positive_keywords if word in text)
    negative_score = sum(1 for word in negative_keywords if word in text)
    positive_score += sum(1 for phrase in mild_positive_cues if phrase in text)
    negative_score += sum(1 for phrase in mild_negative_cues if phrase in text)

    score_delta = positive_score - negative_score
    if score_delta >= 1:
        return "Positive"
    if score_delta <= -1:
        return "Negative"

    # Tie-breaker: strong conflict/governance cues are usually not neutral in news context.
    if any(token in text for token in ["حرب", "قصف", "هجوم", "sanction", "war", "attack"]):
        return "Negative"

    return "Neutral"


def infer_topic_fallback(title: str, excerpt: str = "", broad_topic: str = "") -> str:
    text = f"{title} {excerpt}".lower()

    topic_keywords = {
        "Politics": [
            "politic", "election", "government", "minister", "parliament", "president", "diploma",
            "policy", "white house", "sanction", "trump", "biden", "iran", "gaza", "ukraine",
            "politique", "gouvernement", "ministre", "parlement", "president", "negociation", "diplom",
            "انتخابات", "حكومة", "وزير", "الرئيس", "برلمان", "مفاوضات", "دبلوماس", "سياس", "إيران", "غزة", "أوكرانيا",
        ],
        "Economy": [
            "econom", "inflation", "market", "stock", "gdp", "trade", "tariff", "oil", "bank", "crypto", "finance",
            "economie", "inflation", "marche", "bourse", "banque", "financ",
            "اقتصاد", "تضخم", "بورصة", "أسهم", "سوق", "نفط", "بنك", "دولار", "عملة", "استثمار", "تعرفة",
        ],
        "Technology": [
            "tech", "ai", "artificial intelligence", "software", "app", "chip", "startup", "google", "microsoft", "apple",
            "technologie", "numerique", "logiciel", "intelligence artificielle", "startup",
            "تقنية", "تكنولوجيا", "ذكاء اصطناعي", "الذكاء الاصطناعي", "برمج", "تطبيق", "شريحة", "روبوت", "هاتف",
        ],
        "Science": [
            "science", "research", "study", "experiment", "space", "nasa", "physics", "chemistry", "biology", "climate",
            "recherche", "etude", "espace", "climat",
            "علم", "بحث", "دراسة", "تجربة", "فضاء", "مناخ", "فيزياء", "كيمياء", "أحياء",
        ],
        "Health": [
            "health", "hospital", "vaccine", "disease", "virus", "medical", "doctor", "drug", "cancer", "who",
            "sante", "hopital", "vaccin", "maladie", "medecin", "cancer",
            "صحة", "مستشفى", "لقاح", "مرض", "فيروس", "طبي", "دواء", "سرطان", "طبيب",
        ],
        "Education": [
            "school", "student", "teacher", "university", "education", "curriculum", "exam", "campus", "classroom",
            "ecole", "etudiant", "enseignant", "universite", "education", "examen",
            "تعليم", "مدرسة", "طالب", "طلاب", "جامعة", "مناهج", "امتحان", "معلم", "وزارة التعليم",
        ],
        "Sports": [
            "sport", "match", "league", "cup", "goal", "team", "coach", "fifa", "uefa", "champions",
            "football", "basketball", "tennis",
            "sport", "match", "ligue", "coupe", "equipe", "entraineur", "but",
            "رياض", "مباراة", "الدوري", "كأس", "هدف", "فريق", "مدرب", "كرة", "بطولة",
        ],
    }

    best_topic = ""
    best_score = 0
    for topic_label, keywords in topic_keywords.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score = score
            best_topic = topic_label

    if best_topic and best_score > 0:
        return derive_topic_from_title(title) or best_topic

    if broad_topic:
        return broad_topic

    return derive_topic_from_title(title) or "Untitled Topic"


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

    topic = normalize_topic_label(
        str(raw_analysis.get("topic", "")).strip(),
        candidate,
        confidence_score,
    )

    reasoning_summary = str(raw_analysis.get("reasoning_summary", "")).strip()
    if not reasoning_summary:
        reasoning_summary = f"Topic inferred from the article title and excerpt in {candidate['language']}."

    sentiment_reason = str(raw_analysis.get("sentiment_reason", "")).strip()
    if not sentiment_reason:
        sentiment_reason = f"Sentiment inferred from article signals in {candidate['language']}."

    topic_reason = str(raw_analysis.get("topic_reason", "")).strip()
    if not topic_reason:
        topic_reason = "Topic inferred from dominant entities and keywords in title/excerpt."

    evidence_keywords = normalize_evidence_keywords(raw_analysis.get("evidence_keywords"), candidate)

    inference_log = {
        "model": OLLAMA_MODEL,
        "prompt_version": "v3_simple_multilingual",
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
        "sentiment_reason": sentiment_reason,
        "topic_reason": topic_reason,
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
        "You are a multilingual news classifier.\n"
        "Classify the article's sentiment and one specific topic from the meaning of the text.\n"
        "Keep it simple and fast. Do not overthink.\n"
        "Return all text fields in English.\n"
        "Use the main entity/event in the title as the topic anchor when possible.\n"
        "Use a concise topic label, not vague labels like General News, Other, or News.\n"
        "Give short reasons and a few evidence keywords.\n\n"
        "Return ONLY valid JSON with exactly these keys:\n"
        "{\"sentiment\":\"Positive|Negative|Neutral\",\"confidence_score\":0.0,\"topic\":\"Specific Topic\",\"reasoning_summary\":\"General classification summary under 25 words\",\"sentiment_reason\":\"Why sentiment is this label under 20 words\",\"topic_reason\":\"Why this topic label fits under 20 words\",\"evidence_keywords\":[\"keyword1\",\"keyword2\"]}\n\n"
        f"User broad topic: {candidate['broad_topic']}\n"
        f"Detected article language: {candidate['language']}\n"
        f"Title: {candidate['title']}\n"
        f"Text: {candidate['excerpt']}\n"
    )
    def build_fallback(reason: str) -> dict:
        fallback = {
            "sentiment": infer_sentiment_fallback(candidate["title"], candidate["excerpt"]),
            "confidence_score": 0.35,
            "topic": infer_topic_fallback(candidate["title"], candidate["excerpt"], candidate["broad_topic"]),
            "reasoning_summary": reason,
            "sentiment_reason": "Keyword scoring on multilingual article text indicates this sentiment.",
            "topic_reason": "Topic category matched by strongest multilingual keyword signals.",
            "evidence_keywords": normalize_evidence_keywords(None, candidate),
        }
        return normalize_analysis(fallback, candidate, fallback_used=True)

    last_error = None
    for attempt in range(1, OLLAMA_RETRIES + 2):
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
        except requests.exceptions.ReadTimeout as e:
            print(f"Ollama analysis timeout for article '{candidate['title'][:60]}...': {e}")
            return build_fallback("Fallback heuristics used because Ollama timed out.")
        except Exception as e:
            last_error = e
            print(f"Ollama analysis attempt {attempt} failed: {e}")

    if last_error:
        print(f"Ollama analysis failed after retries: {last_error}")
    return build_fallback("Fallback heuristics used because model analysis was unavailable.")


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


def process_feed(feed: dict, user_id: int, language_per_topic_target: int = None) -> int:
    feed_id = feed["id"]
    feed_url = feed["url"]
    broad_topic = feed["topic"]
    feed_language = feed.get("language", "English")
    added = 0
    
    # Use provided target or fall back to environment default
    target_articles = language_per_topic_target or TARGET_READY_ARTICLES_PER_TOPIC

    print(f"\nProcessing feed: {broad_topic} ({feed_language}) ({feed_url})")

    try:
        # Count articles for this topic in this specific language
        language_topic_count = get_topic_article_count(user_id, broad_topic, feed_language)
        if language_topic_count >= MAX_ARTICLES_PER_TOPIC:
            print(f"  Topic '{broad_topic}' ({feed_language}) already reached the cap of {MAX_ARTICLES_PER_TOPIC}, skipping.")
            return 0

        desired_new_articles = min(
            ARTICLES_PER_FEED,
            target_articles - language_topic_count if language_topic_count < target_articles else 0,
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
    if not _claim_user_pipeline_slot(user_id):
        print(f"\n=== Pipeline already running for user {user_id}, skipping duplicate trigger ===")
        return

    print(f"\n=== Pipeline started for user {user_id} at {datetime.utcnow()} UTC ===")

    try:
        conn = get_conn()
        
        # Get user preferences
        user_row = conn.execute(
            "SELECT articles_per_topic, language_preferences FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        
        if user_row:
            articles_per_topic = user_row["articles_per_topic"] or 3
            try:
                language_preferences = json.loads(user_row["language_preferences"] or "[\"English\"]")
            except (json.JSONDecodeError, TypeError):
                language_preferences = ["English"]
        else:
            articles_per_topic = 3
            language_preferences = ["English"]
        
        # Calculate per-language target
        language_distribution = calculate_language_distribution(articles_per_topic, language_preferences)
        print(f"  User {user_id} preference: {articles_per_topic} articles/topic, distributed as {language_distribution}")
        
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
        max_workers = max(1, min(FEED_PIPELINE_WORKERS, len(feeds), 4))

        if max_workers == 1:
            for feed in feeds:
                feed_language = feed.get("language", "English")
                target_for_feed = language_distribution.get(feed_language, articles_per_topic)
                articles_added += process_feed(feed, user_id, target_for_feed)
        else:
            print(f"  Processing {len(feeds)} feeds in parallel with {max_workers} workers")
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(
                        process_feed,
                        feed,
                        user_id,
                        language_distribution.get(feed.get("language", "English"), articles_per_topic)
                    )
                    for feed in feeds
                ]
                for future in as_completed(futures):
                    try:
                        articles_added += future.result()
                    except Exception as e:
                        print(f"  Feed worker failed: {e}")

        print(f"\n=== Pipeline complete for user {user_id}: {articles_added} new articles ===")
    finally:
        _release_user_pipeline_slot(user_id)


def run_pipeline_for_user_topic(user_id: int, topic: str):
    """Run the pipeline only for feeds that match the given topic for a user."""
    if not _claim_user_pipeline_slot(user_id):
        print(f"\n=== Topic pipeline already running for user {user_id}, skipping duplicate trigger ===")
        return

    print(f"\n=== Topic pipeline started for user {user_id}, topic '{topic}' at {datetime.utcnow()} UTC ===")
    try:
        conn = get_conn()
        feeds = [dict(feed) for feed in conn.execute(
            "SELECT * FROM feeds WHERE user_id = ? AND topic = ? ORDER BY id",
            (user_id, topic),
        ).fetchall()]
        conn.close()

        if not feeds:
            print(f"  No feeds found for user {user_id} with topic '{topic}', skipping.")
            return

        articles_added = 0
        max_workers = max(1, min(FEED_PIPELINE_WORKERS, len(feeds), 4))

        if max_workers == 1:
            for feed in feeds:
                articles_added += process_feed(feed, user_id)
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(process_feed, feed, user_id) for feed in feeds]
                for future in as_completed(futures):
                    try:
                        articles_added += future.result()
                    except Exception as e:
                        print(f"  Feed worker failed: {e}")

        print(f"\n=== Topic pipeline complete for user {user_id}, topic '{topic}': {articles_added} new articles ===")
    finally:
        _release_user_pipeline_slot(user_id)


def run_pipeline():
    print(f"\n=== Global pipeline started at {datetime.utcnow()} UTC ===")
    conn = get_conn()
    users = [dict(user) for user in conn.execute("SELECT id FROM users ORDER BY id").fetchall()]
    conn.close()

    default_user_ids = [user["id"] for user in users]
    ordered_user_ids = _get_global_user_order(default_user_ids)

    print(f"Found {len(ordered_user_ids)} users to process")
    if ordered_user_ids != default_user_ids:
        print(f"Prioritized global order: {ordered_user_ids}")

    for user_id in ordered_user_ids:
        run_pipeline_for_user(user_id)

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


def copy_seed_articles_to_user(user_id: int, topics: list = None):
    """Copy pre-seeded articles from seed user (user_id=0) to a new user.
    This allows new users to see instant articles for their selected topics.
    """
    if user_id == 0:
        return  # Don't copy to seed user itself
    
    conn = get_conn()
    try:
        # Get the new user's feeds
        if topics:
            placeholders = ",".join("?" * len(topics))
            user_feeds = conn.execute(f"""
                SELECT id, topic, language FROM feeds WHERE user_id = ? AND topic IN ({placeholders})
            """, [user_id] + topics).fetchall()
        else:
            user_feeds = conn.execute(
                "SELECT id, topic, language FROM feeds WHERE user_id = ?",
                (user_id,)
            ).fetchall()
        
        if not user_feeds:
            conn.close()
            return
        
        # Build mapping of (new_feed_id, seed_feed_id)
        seed_feed_ids = []
        for feed in user_feeds:
            topic, language = feed["topic"], feed["language"]
            seed_feed = conn.execute(
                "SELECT id FROM feeds WHERE user_id = 0 AND topic = ? AND language = ?",
                (topic, language)
            ).fetchone()
            if seed_feed:
                seed_feed_ids.append((feed["id"], seed_feed["id"]))
        
        if not seed_feed_ids:
            conn.close()
            return
        
        # Copy articles from seed feeds to new user's feeds
        copied = 0
        for new_feed_id, seed_feed_id in seed_feed_ids:
            articles = conn.execute(
                "SELECT title, url, summary, sentiment, confidence_score, topic, language, inference_log, published_at FROM articles WHERE feed_id = ?",
                (seed_feed_id,)
            ).fetchall()
            
            for article in articles:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO articles
                        (feed_id, title, url, summary, sentiment, confidence_score, topic, language, inference_log, published_at, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        new_feed_id,
                        article["title"],
                        article["url"],
                        article["summary"],
                        article["sentiment"],
                        article["confidence_score"],
                        article["topic"],
                        article["language"],
                        article["inference_log"],
                        article["published_at"],
                        datetime.utcnow().isoformat()
                    ))
                    conn.commit()
                    copied += 1
                except Exception as e:
                    print(f"Failed to copy article: {e}")
                    continue
        
        if copied > 0:
            print(f"Copied {copied} seed articles to user {user_id}")
    finally:
        conn.close()
