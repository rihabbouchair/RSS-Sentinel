"""
pipeline.py
-----------
Two-stage article processing:

  Stage 1 — Fast keyword pre-filter (microseconds, no LLM)
    • Google News feeds are already topic-specific → skip pre-filter, trust them.
    • Generic newspaper feeds (Echorouk, Ennahar, Al Arabiya, TSA…) get a title-only
      keyword check. If the title has zero matches for the topic, the article is dropped
      immediately — no Ollama call wasted.

  Stage 2 — LLM analysis (one article at a time)
    • Trusted feeds (Google News, BBC sub-feeds): SHORT prompt → sentiment + summary only.
      Topic is already known; no need to ask the LLM to classify it again.
    • Generic feeds that passed the pre-filter: FULL prompt → topic + sentiment + summary.
      The LLM confirms topic relevance and can still reject off-topic articles.
"""

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

OLLAMA_URL      = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_TIMEOUT  = int(os.getenv("OLLAMA_TIMEOUT", "60"))
OLLAMA_RETRIES  = int(os.getenv("OLLAMA_RETRIES", "1"))

ARTICLES_PER_FEED               = int(os.getenv("ARTICLES_PER_FEED", "5"))
TARGET_READY_ARTICLES_PER_TOPIC = int(os.getenv("TARGET_READY_ARTICLES_PER_TOPIC", "4"))
MAX_ARTICLES_PER_TOPIC          = int(os.getenv("MAX_ARTICLES_PER_TOPIC", "10"))
MAX_EXCERPT_CHARS               = int(os.getenv("MAX_ANALYSIS_CHARS", "900"))
FEED_PIPELINE_WORKERS           = int(os.getenv("FEED_PIPELINE_WORKERS", "2"))
OLLAMA_MAX_CONCURRENT           = int(os.getenv("OLLAMA_MAX_CONCURRENT_REQUESTS", "1"))

# ── Canonical topic labels ─────────────────────────────────────────────────────
KNOWN_TOPICS = {
    "AI", "Tech", "Politics", "Sport", "Economy", "Science", "Health",
    "Business", "Entertainment", "World", "Climate", "Crypto", "Education",
    "Travel", "Gaming", "Cybersecurity", "Space", "Finance", "Football",
    "Basketball", "Tennis", "Formula 1", "Military", "Elections", "Law",
    "Immigration", "Human Rights", "Environment", "Energy", "Robotics",
    "Biotechnology", "Music", "Cinema", "Fashion", "Food", "Real Estate",
    "Agriculture", "Protests", "Natural Disasters", "Culture", "Geopolitics",
    "Diplomacy", "Corruption", "Crime", "Terrorism", "Mental Health",
    "Stock Market", "Investing", "Startups", "Fitness", "Quantum",
}
KNOWN_TOPICS_LOWER = {t.lower(): t for t in KNOWN_TOPICS}

