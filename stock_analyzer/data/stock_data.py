"""Stock data fetching module using Yahoo Finance and Alpha Vantage."""
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from cachetools import TTLCache
import config


class StockDataFetcher:
    """Fetches stock data from multiple sources."""

    def __init__(self):
        self._price_cache = TTLCache(maxsize=500, ttl=config.PRICE_CACHE_TTL)
        self._info_cache = TTLCache(maxsize=500, ttl=config.CACHE_TTL_MINUTES * 60)

    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive stock information."""
        cache_key = f"info_{symbol}"
        if cache_key in self._info_cache:
            return self._info_cache[cache_key]

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            result = {
                "symbol": symbol,
                "name": info.get("longName", info.get("shortName", symbol)),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "market_cap": info.get("marketCap", 0),
                "current_price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
                "previous_close": info.get("previousClose", 0),
                "open": info.get("open", info.get("regularMarketOpen", 0)),
                "day_high": info.get("dayHigh", info.get("regularMarketDayHigh", 0)),
                "day_low": info.get("dayLow", info.get("regularMarketDayLow", 0)),
                "volume": info.get("volume", info.get("regularMarketVolume", 0)),
                "avg_volume": info.get("averageVolume", 0),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh", 0),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow", 0),
                "pe_ratio": info.get("trailingPE", info.get("forwardPE", None)),
                "forward_pe": info.get("forwardPE", None),
                "peg_ratio": info.get("pegRatio", None),
                "price_to_book": info.get("priceToBook", None),
                "dividend_yield": info.get("dividendYield", 0),
                "eps": info.get("trailingEps", None),
                "beta": info.get("beta", None),
                "profit_margins": info.get("profitMargins", None),
                "revenue_growth": info.get("revenueGrowth", None),
                "earnings_growth": info.get("earningsGrowth", None),
                "target_mean_price": info.get("targetMeanPrice", None),
                "recommendation": info.get("recommendationKey", "N/A"),
                "analyst_count": info.get("numberOfAnalystOpinions", 0),
            }

            self._info_cache[cache_key] = result
            return result

        except Exception as e:
            return {"symbol": symbol, "error": str(e)}

    def get_historical_data(
        self,
        symbol: str,
        period: str = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """Get historical price data."""
        period = period or config.DEFAULT_PERIOD

        try:
            ticker = yf.Ticker(symbol)

            if start_date and end_date:
                df = ticker.history(start=start_date, end=end_date, interval=interval)
            else:
                df = ticker.history(period=period, interval=interval)

            if df.empty:
                return pd.DataFrame()

            df = df.reset_index()
            df.columns = [col.lower().replace(" ", "_") for col in df.columns]

            return df

        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()

    def get_intraday_data(self, symbol: str, interval: str = "5m") -> pd.DataFrame:
        """Get intraday price data for short-term analysis."""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1d", interval=interval)

            if df.empty:
                return pd.DataFrame()

            df = df.reset_index()
            df.columns = [col.lower().replace(" ", "_") for col in df.columns]

            return df

        except Exception as e:
            print(f"Error fetching intraday data for {symbol}: {e}")
            return pd.DataFrame()

    def get_financials(self, symbol: str) -> Dict[str, Any]:
        """Get financial statements data."""
        try:
            ticker = yf.Ticker(symbol)

            income_stmt = ticker.income_stmt
            balance_sheet = ticker.balance_sheet
            cash_flow = ticker.cashflow

            result = {
                "income_statement": income_stmt.to_dict() if not income_stmt.empty else {},
                "balance_sheet": balance_sheet.to_dict() if not balance_sheet.empty else {},
                "cash_flow": cash_flow.to_dict() if not cash_flow.empty else {},
            }

            # Get quarterly data
            quarterly_income = ticker.quarterly_income_stmt
            if not quarterly_income.empty:
                result["quarterly_income"] = quarterly_income.to_dict()

            return result

        except Exception as e:
            return {"error": str(e)}

    def get_earnings_calendar(self, symbol: str) -> Dict[str, Any]:
        """Get upcoming earnings dates."""
        try:
            ticker = yf.Ticker(symbol)
            calendar = ticker.calendar

            if calendar is None or (isinstance(calendar, pd.DataFrame) and calendar.empty):
                return {"upcoming_earnings": None}

            return {"calendar": calendar}

        except Exception as e:
            return {"error": str(e)}

    def get_options_data(self, symbol: str) -> Dict[str, Any]:
        """Get options data for sentiment analysis."""
        try:
            ticker = yf.Ticker(symbol)

            # Get available expiration dates
            expirations = ticker.options

            if not expirations:
                return {"error": "No options data available"}

            # Get nearest expiration
            nearest_exp = expirations[0]
            opt_chain = ticker.option_chain(nearest_exp)

            calls = opt_chain.calls
            puts = opt_chain.puts

            # Calculate put/call ratio
            total_call_volume = calls['volume'].sum() if 'volume' in calls.columns else 0
            total_put_volume = puts['volume'].sum() if 'volume' in puts.columns else 0

            put_call_ratio = (total_put_volume / total_call_volume) if total_call_volume > 0 else 0

            return {
                "expiration_dates": list(expirations[:5]),
                "nearest_expiration": nearest_exp,
                "put_call_ratio": round(put_call_ratio, 3),
                "total_call_volume": int(total_call_volume) if pd.notna(total_call_volume) else 0,
                "total_put_volume": int(total_put_volume) if pd.notna(total_put_volume) else 0,
                "calls_count": len(calls),
                "puts_count": len(puts),
            }

        except Exception as e:
            return {"error": str(e)}

    def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get data for multiple stocks efficiently."""
        results = {}

        for symbol in symbols:
            results[symbol] = self.get_stock_info(symbol)

        return results

    def get_sp500_list(self) -> List[str]:
        """Get list of S&P 500 symbols."""
        try:
            # Try to fetch from Wikipedia
            tables = pd.read_html(config.SP500_WIKI_URL)
            sp500_table = tables[0]
            symbols = sp500_table['Symbol'].tolist()
            # Clean up symbols (replace . with -)
            symbols = [s.replace('.', '-') for s in symbols]
            return symbols
        except Exception:
            # Fallback to configured list
            return config.SP500_TOP_COMPANIES
