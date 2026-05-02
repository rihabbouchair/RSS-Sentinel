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

AL_JAZEERA_ARABIC = {
    "AI":       "https://www.aljazeera.net/xml/feeds/aljazeera/articles.xml",
    "Tech":     "https://www.aljazeera.net/xml/feeds/aljazeera/articles.xml",
    "Politics": "https://www.aljazeera.net/xml/feeds/aljazeera/articles.xml",
    "Sport":    "https://www.aljazeera.net/xml/feeds/aljazeera/articles.xml",
    "Economy":  "https://www.aljazeera.net/xml/feeds/aljazeera/articles.xml",
    "Science":  "https://www.aljazeera.net/xml/feeds/aljazeera/articles.xml",
    "Health":   "https://www.aljazeera.net/xml/feeds/aljazeera/articles.xml",
    "Business": "https://www.aljazeera.net/xml/feeds/aljazeera/articles.xml",
    "Entertainment": "https://www.aljazeera.net/xml/feeds/aljazeera/articles.xml",
    "World":    "https://www.aljazeera.net/xml/feeds/aljazeera/articles.xml",
    "Climate":  "https://www.aljazeera.net/xml/feeds/aljazeera/articles.xml",
    "Crypto":   "https://www.aljazeera.net/xml/feeds/aljazeera/articles.xml",
    "Education": "https://www.aljazeera.net/xml/feeds/aljazeera/articles.xml",
    "Travel":   "https://www.aljazeera.net/xml/feeds/aljazeera/articles.xml",
    "Gaming":   "https://www.aljazeera.net/xml/feeds/aljazeera/articles.xml",
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
    "AI":       "https://www.ennaharonline.com/feed/",
    "Tech":     "https://www.ennaharonline.com/feed/",
    "Politics": "https://www.ennaharonline.com/feed/",
    "Sport":    "https://sport.ennaharonline.com/feed/",
    "Economy":  "https://www.ennaharonline.com/feed/",
    "Science":  "https://www.ennaharonline.com/feed/",
    "Health":   "https://www.ennaharonline.com/feed/",
    "Business": "https://www.ennaharonline.com/feed/",
    "Entertainment": "https://www.ennaharonline.com/feed/",
    "World":    "https://www.ennaharonline.com/feed/",
    "Climate":  "https://www.ennaharonline.com/feed/",
    "Crypto":   "https://www.ennaharonline.com/feed/",
    "Education": "https://www.ennaharonline.com/feed/",
    "Travel":   "https://www.ennaharonline.com/feed/",
    "Gaming":   "https://www.ennaharonline.com/feed/",
}

# Additional Arabic sources (working RSS feeds)
ARABIC_NEWS_SOURCES = {
    "AI":       "https://feeds.alarabiya.net/newsfeed.xml",
    "Tech":     "https://feeds.alarabiya.net/newsfeed.xml",
    "Politics": "https://feeds.alarabiya.net/newsfeed.xml",
    "Sport":    "https://feeds.alarabiya.net/newsfeed.xml",
    "Economy":  "https://feeds.alarabiya.net/newsfeed.xml",
    "Science":  "https://feeds.alarabiya.net/newsfeed.xml",
    "Health":   "https://feeds.alarabiya.net/newsfeed.xml",
    "Business": "https://feeds.alarabiya.net/newsfeed.xml",
    "Entertainment": "https://feeds.alarabiya.net/newsfeed.xml",
    "World":    "https://feeds.alarabiya.net/newsfeed.xml",
    "Climate":  "https://feeds.alarabiya.net/newsfeed.xml",
    "Crypto":   "https://feeds.alarabiya.net/newsfeed.xml",
    "Education": "https://feeds.alarabiya.net/newsfeed.xml",
    "Travel":   "https://feeds.alarabiya.net/newsfeed.xml",
    "Gaming":   "https://feeds.alarabiya.net/newsfeed.xml",
}

# Algerian French sources
ALGERIAN_FRENCH = {
    "AI":       "https://www.tsa-algerie.com/feed/",
    "Tech":     "https://www.tsa-algerie.com/feed/",
    "Politics": "https://www.tsa-algerie.com/feed/",
    "Sport":    "https://www.tsa-algerie.com/feed/",
    "Economy":  "https://www.tsa-algerie.com/feed/",
    "Science":  "https://www.tsa-algerie.com/feed/",
    "Health":   "https://www.tsa-algerie.com/feed/",
    "Business": "https://www.tsa-algerie.com/feed/",
    "Entertainment": "https://www.tsa-algerie.com/feed/",
    "World":    "https://www.tsa-algerie.com/feed/",
    "Climate":  "https://www.tsa-algerie.com/feed/",
    "Crypto":   "https://www.tsa-algerie.com/feed/",
    "Education": "https://www.tsa-algerie.com/feed/",
    "Travel":   "https://www.tsa-algerie.com/feed/",
    "Gaming":   "https://www.tsa-algerie.com/feed/",
}

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
    
    if 'French' in languages:
        feeds.append((f"https://news.google.com/rss/search?q={query}&hl=fr&gl=FR&ceid=FR:fr", "French"))
        feeds.append((ALGERIAN_FRENCH.get(topic, "https://www.tsa-algerie.com/feed/"), "French"))
    
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
        feeds.append((ALGERIAN_ARABIC.get(topic, "https://www.ennaharonline.com/feed/"), "Arabic"))
        feeds.append((ECHOUROUK_ARABIC.get(topic, "https://www.echorouk.dz/feed/"), "Arabic"))
        feeds.append((ARABIC_NEWS_SOURCES.get(topic, "https://feeds.alarabiya.net/newsfeed.xml"), "Arabic"))
    
    return feeds