# ── Pre-filter keyword bank ────────────────────────────────────────────────────
# Small focused keyword sets used ONLY for Stage-1 title checks on generic feeds.
# Each list has ~10-15 high-signal terms in EN + AR + FR roots.
PRE_FILTER_KEYWORDS: dict[str, list[str]] = {
    "AI": [
        "ai", "artificial intelligence", "machine learning", "deep learning",
        "llm", "chatgpt", "openai", "gemini", "gpt", "neural", "generative",
        "ذكاء اصطناعي", "تعلم الآلة", "نموذج لغوي",
        "intelligence artificielle",
    ],
    "Tech": [
        "tech", "software", "app", "smartphone", "chip", "google", "apple",
        "microsoft", "samsung", "internet", "digital", "cloud", "silicon",
        "تقني", "تكنولوج", "برمجي", "تطبيق", "رقمي",
        "technolog", "numérique", "logiciel",
    ],
    "Crypto": [
        "crypto", "bitcoin", "ethereum", "blockchain", "nft", "binance",
        "token", "defi", "web3", "stablecoin",
        "عملة رقمية", "بيتكوين", "بلوكتشين",
        "cryptomonnaie",
    ],
    "Gaming": [
        "game", "gaming", "playstation", "xbox", "nintendo", "esport",
        "twitch", "steam", "console", "gamer", "video game",
        "ألعاب", "بلايستيشن", "اكسبوكس",
        "jeu vidéo", "jeux video",
    ],
    "Space": [
        "space", "nasa", "rocket", "satellite", "moon", "mars", "galaxy",
        "astronaut", "spacex", "telescope", "orbit",
        "فضاء", "صاروخ", "قمر", "مريخ", "رائد فضاء",
        "fusée", "espace", "astronaute",
    ],
    "Cybersecurity": [
        "cybersecurity", "hacker", "hacking", "breach", "malware",
        "ransomware", "phishing", "data leak", "cyber", "encryption",
        "أمن سيبراني", "قرصن", "اختراق", "هجوم إلكتروني",
        "piratage", "fuite de données",
    ],
    "Science": [
        "science", "research", "study", "experiment", "discovery",
        "scientist", "lab", "physics", "chemistry", "biology", "dna",
        "علم", "بحث", "اكتشاف", "فيزياء",
        "recherche", "découverte", "scientifique",
    ],
    "Robotics": [
        "robot", "robotics", "automation", "drone", "autonomous", "humanoid",
        "روبوت", "طائرة مسيرة",
        "automatisation",
    ],
    "Climate": [
        "climate", "global warming", "carbon", "emission", "drought",
        "wildfire", "greenhouse", "renewable",
        "مناخ", "احترار", "كربون", "انبعاث",
        "climat", "réchauffement",
    ],
    "Health": [
        "health", "hospital", "vaccine", "disease", "virus", "doctor",
        "cancer", "treatment", "pandemic", "drug", "surgery",
        "صح", "مستشفى", "لقاح", "مرض", "فيروس", "طبي",
        "santé", "hôpital", "vaccin", "maladie",
    ],
    "Economy": [
        "econom", "inflation", "gdp", "trade", "recession", "dollar",
        "tariff", "currency", "fiscal", "deficit", "budget",
        "اقتصاد", "تضخم", "ميزانية", "عجز", "تجار",
        "économie", "banque centrale",
    ],
    "Politics": [
        "politic", "election", "government", "minister", "parliament",
        "president", "senate", "congress", "policy", "vote", "diplomat",
        "سياس", "انتخاب", "حكوم", "وزير", "رئيس", "برلمان",
        "politique", "gouvernement", "ministre",
    ],
    "Sport": [
        "sport", "match", "league", "cup", "team", "coach", "tournament",
        "olympic", "medal", "athlete", "championship", "stadium",
        "رياض", "مباراة", "دوري", "كأس", "فريق", "بطول",
        "équipe", "entraîneur", "coupe",
    ],
    "Football": [
        "football", "soccer", "premier league", "la liga", "champions league",
        "world cup", "fifa", "goal", "penalty", "transfer",
        "كرة القدم", "الدوري", "هدف", "ركلة جزاء",
        "ligue des champions",
    ],
    "Business": [
        "business", "company", "ceo", "merger", "acquisition", "earnings",
        "ipo", "corporate", "revenue", "profit",
        "شرك", "رئيس تنفيذي", "أرباح", "أعمال",
        "entreprise", "pdg", "fusion",
    ],
    "Finance": [
        "finance", "loan", "interest rate", "federal reserve", "bond",
        "debt", "credit", "imf", "mortgage",
        "تمويل", "قرض", "فائدة", "ديون",
        "taux", "dette",
    ],
    "Education": [
        "school", "student", "university", "education", "exam",
        "scholarship", "curriculum", "teacher",
        "تعليم", "مدرس", "طالب", "جامع", "امتحان",
        "école", "étudiant", "université",
    ],
    "Travel": [
        "travel", "tourism", "destination", "flight", "hotel", "airport",
        "سفر", "سياح", "فندق", "طيران",
        "voyage", "tourisme", "hôtel",
    ],
    "Entertainment": [
        "entertainment", "celebrity", "oscar", "grammy", "movie", "film",
        "netflix", "disney", "actor", "singer", "streaming",
        "ترفيه", "مشاهير", "جوائز", "فيلم", "مسلسل",
        "divertissement", "célébrité",
    ],
    "Military": [
        "military", "army", "war", "weapon", "missile", "airstrike",
        "troops", "defense", "navy", "soldier",
        "عسكري", "جيش", "حرب", "سلاح", "صاروخ", "قوات",
        "armée", "soldat", "guerre",
    ],
    "World": [
        "world", "global", "international", "united nations", "nato",
        "summit", "refugee", "humanitarian", "g7", "g20",
        "عالم", "دولي", "أمم متحدة", "قمة",
        "mondial", "onu",
    ],
}

# ── Thread-safety state ────────────────────────────────────────────────────────
_pipeline_state_lock = threading.Lock()
_priority_user_ids: list[int] = []
_running_user_ids: set[int] = set()
_current_logged_in_user = None
_ollama_semaphore = threading.Semaphore(max(1, OLLAMA_MAX_CONCURRENT))
_topic_pipeline_cooldown: dict[int, float] = {}  # user_id -> last trigger time


