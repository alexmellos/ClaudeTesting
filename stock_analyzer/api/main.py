"""FastAPI backend for stock analyzer."""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.stock_data import StockDataFetcher
from data.news_data import NewsFetcher
from analysis.technical import TechnicalAnalyzer
from analysis.fundamentals import FundamentalsAnalyzer
from analysis.signals import SignalGenerator
import config

app = FastAPI(
    title="Stock Analyzer API",
    description="API for analyzing S&P 500 stocks with technical, fundamental, and sentiment analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize data fetchers
stock_fetcher = StockDataFetcher()
news_fetcher = NewsFetcher()


class StockSymbol(BaseModel):
    symbol: str


class MultipleSymbols(BaseModel):
    symbols: List[str]


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Stock Analyzer API",
        "version": "1.0.0",
        "endpoints": [
            "/stock/{symbol}",
            "/stock/{symbol}/technical",
            "/stock/{symbol}/fundamentals",
            "/stock/{symbol}/news",
            "/stock/{symbol}/signals",
            "/stock/{symbol}/full-analysis",
            "/screener",
            "/sp500"
        ]
    }


@app.get("/stock/{symbol}")
async def get_stock_info(symbol: str):
    """Get basic stock information."""
    info = stock_fetcher.get_stock_info(symbol.upper())
    if "error" in info:
        raise HTTPException(status_code=404, detail=info["error"])
    return info


@app.get("/stock/{symbol}/historical")
async def get_historical_data(
    symbol: str,
    period: str = Query(default="3mo", description="Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max"),
    interval: str = Query(default="1d", description="Interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo")
):
    """Get historical price data."""
    df = stock_fetcher.get_historical_data(symbol.upper(), period=period, interval=interval)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No historical data found for {symbol}")

    # Convert to dict for JSON response
    df['date'] = df['date'].astype(str) if 'date' in df.columns else df.index.astype(str)
    return {"symbol": symbol.upper(), "data": df.to_dict(orient="records")}


