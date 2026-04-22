TOPIC_QUERIES = {
    "AI": "artificial+intelligence",
    "Tech": "technology",
    "Politics": "politics",
    "Sport": "sport",
    "Economy": "economy",
    "Science": "science",
}

# BBC Arabic - confirmed working 25 entries
BBC_ARABIC = {
    "AI":       "https://feeds.bbci.co.uk/arabic/scienceandtech/rss.xml",
    "Tech":     "https://feeds.bbci.co.uk/arabic/scienceandtech/rss.xml",
    "Politics": "https://feeds.bbci.co.uk/arabic/worldservice/rss.xml",
    "Sport":    "https://feeds.bbci.co.uk/arabic/sport/rss.xml",
    "Economy":  "https://feeds.bbci.co.uk/arabic/business/rss.xml",
    "Science":  "https://feeds.bbci.co.uk/arabic/scienceandtech/rss.xml",
}

# Algerian Arabic sources (WordPress RSS)
ALGERIAN_ARABIC = {
    "AI":       "https://www.ennaharonline.com/feed/",
    "Tech":     "https://www.ennaharonline.com/feed/",
    "Politics": "https://www.ennaharonline.com/feed/",
    "Sport":    "https://sport.ennaharonline.com/feed/",
    "Economy":  "https://www.ennaharonline.com/feed/",
    "Science":  "https://www.ennaharonline.com/feed/",
}

# Algerian French sources
ALGERIAN_FRENCH = {
    "AI":       "https://www.tsa-algerie.com/feed/",
    "Tech":     "https://www.tsa-algerie.com/feed/",
    "Politics": "https://www.tsa-algerie.com/feed/",
    "Sport":    "https://www.tsa-algerie.com/feed/",
    "Economy":  "https://www.tsa-algerie.com/feed/",
    "Science":  "https://www.tsa-algerie.com/feed/",
}

def get_feed_urls(topic: str) -> list:
    """Generate multilingual RSS feed URLs for a topic"""
    query = TOPIC_QUERIES.get(topic, topic)
    return [
        # English - Google News
        f"https://news.google.com/rss/search?q={query}&hl=en&gl=US&ceid=US:en",
        # French - Google News (covers international French press)
        f"https://news.google.com/rss/search?q={query}&hl=fr&gl=FR&ceid=FR:fr",
        # Arabic - BBC Arabic
        BBC_ARABIC.get(topic, "https://feeds.bbci.co.uk/arabic/worldservice/rss.xml"),
        # Arabic - Ennahar Algeria
        ALGERIAN_ARABIC.get(topic, "https://www.ennaharonline.com/feed/"),
        # French - TSA Algeria
        ALGERIAN_FRENCH.get(topic, "https://www.tsa-algerie.com/feed/"),
    ]