# ── Pipeline priority helpers ──────────────────────────────────────────────────
def prioritize_user_pipeline(user_id: int):
    with _pipeline_state_lock:
        if user_id in _priority_user_ids:
            _priority_user_ids.remove(user_id)
        _priority_user_ids.insert(0, user_id)


def set_logged_in_user(user_id: int):
    global _current_logged_in_user
    with _pipeline_state_lock:
        _current_logged_in_user = user_id
        print(f"[Pipeline] Logged-in user set to: {user_id}")


def _claim_user_pipeline_slot(user_id: int) -> bool:
    with _pipeline_state_lock:
        if user_id in _running_user_ids:
            return False
        _running_user_ids.add(user_id)
        return True


def _release_user_pipeline_slot(user_id: int):
    with _pipeline_state_lock:
        _running_user_ids.discard(user_id)


def _should_skip_topic_pipeline_cooldown(user_id: int, cooldown_secs: int = 2) -> bool:
    """Check if topic pipeline was triggered recently and should be skipped."""
    with _pipeline_state_lock:
        now = datetime.utcnow().timestamp()
        last_trigger = _topic_pipeline_cooldown.get(user_id, 0)
        if now - last_trigger < cooldown_secs:
            return True  # Skip this trigger
        _topic_pipeline_cooldown[user_id] = now
        return False  # Allow this trigger


def enforce_article_limits(user_id: int, articles_per_topic: int, language_preferences: list):
    """Remove excess articles to enforce per-topic limits after parallel processing."""
    if not language_preferences:
        language_preferences = ["English"]
    
    lang_dist = calculate_language_distribution(articles_per_topic, language_preferences)
    conn = get_conn()
    try:
        # Get all topics for this user
        topics = [row["topic"] for row in conn.execute(
            "SELECT DISTINCT topic FROM feeds WHERE user_id=?", (user_id,)
        ).fetchall()]
        
        for topic in topics:
            for lang, target in lang_dist.items():
                # Count articles for this topic+language
                count = conn.execute("""
                    SELECT COUNT(*) FROM articles a
                    INNER JOIN feeds f ON a.feed_id = f.id
                    WHERE f.user_id = ? AND f.topic = ? AND a.language = ?
                """, (user_id, topic, lang)).fetchone()[0]
                
                # If over limit, delete oldest excess articles
                if count > target:
                    excess = count - target
                    conn.execute("""
                        DELETE FROM articles WHERE id IN (
                            SELECT a.id FROM articles a
                            INNER JOIN feeds f ON a.feed_id = f.id
                            WHERE f.user_id = ? AND f.topic = ? AND a.language = ?
                            ORDER BY a.fetched_at ASC LIMIT ?
                        )
                    """, (user_id, topic, lang, excess))
        
        conn.commit()
    finally:
        conn.close()


def calculate_language_distribution(articles_per_topic: int, language_preferences: list) -> dict:
    if not language_preferences:
        language_preferences = ["English"]
    base = articles_per_topic // len(language_preferences)
    remainder = articles_per_topic % len(language_preferences)
    dist = {lang: base for lang in language_preferences}
    for i in range(remainder):
        dist[language_preferences[i % len(language_preferences)]] += 1
    return dist


# ── Text helpers ───────────────────────────────────────────────────────────────
def clean_html(html_text: str) -> str:
    if not html_text:
        return ""
    return BeautifulSoup(html_text, "html.parser").get_text(separator=" ", strip=True)


def extract_excerpt(text: str, max_sentences: int = 4) -> str:
    if not text:
        return ""
    normalized = " ".join(text.split())
    sentences = re.split(r"(?<=[.!?؟])\s+", normalized)
    excerpt = " ".join(s.strip() for s in sentences[:max_sentences] if s.strip())
    return (excerpt or normalized)[:MAX_EXCERPT_CHARS].strip()


def detect_language(text: str) -> str:
    if re.search(r"[\u0600-\u06FF]", text):
        return "Arabic"
    if re.search(r"[éèàùâêîôûçëïüœ]", text.lower()):
        return "French"
    return "English"


# ── Stage 1: Fast keyword pre-filter ──────────────────────────────────────────
def passes_topic_prefilter(title: str, topic: str) -> bool:
    """
    Title-only keyword check for generic feeds.
    Returns True if at least one keyword for the topic appears in the title.
    No LLM, runs in microseconds.
    """
    keywords = PRE_FILTER_KEYWORDS.get(topic)
    if not keywords:
        return True  # No filter defined — let it through to LLM
    title_lower = title.lower()
    return any(kw in title_lower for kw in keywords)


