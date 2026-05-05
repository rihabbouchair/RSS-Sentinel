TOPIC_QUERIES = {
    "AI": "artificial+intelligence",
    "Tech": "technology",
    "Politics": "politics",
    "Sport": "sport",
    "Economy": "economy",
    "Science": "science",
    "Health": "health",
    "Business": "business",
    "Entertainment": "entertainment",
    "World": "world+news",
    "Climate": "climate+change",
    "Crypto": "cryptocurrency",
    "Education": "education",
    "Travel": "travel",
    "Gaming": "gaming",
    "إعلام": "world+news",
    "رياضة": "sport",
    "اقتصاد": "economy",
    "تكنولوجيا": "technology",
    "صحة": "health",
    "سياسة": "politics",
    "تعليم": "education",
}

ALGERIAN_LOCAL_TOPICS = {"World", "Politics", "Economy", "Sport"}

ECHOUROUK_ARABIC = {
    "AI":       "https://www.echorouk.dz/feed/",
    "Tech":     "https://www.echorouk.dz/feed/",
    "Politics": "https://www.echorouk.dz/feed/",
    "Sport":    "https://www.echorouk.dz/feed/",
    "Economy":  "https://www.echorouk.dz/feed/",
    "Science":  "https://www.echorouk.dz/feed/",
    "Health":   "https://www.echorouk.dz/feed/",
    "Business": "https://www.echorouk.dz/feed/",
    "Entertainment": "https://www.echorouk.dz/feed/",
    "World":    "https://www.echorouk.dz/feed/",
    "Climate":  "https://www.echorouk.dz/feed/",
    "Crypto":   "https://www.echorouk.dz/feed/",
    "Education": "https://www.echorouk.dz/feed/",
    "Travel":   "https://www.echorouk.dz/feed/",
    "Gaming":   "https://www.echorouk.dz/feed/",
}

# BBC Arabic - only topic-specific feeds that add value
BBC_ARABIC = {
    # Sport-specific feed — genuinely relevant
    "Sport":         "https://feeds.bbci.co.uk/arabic/sport/rss.xml",
    "Football":      "https://feeds.bbci.co.uk/arabic/sport/rss.xml",
    "Basketball":    "https://feeds.bbci.co.uk/arabic/sport/rss.xml",
    "Tennis":        "https://feeds.bbci.co.uk/arabic/sport/rss.xml",
    "Formula 1":     "https://feeds.bbci.co.uk/arabic/sport/rss.xml",
    "Fitness":       "https://feeds.bbci.co.uk/arabic/sport/rss.xml",

    # Business-specific feed — genuinely relevant
    "Economy":       "https://feeds.bbci.co.uk/arabic/business/rss.xml",
    "Business":      "https://feeds.bbci.co.uk/arabic/business/rss.xml",
    "Finance":       "https://feeds.bbci.co.uk/arabic/business/rss.xml",
    "Crypto":        "https://feeds.bbci.co.uk/arabic/business/rss.xml",
    "Stock Market":  "https://feeds.bbci.co.uk/arabic/business/rss.xml",
    "Investing":     "https://feeds.bbci.co.uk/arabic/business/rss.xml",
    "Startups":      "https://feeds.bbci.co.uk/arabic/business/rss.xml",
    "Energy":        "https://feeds.bbci.co.uk/arabic/business/rss.xml",
    "Real Estate":   "https://feeds.bbci.co.uk/arabic/business/rss.xml",

    # Science and tech feed — genuinely relevant
    "AI":            "https://feeds.bbci.co.uk/arabic/scienceandtech/rss.xml",
    "Tech":          "https://feeds.bbci.co.uk/arabic/scienceandtech/rss.xml",
    "Science":       "https://feeds.bbci.co.uk/arabic/scienceandtech/rss.xml",
    "Health":        "https://feeds.bbci.co.uk/arabic/scienceandtech/rss.xml",
    "Space":         "https://feeds.bbci.co.uk/arabic/scienceandtech/rss.xml",
    "Cybersecurity": "https://feeds.bbci.co.uk/arabic/scienceandtech/rss.xml",
    "Environment":   "https://feeds.bbci.co.uk/arabic/scienceandtech/rss.xml",
    "Robotics":      "https://feeds.bbci.co.uk/arabic/scienceandtech/rss.xml",
    "Biotechnology": "https://feeds.bbci.co.uk/arabic/scienceandtech/rss.xml",
    "Mental Health": "https://feeds.bbci.co.uk/arabic/scienceandtech/rss.xml",
    "Climate":       "https://feeds.bbci.co.uk/arabic/scienceandtech/rss.xml",
    "Gaming":        "https://feeds.bbci.co.uk/arabic/scienceandtech/rss.xml",
    "Quantum":       "https://feeds.bbci.co.uk/arabic/scienceandtech/rss.xml",

    # World service — only use for topics where world news is appropriate
    "Politics":      "https://feeds.bbci.co.uk/arabic/worldservice/rss.xml",
    "World":         "https://feeds.bbci.co.uk/arabic/worldservice/rss.xml",
    "Military":      "https://feeds.bbci.co.uk/arabic/worldservice/rss.xml",
    "Elections":     "https://feeds.bbci.co.uk/arabic/worldservice/rss.xml",
    "Geopolitics":   "https://feeds.bbci.co.uk/arabic/worldservice/rss.xml",
    "Diplomacy":     "https://feeds.bbci.co.uk/arabic/worldservice/rss.xml",
    "Terrorism":     "https://feeds.bbci.co.uk/arabic/worldservice/rss.xml",
    "Human Rights":  "https://feeds.bbci.co.uk/arabic/worldservice/rss.xml",
    "Immigration":   "https://feeds.bbci.co.uk/arabic/worldservice/rss.xml",
    "Protests":      "https://feeds.bbci.co.uk/arabic/worldservice/rss.xml",
    "Natural Disasters": "https://feeds.bbci.co.uk/arabic/worldservice/rss.xml",

    # NOT included (no relevant BBC Arabic feed):
    # Entertainment, Cinema, Music, Fashion, Food, Travel, Culture,
    # Agriculture, Law, Corruption, Crime
}