@app.get("/stock/{symbol}/technical")
async def get_technical_analysis(
    symbol: str,
    period: str = Query(default="6mo", description="Historical data period for analysis")
):
    """Get technical analysis for a stock."""
    df = stock_fetcher.get_historical_data(symbol.upper(), period=period)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

    try:
        analyzer = TechnicalAnalyzer(df)
        analyzer.calculate_all()

        return {
            "symbol": symbol.upper(),
            "indicators": analyzer.get_latest_indicators(),
            "trend": analyzer.get_trend_analysis()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stock/{symbol}/fundamentals")
async def get_fundamental_analysis(symbol: str):
    """Get fundamental analysis for a stock."""
    info = stock_fetcher.get_stock_info(symbol.upper())
    if "error" in info:
        raise HTTPException(status_code=404, detail=info["error"])

    analyzer = FundamentalsAnalyzer(info)
    analysis = analyzer.analyze()

    return {
        "symbol": symbol.upper(),
        "info": info,
        "analysis": analysis
    }


@app.get("/stock/{symbol}/news")
async def get_stock_news(symbol: str):
    """Get news and sentiment for a stock."""
    info = stock_fetcher.get_stock_info(symbol.upper())
    company_name = info.get("name", "") if "error" not in info else ""

    news = news_fetcher.get_all_news(symbol.upper(), company_name)
    sentiment = news_fetcher.get_sentiment_summary(symbol.upper(), company_name)

    return {
        "symbol": symbol.upper(),
        "news": news,
        "sentiment_summary": sentiment
    }


@app.get("/stock/{symbol}/options")
async def get_options_data(symbol: str):
    """Get options data including put/call ratio."""
    data = stock_fetcher.get_options_data(symbol.upper())
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return {"symbol": symbol.upper(), "options": data}


@app.get("/stock/{symbol}/signals")
async def get_trading_signals(symbol: str):
    """Get trading signals for a stock."""
    # Get all required data
    info = stock_fetcher.get_stock_info(symbol.upper())
    if "error" in info:
        raise HTTPException(status_code=404, detail=info["error"])

    df = stock_fetcher.get_historical_data(symbol.upper(), period="6mo")
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No historical data for {symbol}")

    company_name = info.get("name", "")
    sentiment = news_fetcher.get_sentiment_summary(symbol.upper(), company_name)

    # Run analysis
    technical_analyzer = TechnicalAnalyzer(df)
    technical_analyzer.calculate_all()

    fundamentals_analyzer = FundamentalsAnalyzer(info)

    # Generate signals
    signal_generator = SignalGenerator(
        technical_analyzer,
        fundamentals_analyzer,
        sentiment
    )

    signals = signal_generator.generate_signals()

    return {
        "symbol": symbol.upper(),
        "signals": signals
    }


@app.get("/stock/{symbol}/full-analysis")
async def get_full_analysis(symbol: str):
    """Get comprehensive analysis including all metrics and signals."""
    symbol = symbol.upper()

    # Get basic info
    info = stock_fetcher.get_stock_info(symbol)
    if "error" in info:
        raise HTTPException(status_code=404, detail=info["error"])

    # Get historical data
    df = stock_fetcher.get_historical_data(symbol, period="6mo")
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No historical data for {symbol}")

    # Technical analysis
    technical_analyzer = TechnicalAnalyzer(df)
    technical_analyzer.calculate_all()
    technical = {
        "indicators": technical_analyzer.get_latest_indicators(),
        "trend": technical_analyzer.get_trend_analysis()
    }

    # Fundamental analysis
    fundamentals_analyzer = FundamentalsAnalyzer(info)
    fundamentals = fundamentals_analyzer.analyze()

    # News and sentiment
    company_name = info.get("name", "")
    news = news_fetcher.get_all_news(symbol, company_name)
    sentiment = news_fetcher.get_sentiment_summary(symbol, company_name)

    # Generate signals
    signal_generator = SignalGenerator(
        technical_analyzer,
        fundamentals_analyzer,
        sentiment
    )
    signals = signal_generator.generate_signals()

    # Options data
    options = stock_fetcher.get_options_data(symbol)

    return {
        "symbol": symbol,
        "info": info,
        "technical": technical,
        "fundamentals": fundamentals,
        "news": {
            "articles": news[:10],
            "sentiment": sentiment
        },
        "options": options if "error" not in options else None,
        "signals": signals,
        "timestamp": pd.Timestamp.now().isoformat()
    }


@app.get("/screener")
async def screen_stocks(
    min_pe: Optional[float] = Query(default=None, description="Minimum P/E ratio"),
    max_pe: Optional[float] = Query(default=None, description="Maximum P/E ratio"),
    min_market_cap: Optional[float] = Query(default=None, description="Minimum market cap"),
    sector: Optional[str] = Query(default=None, description="Filter by sector"),
    signal: Optional[str] = Query(default=None, description="Filter by signal: buy, sell, hold"),
    limit: int = Query(default=20, description="Number of results")
):
    """Screen stocks based on criteria."""
    # Get S&P 500 list
    symbols = stock_fetcher.get_sp500_list()[:50]  # Limit for performance

    results = []
    for symbol in symbols:
        try:
            info = stock_fetcher.get_stock_info(symbol)
            if "error" in info:
                continue

            # Apply filters
            if min_pe is not None and (info.get('pe_ratio') is None or info['pe_ratio'] < min_pe):
                continue
            if max_pe is not None and (info.get('pe_ratio') is None or info['pe_ratio'] > max_pe):
                continue
            if min_market_cap is not None and (info.get('market_cap') is None or info['market_cap'] < min_market_cap):
                continue
            if sector is not None and info.get('sector', '').lower() != sector.lower():
                continue

            # Add basic signal if requested
            if signal is not None:
                df = stock_fetcher.get_historical_data(symbol, period="3mo")
                if not df.empty:
                    analyzer = TechnicalAnalyzer(df)
                    analyzer.calculate_all()
                    trend = analyzer.get_trend_analysis()

                    if signal.lower() == "buy" and trend['trend'] != "bullish":
                        continue
                    elif signal.lower() == "sell" and trend['trend'] != "bearish":
                        continue
                    elif signal.lower() == "hold" and trend['trend'] != "neutral":
                        continue

            results.append({
                "symbol": symbol,
                "name": info.get("name", symbol),
                "sector": info.get("sector", "N/A"),
                "price": info.get("current_price"),
                "pe_ratio": info.get("pe_ratio"),
                "market_cap": info.get("market_cap"),
                "change_percent": ((info.get("current_price", 0) - info.get("previous_close", 0)) /
                                  info.get("previous_close", 1) * 100) if info.get("previous_close") else None
            })

            if len(results) >= limit:
                break

        except Exception:
            continue

    return {"count": len(results), "stocks": results}


@app.get("/sp500")
async def get_sp500_list():
    """Get list of S&P 500 symbols."""
    symbols = stock_fetcher.get_sp500_list()
    return {"count": len(symbols), "symbols": symbols}


@app.get("/sp500/overview")
async def get_sp500_overview(limit: int = Query(default=20, description="Number of stocks")):
    """Get overview of top S&P 500 stocks with basic metrics."""
    symbols = config.SP500_TOP_COMPANIES[:limit]

    overview = []
    for symbol in symbols:
        try:
            info = stock_fetcher.get_stock_info(symbol)
            if "error" not in info:
                overview.append({
                    "symbol": symbol,
                    "name": info.get("name", symbol),
                    "sector": info.get("sector", "N/A"),
                    "price": info.get("current_price"),
                    "change": info.get("current_price", 0) - info.get("previous_close", 0),
                    "change_percent": ((info.get("current_price", 0) - info.get("previous_close", 0)) /
                                      info.get("previous_close", 1) * 100) if info.get("previous_close") else None,
                    "volume": info.get("volume"),
                    "market_cap": info.get("market_cap"),
                    "pe_ratio": info.get("pe_ratio"),
                    "recommendation": info.get("recommendation")
                })
        except Exception:
            continue

    return {"count": len(overview), "stocks": overview}


# Import pandas for timestamp
import pandas as pd


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