# ── Stage 2a: Short LLM prompt (trusted feeds) ────────────────────────────────
def _build_short_prompt(candidate: dict) -> str:
    lang = candidate["language"]
    title = candidate["title"]
    excerpt = candidate["excerpt"][:600]
    topic = candidate["broad_topic"]

    if lang == "Arabic":
        lang_note = "Article is in Arabic. Respond in English JSON only."
    elif lang == "French":
        lang_note = "Article is in French. Respond in English JSON only."
    else:
        lang_note = "Article is in English."

    return f"""{lang_note}
You are a news analyst. This article is about: {topic}.
Return ONLY a JSON object — no markdown, no explanation.

Fields:
"sentiment": Positive / Negative / Neutral.
  Positive = success, growth, victory, agreement, breakthrough, approval.
  Negative = conflict, death, attack, crisis, decline, scandal, failure, threat.
  Use Neutral ONLY for purely factual zero-tone content. When unsure, prefer Positive or Negative.

"confidence_score": float 0.0–1.0

"summary": 2 sentences. State what happened, who is involved, and the key outcome.
  Do NOT copy or paraphrase the title. Provide new information.

"sentiment_reason": 1 short sentence explaining your choice.

"evidence_keywords": list of 3–4 key terms from the article.

Title: {title}
Text: {excerpt}

JSON:"""


# ── Stage 2b: Full LLM prompt (generic feeds that passed pre-filter) ───────────
def _build_full_prompt(candidate: dict) -> str:
    lang = candidate["language"]
    title = candidate["title"]
    excerpt = candidate["excerpt"][:700]
    broad = candidate["broad_topic"]
    known_str = ", ".join(sorted(KNOWN_TOPICS))

    if lang == "Arabic":
        lang_note = "Article is in Arabic. Respond in English JSON only."
    elif lang == "French":
        lang_note = "Article is in French. Respond in English JSON only."
    else:
        lang_note = "Article is in English."

    return f"""{lang_note}
You are a news analyst. Return ONLY a JSON object — no markdown, no explanation.

Fields:
"topic": The TRUE topic of this article based on its actual content.
  Choose the best match from: {known_str}
  If none fit, use a specific 1-3 word English label.
  Do NOT force the topic to be "{broad}". Classify what the article is really about.
  NEVER return: General, News, Other, Update, Breaking, Latest.

"subtopic": A more specific 1-3 word label (e.g. "Transfer Window", "Interest Rates").

"sentiment": Positive / Negative / Neutral.
  Positive = success, growth, victory, agreement, breakthrough, approval.
  Negative = conflict, death, attack, crisis, decline, scandal, failure, threat.
  Use Neutral ONLY for purely factual zero-tone content. When unsure, prefer Positive or Negative.

"confidence_score": float 0.0–1.0

"summary": 2 sentences. State what happened, who is involved, and the key outcome.
  Do NOT copy or paraphrase the title. Provide new information.

"sentiment_reason": 1 short sentence.

"topic_reason": 1 short sentence explaining the topic classification.

"evidence_keywords": list of 3–5 key terms from the article.

Title: {title}
Text: {excerpt}

JSON:"""


# ── Ollama call ────────────────────────────────────────────────────────────────
def _call_ollama(prompt: str, title: str) -> dict | None:
    """Send prompt to Ollama. Returns parsed JSON dict or None."""
    num_ctx = 1024 if len(prompt) < 800 else 1536

    for attempt in range(1, OLLAMA_RETRIES + 2):
        try:
            with _ollama_semaphore:
                resp = requests.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={
                        "model": OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                        "options": {
                            "temperature": 0.2,
                            "top_p": 0.9,
                            "num_ctx": num_ctx,
                            "num_predict": 220,
                        },
                    },
                    timeout=OLLAMA_TIMEOUT,
                )
            resp.raise_for_status()
            text = resp.json().get("response", "")
            s, e = text.find("{"), text.rfind("}") + 1
            if s != -1 and e > s:
                return json.loads(text[s:e])
            raise ValueError("No JSON in Ollama response")

        except requests.exceptions.ReadTimeout:
            print(f"  Ollama timeout — '{title[:50]}'")
            return None
        except Exception as ex:
            print(f"  Ollama attempt {attempt} failed — '{title[:50]}': {ex}")

    return None


# ── Result builders ────────────────────────────────────────────────────────────
def _val_sentiment(raw) -> str:
    v = str(raw).strip().capitalize()
    return v if v in {"Positive", "Negative", "Neutral"} else "Neutral"


def _val_confidence(raw) -> float:
    try:
        return max(0.0, min(1.0, float(raw)))
    except (TypeError, ValueError):
        return 0.5


def _val_keywords(raw) -> list[str]:
    if isinstance(raw, list):
        return [str(k).strip() for k in raw if str(k).strip()][:5]
    return []