# Algerian Arabic sources (WordPress RSS)
ALGERIAN_ARABIC = {
    "Politics": "https://www.ennaharonline.com/feed/",
    "Sport":    "https://sport.ennaharonline.com/feed/",
    "Economy":  "https://www.ennaharonline.com/feed/",
    "World":    "https://www.ennaharonline.com/feed/",
}

# Additional Arabic sources (working RSS feeds)
# These are only used for broad Arabic topics, not narrow subjects like AI or Crypto.
ARABIC_NEWS_SOURCES = {
    "Politics": "https://feeds.alarabiya.net/newsfeed.xml",
    "Sport":    "https://feeds.alarabiya.net/newsfeed.xml",
    "Economy":  "https://feeds.alarabiya.net/newsfeed.xml",
    "World":    "https://feeds.alarabiya.net/newsfeed.xml",
}

# Algerian French sources
ALGERIAN_FRENCH = {
    "Politics": "https://www.tsa-algerie.com/feed/",
    "Sport":    "https://www.tsa-algerie.com/feed/",
    "Economy":  "https://www.tsa-algerie.com/feed/",
    "World":    "https://www.tsa-algerie.com/feed/",
}


def _append_topic_feed(feeds: list, mapping: dict, topic: str, language: str, default_url: str, allowed_topics: set[str] | None = None):
    if allowed_topics is not None and topic not in allowed_topics:
        return
    value = mapping.get(topic, default_url)
    # Support single URL or list of URLs in mapping
    if isinstance(value, (list, tuple)):
        for url in value:
            feeds.append((url, language))
    else:
        feeds.append((value, language))

