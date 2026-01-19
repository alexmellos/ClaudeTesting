# S&P 500 Stock Analyzer

A comprehensive stock analysis system for S&P 500 companies focused on short-term trading. Combines technical analysis, fundamental analysis, and news sentiment to generate trading signals.

## Features

### Technical Analysis
- **Moving Averages**: SMA (5, 10, 20, 50, 200), EMA (9, 12, 20, 26, 50)
- **Momentum Indicators**: RSI, MACD, Stochastic Oscillator, Williams %R, CCI, ROC
- **Volatility**: Bollinger Bands, ATR
- **Volume**: OBV, VWAP
- **Trend Detection**: Golden Cross / Death Cross detection

### Fundamental Analysis
- Valuation metrics (P/E, Forward P/E, PEG, Price/Book)
- Growth metrics (Revenue growth, Earnings growth)
- Profitability (Profit margins, EPS)
- Analyst ratings and price targets
- Risk assessment (Beta, 52-week range)

### Sentiment Analysis
- News aggregation from multiple sources (Yahoo Finance, Google News, Finnhub)
- Sentiment scoring using TextBlob NLP
- Overall sentiment summary

### Signal Generation
- Combined scoring system with weighted signals
- Action recommendations (Strong Buy, Buy, Hold, Sell, Strong Sell)
- Confidence and risk assessment

## Installation

1. Clone the repository:
```bash
cd stock_analyzer
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. (Optional) Configure API keys for enhanced data:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Usage

### Quick Start

Run the application:
```bash
python run.py
```

Choose from:
1. **Web Dashboard** (Streamlit) - Interactive UI for analysis
2. **API Server** (FastAPI) - REST API for programmatic access
3. **Both** - Run dashboard and API together

### Web Dashboard

```bash
streamlit run dashboard/app.py
```

Open http://localhost:8501 in your browser.

### API Server

```bash
uvicorn api.main:app --reload
```

API available at http://localhost:8000
Documentation at http://localhost:8000/docs

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /stock/{symbol}` | Basic stock information |
| `GET /stock/{symbol}/historical` | Historical price data |
| `GET /stock/{symbol}/technical` | Technical indicators |
| `GET /stock/{symbol}/fundamentals` | Fundamental analysis |
| `GET /stock/{symbol}/news` | News and sentiment |
| `GET /stock/{symbol}/signals` | Trading signals |
| `GET /stock/{symbol}/full-analysis` | Complete analysis |
| `GET /screener` | Stock screener with filters |
| `GET /sp500` | List of S&P 500 symbols |
| `GET /sp500/overview` | Overview of top stocks |

## Project Structure

```
stock_analyzer/
├── api/
│   ├── __init__.py
│   └── main.py           # FastAPI backend
├── analysis/
│   ├── __init__.py
│   ├── technical.py      # Technical indicators
│   ├── fundamentals.py   # Fundamental analysis
│   └── signals.py        # Signal generation
├── dashboard/
│   ├── __init__.py
│   └── app.py            # Streamlit dashboard
├── data/
│   ├── __init__.py
│   ├── stock_data.py     # Stock data fetching
│   └── news_data.py      # News fetching & sentiment
├── utils/
│   └── __init__.py
├── config.py             # Configuration settings
├── requirements.txt      # Dependencies
├── run.py               # Application launcher
└── README.md
```

## Configuration

Edit `config.py` to customize:
- RSI thresholds (oversold/overbought)
- Moving average periods
- Cache settings
- S&P 500 company list

## Data Sources

- **Yahoo Finance** (via yfinance): Price data, fundamentals, options
- **Google News**: News articles (free)
- **Finnhub** (optional): Enhanced news with API key
- **Wikipedia**: S&P 500 company list

## Disclaimer

This tool is for educational and informational purposes only. It is not financial advice. Always do your own research and consult with a qualified financial advisor before making investment decisions. Past performance does not guarantee future results.

## License

MIT License