def _is_summary_bad(summary: str, title: str) -> bool:
    """True if summary is empty or just restates the title."""
    if not summary:
        return True
    s = re.sub(r"\W+", " ", summary.lower()).strip()
    t = re.sub(r"\W+", " ", title.lower()).strip()
    return s == t or (len(t) > 10 and t in s and len(s) < len(t) + 25)


def _build_result_trusted(parsed: dict, candidate: dict) -> dict:
    """Result for trusted-feed articles — topic taken from feed, not LLM."""
    topic = candidate["broad_topic"]
    summary = str(parsed.get("summary", "")).strip()
    if _is_summary_bad(summary, candidate["title"]):
        summary = candidate["excerpt"][:280]

    sentiment  = _val_sentiment(parsed.get("sentiment"))
    confidence = _val_confidence(parsed.get("confidence_score", 0.75))
    s_reason   = str(parsed.get("sentiment_reason", "")).strip()
    keywords   = _val_keywords(parsed.get("evidence_keywords"))

    log = {
        "model": OLLAMA_MODEL, "prompt_version": "v5_short",
        "timestamp_utc": datetime.utcnow().isoformat(),
        "broad_topic": topic, "language": candidate["language"],
        "source_host": candidate["source_host"], "title": candidate["title"],
        "sentiment": sentiment, "topic": topic, "subtopic": "",
        "confidence_score": confidence, "reasoning_summary": summary,
        "sentiment_reason": s_reason,
        "topic_reason": "Article sourced from a topic-specific feed.",
        "evidence_keywords": keywords,
    }
    return {
        "sentiment": sentiment, "confidence_score": confidence,
        "topic": topic, "summary": summary,
        "inference_log": json.dumps(log, ensure_ascii=False),
    }


def _build_result_generic(parsed: dict, candidate: dict) -> dict | None:
    """
    Result for generic-feed articles.
    Returns None if the LLM topic clearly doesn't match the feed topic.
    """
    broad = candidate["broad_topic"]
    raw_topic = str(parsed.get("topic", "")).strip()
    topic = KNOWN_TOPICS_LOWER.get(raw_topic.lower(), raw_topic) or broad

    # Reject if LLM thinks this is a clearly different topic
    t_low, b_low = topic.lower(), broad.lower()
    if t_low != b_low and b_low not in t_low and t_low not in b_low:
        print(f"      LLM rejected: '{topic}' ≠ feed '{broad}'")
        return None

    summary = str(parsed.get("summary", "")).strip()
    if _is_summary_bad(summary, candidate["title"]):
        summary = candidate["excerpt"][:280]

    sentiment  = _val_sentiment(parsed.get("sentiment"))
    confidence = _val_confidence(parsed.get("confidence_score", 0.6))
    subtopic   = str(parsed.get("subtopic", "")).strip()
    s_reason   = str(parsed.get("sentiment_reason", "")).strip()
    t_reason   = str(parsed.get("topic_reason", "")).strip()
    keywords   = _val_keywords(parsed.get("evidence_keywords"))

    log = {
        "model": OLLAMA_MODEL, "prompt_version": "v5_full",
        "timestamp_utc": datetime.utcnow().isoformat(),
        "broad_topic": broad, "language": candidate["language"],
        "source_host": candidate["source_host"], "title": candidate["title"],
        "sentiment": sentiment, "topic": topic, "subtopic": subtopic,
        "confidence_score": confidence, "reasoning_summary": summary,
        "sentiment_reason": s_reason, "topic_reason": t_reason,
        "evidence_keywords": keywords,
    }
    return {
        "sentiment": sentiment, "confidence_score": confidence,
        "topic": topic, "summary": summary,
        "inference_log": json.dumps(log, ensure_ascii=False),
    }


# ── Analyze one article ────────────────────────────────────────────────────────
def analyze_article(candidate: dict, is_generic: bool) -> dict | None:
    """
    Analyze a single article through the LLM.
    is_generic=False → short prompt (sentiment + summary only, topic trusted).
    is_generic=True  → full prompt (LLM also verifies topic relevance).
    Returns result dict or None if the article should be discarded.
    """
    title = candidate["title"]
    if is_generic:
        parsed = _call_ollama(_build_full_prompt(candidate), title)
        if parsed is None:
            return None
        return _build_result_generic(parsed, candidate)
    else:
        parsed = _call_ollama(_build_short_prompt(candidate), title)
        if parsed is None:
            return None
        return _build_result_trusted(parsed, candidate)


