"""News data fetching and sentiment analysis module."""
import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from textblob import TextBlob
from bs4 import BeautifulSoup
from cachetools import TTLCache
import config


class NewsFetcher:
    """Fetches and analyzes news for stocks."""

    def __init__(self):
        self._cache = TTLCache(maxsize=200, ttl=config.CACHE_TTL_MINUTES * 60)

    def get_yahoo_finance_news(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch news from Yahoo Finance RSS feed."""
        cache_key = f"yahoo_news_{symbol}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
            feed = feedparser.parse(url)

            news_items = []
            for entry in feed.entries[:10]:
                published = entry.get('published', '')
                if published:
                    try:
                        pub_date = datetime(*entry.published_parsed[:6])
                    except Exception:
                        pub_date = datetime.now()
                else:
                    pub_date = datetime.now()

                news_item = {
                    "title": entry.get('title', ''),
                    "link": entry.get('link', ''),
                    "published": pub_date.isoformat(),
                    "source": "Yahoo Finance",
                    "summary": entry.get('summary', '')[:500] if entry.get('summary') else '',
                }

                # Analyze sentiment
                text = f"{news_item['title']} {news_item['summary']}"
                sentiment = self._analyze_sentiment(text)
                news_item["sentiment"] = sentiment

                news_items.append(news_item)

            self._cache[cache_key] = news_items
            return news_items

        except Exception as e:
            print(f"Error fetching Yahoo Finance news: {e}")
            return []

    def get_google_news(self, symbol: str, company_name: str = "") -> List[Dict[str, Any]]:
        """Fetch news from Google News RSS."""
        cache_key = f"google_news_{symbol}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            search_term = f"{symbol} stock" if not company_name else f"{company_name} stock"
            url = f"https://news.google.com/rss/search?q={search_term}&hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(url)

            news_items = []
            for entry in feed.entries[:10]:
                published = entry.get('published', '')
                if published:
                    try:
                        pub_date = datetime(*entry.published_parsed[:6])
                    except Exception:
                        pub_date = datetime.now()
                else:
                    pub_date = datetime.now()

                news_item = {
                    "title": entry.get('title', ''),
                    "link": entry.get('link', ''),
                    "published": pub_date.isoformat(),
                    "source": "Google News",
                    "summary": "",
                }

                # Analyze sentiment from title
                sentiment = self._analyze_sentiment(news_item['title'])
                news_item["sentiment"] = sentiment

                news_items.append(news_item)

            self._cache[cache_key] = news_items
            return news_items

        except Exception as e:
            print(f"Error fetching Google News: {e}")
            return []

    def get_finnhub_news(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch news from Finnhub API (requires API key)."""
        if not config.FINNHUB_API_KEY:
            return []

        cache_key = f"finnhub_news_{symbol}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            today = datetime.now()
            week_ago = today - timedelta(days=7)

            url = f"https://finnhub.io/api/v1/company-news"
            params = {
                "symbol": symbol,
                "from": week_ago.strftime("%Y-%m-%d"),
                "to": today.strftime("%Y-%m-%d"),
                "token": config.FINNHUB_API_KEY
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            news_items = []
            for item in data[:15]:
                news_item = {
                    "title": item.get('headline', ''),
                    "link": item.get('url', ''),
                    "published": datetime.fromtimestamp(item.get('datetime', 0)).isoformat(),
                    "source": item.get('source', 'Finnhub'),
                    "summary": item.get('summary', '')[:500],
                }

                text = f"{news_item['title']} {news_item['summary']}"
                sentiment = self._analyze_sentiment(text)
                news_item["sentiment"] = sentiment

                news_items.append(news_item)

            self._cache[cache_key] = news_items
            return news_items

        except Exception as e:
            print(f"Error fetching Finnhub news: {e}")
            return []

    def get_all_news(self, symbol: str, company_name: str = "") -> List[Dict[str, Any]]:
        """Aggregate news from all sources."""
        all_news = []

        # Fetch from all sources
        yahoo_news = self.get_yahoo_finance_news(symbol)
        google_news = self.get_google_news(symbol, company_name)
        finnhub_news = self.get_finnhub_news(symbol)

        all_news.extend(yahoo_news)
        all_news.extend(google_news)
        all_news.extend(finnhub_news)

        # Sort by published date (newest first)
        all_news.sort(key=lambda x: x.get('published', ''), reverse=True)

        # Remove duplicates based on title similarity
        seen_titles = set()
        unique_news = []
        for news in all_news:
            title_key = news['title'].lower()[:50]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_news.append(news)

        return unique_news[:20]

    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text using TextBlob."""
        if not text:
            return {"score": 0, "label": "neutral", "subjectivity": 0}

        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            if polarity > 0.1:
                label = "positive"
            elif polarity < -0.1:
                label = "negative"
            else:
                label = "neutral"

            return {
                "score": round(polarity, 3),
                "label": label,
                "subjectivity": round(subjectivity, 3)
            }

        except Exception:
            return {"score": 0, "label": "neutral", "subjectivity": 0}

    def get_sentiment_summary(self, symbol: str, company_name: str = "") -> Dict[str, Any]:
        """Get overall sentiment summary for a stock."""
        news = self.get_all_news(symbol, company_name)

        if not news:
            return {
                "overall_sentiment": "neutral",
                "average_score": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "news_count": 0
            }

        scores = [n['sentiment']['score'] for n in news if 'sentiment' in n]
        labels = [n['sentiment']['label'] for n in news if 'sentiment' in n]

        avg_score = sum(scores) / len(scores) if scores else 0

        if avg_score > 0.1:
            overall = "positive"
        elif avg_score < -0.1:
            overall = "negative"
        else:
            overall = "neutral"

        return {
            "overall_sentiment": overall,
            "average_score": round(avg_score, 3),
            "positive_count": labels.count("positive"),
            "negative_count": labels.count("negative"),
            "neutral_count": labels.count("neutral"),
            "news_count": len(news)
        }
