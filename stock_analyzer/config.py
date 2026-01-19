"""Configuration settings for the stock analyzer."""
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys (set these in .env file or environment variables)
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")

# Cache settings
CACHE_TTL_MINUTES = 5
PRICE_CACHE_TTL = 60  # seconds

# Analysis settings
DEFAULT_PERIOD = "3mo"  # Default historical data period
SHORT_TERM_DAYS = 20  # Short-term moving average
MEDIUM_TERM_DAYS = 50  # Medium-term moving average
LONG_TERM_DAYS = 200  # Long-term moving average

# Technical indicator thresholds
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
MACD_SIGNAL_THRESHOLD = 0

# S&P 500 - Top companies by market cap (can be expanded)
SP500_TOP_COMPANIES = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "UNH", "JNJ",
    "JPM", "V", "PG", "XOM", "MA", "HD", "CVX", "MRK", "ABBV", "LLY",
    "PEP", "KO", "COST", "AVGO", "WMT", "MCD", "CSCO", "TMO", "ACN", "ABT",
    "DHR", "NEE", "LIN", "WFC", "PM", "TXN", "BMY", "UPS", "RTX", "HON",
    "ORCL", "COP", "LOW", "QCOM", "UNP", "SPGI", "GS", "ELV", "CAT", "BA"
]

# Full S&P 500 list endpoint
SP500_WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