# ── Article candidate builder ──────────────────────────────────────────────────
def build_article_candidate(entry: dict, broad_topic: str) -> dict | None:
    title = entry.get("title", "Untitled")
    url   = entry.get("link", "")
    if not url:
        return None

    content = entry.get("summary", entry.get("description", ""))
    if "content" in entry and entry["content"]:
        content = entry["content"][0].get("value", content)

    cleaned = clean_html(content) or title
    excerpt = extract_excerpt(cleaned)
    source_host = urlparse(url).netloc or "unknown"

    return {
        "title": title,
        "url": url,
        "excerpt": excerpt,
        "published_at": entry.get("published", entry.get("updated", "")),
        "fetched_at": datetime.utcnow().isoformat(),
        "broad_topic": broad_topic,
        "source_host": source_host,
        "language": detect_language(f"{title} {excerpt}"),
    }


# ── DB helpers ─────────────────────────────────────────────────────────────────
def cleanup_old_articles(user_id: int):
    conn = get_conn()
    conn.execute("""
        DELETE FROM articles
        WHERE feed_id IN (SELECT id FROM feeds WHERE user_id = ?)
          AND datetime(fetched_at) < datetime('now', '-24 hours')
    """, (user_id,))
    conn.commit()
    deleted = conn.execute("SELECT changes()").fetchone()[0]
    conn.close()
    print(f"  Cleaned {deleted} old articles for user {user_id}")


def get_topic_article_count(user_id: int, broad_topic: str, language: str = None) -> int:
    conn = get_conn()
    try:
        if language:
            return conn.execute("""
                SELECT COUNT(*) FROM articles
                WHERE feed_id IN (
                    SELECT id FROM feeds WHERE user_id=? AND topic=? AND language=?
                )
            """, (user_id, broad_topic, language)).fetchone()[0]
        return conn.execute("""
            SELECT COUNT(*) FROM articles
            WHERE feed_id IN (SELECT id FROM feeds WHERE user_id=? AND topic=?)
        """, (user_id, broad_topic)).fetchone()[0]
    finally:
        conn.close()


def get_existing_urls(urls: list[str]) -> set[str]:
    if not urls:
        return set()
    conn = get_conn()
    try:
        ph = ",".join("?" for _ in urls)
        rows = conn.execute(f"SELECT url FROM articles WHERE url IN ({ph})", urls).fetchall()
        return {r["url"] for r in rows}
    finally:
        conn.close()


# ── Core feed processor ────────────────────────────────────────────────────────
def process_feed(feed: dict, user_id: int, language_per_topic_target: int = None) -> int:
    """
    Process one feed. Returns number of articles added to the DB.
    feed dict must contain: id, url, topic, language, is_generic (bool).
    """
    feed_id     = feed["id"]
    feed_url    = feed["url"]
    broad_topic = feed["topic"]
    feed_lang   = feed.get("language", "English")
    is_generic  = bool(feed.get("is_generic", False))
    target      = language_per_topic_target or TARGET_READY_ARTICLES_PER_TOPIC
    added       = 0

    label = "[generic]" if is_generic else "[trusted]"
    print(f"\nFeed: {broad_topic} ({feed_lang}) {label} — {feed_url}")

    try:
        lang_count = get_topic_article_count(user_id, broad_topic, feed_lang)
        if lang_count >= MAX_ARTICLES_PER_TOPIC:
            print(f"  At cap ({MAX_ARTICLES_PER_TOPIC}), skipping.")
            return 0

        desired = min(
            ARTICLES_PER_FEED,
            max(0, target - lang_count),
            MAX_ARTICLES_PER_TOPIC - lang_count,
        )
        if desired <= 0:
            print(f"  Already has enough articles.")
            return 0

        parsed_feed = feedparser.parse(feed_url)
        entries = parsed_feed.get("entries", [])
        print(f"  {len(entries)} entries fetched, need {desired} more")

        if not entries:
            return 0

        candidates = [c for e in entries if (c := build_article_candidate(e, broad_topic))]
        if not candidates:
            return 0

        existing_urls = get_existing_urls([c["url"] for c in candidates])
        fresh = [c for c in candidates if c["url"] not in existing_urls]
        if not fresh:
            print(f"  All entries already in DB.")
            return 0

        # ── Stage 1: Title keyword pre-filter for generic feeds ────────────────
        if is_generic:
            before = len(fresh)
            fresh = [c for c in fresh if passes_topic_prefilter(c["title"], broad_topic)]
            dropped = before - len(fresh)
            if dropped:
                print(f"  Pre-filter: dropped {dropped}/{before} off-topic titles instantly")
            if not fresh:
                print(f"  No articles passed pre-filter, skipping feed.")
                return 0

        # ── Stage 2: LLM analysis, one article at a time ───────────────────────
        for candidate in fresh:
            if added >= desired:
                break

            print(f"    → {candidate['title'][:75]}")
            result = analyze_article(candidate, is_generic=is_generic)

            if result is None:
                print(f"      Skipped.")
                continue

            try:
                conn = get_conn()
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO articles
                        (feed_id, title, url, summary, sentiment, confidence_score,
                         topic, language, inference_log, published_at, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        feed_id,
                        candidate["title"],
                        candidate["url"],
                        result["summary"],
                        result["sentiment"],
                        result["confidence_score"],
                        result["topic"],
                        candidate["language"],
                        result["inference_log"],
                        candidate["published_at"],
                        candidate["fetched_at"],
                    ))
                    conn.commit()
                    if conn.total_changes > 0:
                        added += 1
                        print(
                            f"      Saved [{result['topic']}] "
                            f"{result['sentiment']} ({result['confidence_score']:.2f})"
                        )
                finally:
                    conn.close()
            except Exception as e:
                print(f"      DB error: {e}")

        conn = get_conn()
        conn.execute(
            "UPDATE feeds SET last_fetched_at=? WHERE id=?",
            (datetime.utcnow().isoformat(), feed_id),
        )
        conn.commit()
        conn.close()

    except Exception as e:
        print(f"  Feed failed: {e}")

    return added