def get_feed_urls(topic: str, languages: list = None) -> list:
    """Generate language-specific RSS feed URLs for a topic.
    
    Args:
        topic: Topic name
        languages: List of preferred languages ['English', 'French', 'Arabic']. 
                   Defaults to ['English'] if None.
    
    Returns:
        List of tuples (feed_url, language) filtered by language preference
    """
    if languages is None:
        languages = ['English']
    
    query = TOPIC_QUERIES.get(topic, topic)
    query_ar = query
    feeds = []
    
    if 'English' in languages:
        feeds.append((f"https://news.google.com/rss/search?q={query}&hl=en&gl=US&ceid=US:en", "English"))
        # Add curated English sources per topic to ensure discover returns real feeds
        ENGLISH_SOURCES = {
            "AI": [
                "https://venturebeat.com/category/ai/feed/",
                "https://www.technologyreview.com/feed/",
            ],
            "Tech": [
                "https://www.theverge.com/rss/index.xml",
                "https://feeds.arstechnica.com/arstechnica/index",
            ],
            "Politics": [
                "https://www.politico.com/rss/politics08.xml",
                "https://www.theguardian.com/politics/rss",
            ],
            "Sport": [
                "https://www.espn.com/espn/rss/news",
                "https://feeds.skysports.com/skysports/rss/12040",
            ],
            "Economy": [
                "https://www.theguardian.com/business/rss",
                "https://www.ft.com/?format=rss",
            ],
            "Science": [
                "https://www.sciencedaily.com/rss/all.xml",
                "https://www.nature.com/subjects/research.rss",
            ],
            "Health": [
                "https://www.who.int/feeds/entity/mediacentre/news/en/rss.xml",
                "https://www.healthline.com/rss",
            ],
            "World": [
                "https://www.reuters.com/world/rss",
                "https://www.theguardian.com/world/rss",
            ],
            "Climate": [
                "https://www.climatechangenews.com/feed/",
                "https://www.carbonbrief.org/feed/",
            ],
            "Crypto": [
                "https://cointelegraph.com/rss",
                "https://www.coindesk.com/arc/outboundfeeds/rss/",
            ],
            "Entertainment": [
                "https://variety.com/feed/",
                "https://www.hollywoodreporter.com/t/headlines/feed/",
            ],
            "Education": [
                "https://www.insidehighered.com/rss.xml",
                "https://www.timeshighereducation.com/rss",
            ],
            "Travel": [
                "https://www.lonelyplanet.com/news/feed",
                "https://www.nationalgeographic.com/travel/_jcr_content/.feed",
            ],
            "Gaming": [
                "https://www.polygon.com/rss/index.xml",
                "https://www.ign.com/articles?format=rss",
            ],
        }
        _append_topic_feed(feeds, ENGLISH_SOURCES, topic, "English", f"https://news.google.com/rss/search?q={query}&hl=en&gl=US&ceid=US:en")
    
    if 'French' in languages:
        feeds.append((f"https://news.google.com/rss/search?q={query}&hl=fr&gl=FR&ceid=FR:fr", "French"))
        _append_topic_feed(
            feeds,
            ALGERIAN_FRENCH,
            topic,
            "French",
            "https://www.tsa-algerie.com/feed/",
            ALGERIAN_LOCAL_TOPICS,
        )
    
    if 'Arabic' in languages:
        # PRIMARY: Google News Arabic with Arabic topic query
        # Searches the full Arabic web specifically for this topic
        feeds.append((
            f"https://news.google.com/rss/search?q={query_ar}&hl=ar&gl=DZ&ceid=DZ:ar",
            "Arabic",
        ))
        # SUPPLEMENT: BBC Arabic — only added when it has a genuinely
        # relevant feed for this topic (not worldservice for non-news topics)
        bbc_url = BBC_ARABIC.get(topic)
        if bbc_url:
            # Only add worldservice for topics where world news is appropriate
            worldservice_topics = {
                "Politics", "World", "Military", "Elections", "Geopolitics",
                "Diplomacy", "Terrorism", "Human Rights", "Immigration",
                "Protests", "Natural Disasters",
            }
            if bbc_url != "https://feeds.bbci.co.uk/arabic/worldservice/rss.xml" \
               or topic in worldservice_topics:
                feeds.append((bbc_url, "Arabic"))
        _append_topic_feed(
            feeds,
            ALGERIAN_ARABIC,
            topic,
            "Arabic",
            "https://www.ennaharonline.com/feed/",
            ALGERIAN_LOCAL_TOPICS,
        )
        _append_topic_feed(
            feeds,
            ECHOUROUK_ARABIC,
            topic,
            "Arabic",
            "https://www.echorouk.dz/feed/",
            ALGERIAN_LOCAL_TOPICS,
        )
        _append_topic_feed(
            feeds,
            ARABIC_NEWS_SOURCES,
            topic,
            "Arabic",
            "https://feeds.alarabiya.net/newsfeed.xml",
            ALGERIAN_LOCAL_TOPICS,
        )
    
    return feeds