# ── User pipeline ──────────────────────────────────────────────────────────────
def run_pipeline_for_user(user_id: int):
    if not _claim_user_pipeline_slot(user_id):
        print(f"\n=== Pipeline already running for user {user_id}, skipping ===")
        return

    print(f"\n=== Pipeline started for user {user_id} at {datetime.utcnow()} UTC ===")
    try:
        conn = get_conn()
        user_row = conn.execute(
            "SELECT articles_per_topic, language_preferences FROM users WHERE id=?",
            (user_id,)
        ).fetchone()

        apt = 3
        lang_prefs = ["English"]
        if user_row:
            apt = user_row["articles_per_topic"] or 3
            try:
                lang_prefs = json.loads(user_row["language_preferences"] or '["English"]')
            except (json.JSONDecodeError, TypeError):
                pass

        lang_dist = calculate_language_distribution(apt, lang_prefs)
        print(f"  {apt} articles/topic → {lang_dist}")

        feeds = [dict(f) for f in conn.execute(
            "SELECT * FROM feeds WHERE user_id=? ORDER BY topic, id", (user_id,)
        ).fetchall()]
        conn.close()

        if not feeds:
            print(f"  No feeds found.")
            return

        cleanup_old_articles(user_id)

        articles_added = 0
        max_workers = max(1, min(FEED_PIPELINE_WORKERS, len(feeds), 4))

        if max_workers == 1:
            for feed in feeds:
                target = lang_dist.get(feed.get("language", "English"), apt)
                articles_added += process_feed(feed, user_id, target)
        else:
            print(f"  Processing {len(feeds)} feeds with {max_workers} workers")
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(
                        process_feed, feed, user_id,
                        lang_dist.get(feed.get("language", "English"), apt)
                    )
                    for feed in feeds
                ]
                for future in as_completed(futures):
                    try:
                        articles_added += future.result()
                    except Exception as e:
                        print(f"  Worker failed: {e}")

        # Enforce article count limits to clean up excess from parallel processing
        enforce_article_limits(user_id, apt, lang_prefs)
        
        print(f"\n=== Pipeline complete for user {user_id}: {articles_added} new articles ===")
    finally:
        _release_user_pipeline_slot(user_id)


def run_pipeline_for_user_topic(user_id: int, topic: str):
    # Check cooldown to avoid spamming messages when user clicks rapidly
    if _should_skip_topic_pipeline_cooldown(user_id, cooldown_secs=2):
        return  # Silently skip rapid triggers
    
    if not _claim_user_pipeline_slot(user_id):
        return  # Already running, skip silently

    print(f"\n=== Topic pipeline: user {user_id}, '{topic}' at {datetime.utcnow()} UTC ===")
    try:
        conn = get_conn()
        feeds = [dict(f) for f in conn.execute(
            "SELECT * FROM feeds WHERE user_id=? AND topic=? ORDER BY id",
            (user_id, topic),
        ).fetchall()]
        conn.close()

        if not feeds:
            print(f"  No feeds for '{topic}'.")
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
                        print(f"  Worker failed: {e}")

        print(f"\n=== Topic pipeline complete: '{topic}' → {articles_added} new articles ===")
    finally:
        _release_user_pipeline_slot(user_id)


def run_pipeline(priority_user_id: int = None):
    """Global pipeline. Processes all users in priority order."""
    print(f"\n=== Global pipeline started at {datetime.utcnow()} UTC ===")

    conn = get_conn()
    all_ids = [u["id"] for u in conn.execute("SELECT id FROM users ORDER BY id").fetchall()]
    conn.close()

    if not all_ids:
        print("=== No users found ===")
        return

    ordered, seen = [], set()

    def add(uid):
        if uid is not None and uid in all_ids and uid not in seen:
            ordered.append(uid)
            seen.add(uid)

    add(priority_user_id)
    with _pipeline_state_lock:
        add(_current_logged_in_user)
    with _pipeline_state_lock:
        for uid in list(_priority_user_ids):
            add(uid)
    for uid in all_ids:
        add(uid)

    print(f"Processing {len(ordered)} users: {ordered}")
    for uid in ordered:
        run_pipeline_for_user(uid)

    print(f"=== Global pipeline complete at {datetime.utcnow()} UTC ===\n")


# ── Email digest ───────────────────────────────────────────────────────────────
def send_daily_digest_for_user(user_id: int):
    conn = get_conn()
    user = conn.execute("""
        SELECT id, email, wants_email_digest, email_verified, last_digest_sent_at
        FROM users WHERE id=?
    """, (user_id,)).fetchone()

    if not user or not user["email"] or user["wants_email_digest"] != 1 or user["email_verified"] != 1:
        conn.close()
        return

    today = datetime.utcnow().date()
    if user["last_digest_sent_at"]:
        try:
            if datetime.fromisoformat(user["last_digest_sent_at"]).date() == today:
                conn.close()
                return
        except Exception:
            pass

    since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    articles = [dict(r) for r in conn.execute("""
        SELECT a.title, a.url, a.summary, a.sentiment, a.confidence_score,
               a.topic, f.topic AS feed_topic, a.published_at
        FROM articles a INNER JOIN feeds f ON a.feed_id = f.id
        WHERE f.user_id=? AND a.fetched_at>=?
        ORDER BY a.fetched_at DESC LIMIT 20
    """, (user_id, since)).fetchall()]

    if not articles:
        conn.close()
        return

    if send_digest(user["email"], articles):
        conn.execute("UPDATE users SET last_digest_sent_at=? WHERE id=?",
                     (datetime.utcnow().isoformat(), user_id))
        conn.commit()
        print(f"Digest sent for user {user_id}")
    conn.close()


def send_daily_digests():
    print(f"\n=== Daily digest job at {datetime.utcnow()} UTC ===")
    conn = get_conn()
    users = [dict(u) for u in conn.execute("""
        SELECT id FROM users
        WHERE wants_email_digest=1 AND email_verified=1 AND email IS NOT NULL
    """).fetchall()]
    conn.close()
    for u in users:
        send_daily_digest_for_user(u["id"])
    print("=== Digest job complete ===\n")


# ── Seed articles copy ─────────────────────────────────────────────────────────
def copy_seed_articles_to_user(user_id: int, topics: list = None):
    """Copy pre-seeded articles from seed user (id=0) to a new user."""
    if user_id == 0:
        return

    conn = get_conn()
    try:
        if topics:
            ph = ",".join("?" * len(topics))
            user_feeds = conn.execute(
                f"SELECT id, topic, language FROM feeds WHERE user_id=? AND topic IN ({ph})",
                [user_id] + topics
            ).fetchall()
        else:
            user_feeds = conn.execute(
                "SELECT id, topic, language FROM feeds WHERE user_id=?", (user_id,)
            ).fetchall()

        if not user_feeds:
            return

        copied = 0
        for feed in user_feeds:
            seed = conn.execute(
                "SELECT id FROM feeds WHERE user_id=0 AND topic=? AND language=?",
                (feed["topic"], feed["language"])
            ).fetchone()
            if not seed:
                continue

            for art in conn.execute(
                """SELECT title, url, summary, sentiment, confidence_score,
                          topic, language, inference_log, published_at
                   FROM articles WHERE feed_id=?""", (seed["id"],)
            ).fetchall():
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO articles
                        (feed_id, title, url, summary, sentiment, confidence_score,
                         topic, language, inference_log, published_at, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        feed["id"], art["title"], art["url"], art["summary"],
                        art["sentiment"], art["confidence_score"], art["topic"],
                        art["language"], art["inference_log"], art["published_at"],
                        datetime.utcnow().isoformat()
                    ))
                    conn.commit()
                    copied += 1
                except Exception as e:
                    print(f"Seed copy error: {e}")

        if copied:
            print(f"Copied {copied} seed articles to user {user_id}")
    finally:
        conn.close()