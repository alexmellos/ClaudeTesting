"""Streamlit dashboard for stock analysis."""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
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

# Page config
st.set_page_config(
    page_title="Stock Analyzer - S&P 500",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'stock_fetcher' not in st.session_state:
    st.session_state.stock_fetcher = StockDataFetcher()
if 'news_fetcher' not in st.session_state:
    st.session_state.news_fetcher = NewsFetcher()

stock_fetcher = st.session_state.stock_fetcher
news_fetcher = st.session_state.news_fetcher


def create_candlestick_chart(df: pd.DataFrame, symbol: str, indicators: bool = True) -> go.Figure:
    """Create an interactive candlestick chart with indicators."""
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=(f'{symbol} Price', 'Volume', 'RSI')
    )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df['date'] if 'date' in df.columns else df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Price'
        ),
        row=1, col=1
    )

    if indicators and 'sma_20' in df.columns:
        # Add moving averages
        fig.add_trace(
            go.Scatter(
                x=df['date'] if 'date' in df.columns else df.index,
                y=df['sma_20'],
                mode='lines',
                name='SMA 20',
                line=dict(color='orange', width=1)
            ),
            row=1, col=1
        )

        if 'sma_50' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['date'] if 'date' in df.columns else df.index,
                    y=df['sma_50'],
                    mode='lines',
                    name='SMA 50',
                    line=dict(color='blue', width=1)
                ),
                row=1, col=1
            )

        # Add Bollinger Bands
        if 'bb_upper' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['date'] if 'date' in df.columns else df.index,
                    y=df['bb_upper'],
                    mode='lines',
                    name='BB Upper',
                    line=dict(color='gray', width=1, dash='dash')
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df['date'] if 'date' in df.columns else df.index,
                    y=df['bb_lower'],
                    mode='lines',
                    name='BB Lower',
                    line=dict(color='gray', width=1, dash='dash'),
                    fill='tonexty',
                    fillcolor='rgba(128, 128, 128, 0.1)'
                ),
                row=1, col=1
            )

    # Volume
    colors = ['red' if row['close'] < row['open'] else 'green'
              for _, row in df.iterrows()]
    fig.add_trace(
        go.Bar(
            x=df['date'] if 'date' in df.columns else df.index,
            y=df['volume'],
            marker_color=colors,
            name='Volume'
        ),
        row=2, col=1
    )

    # RSI
    if 'rsi' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['date'] if 'date' in df.columns else df.index,
                y=df['rsi'],
                mode='lines',
                name='RSI',
                line=dict(color='purple', width=1)
            ),
            row=3, col=1
        )
        # Add RSI thresholds
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    fig.update_layout(
        height=700,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        template='plotly_dark'
    )

    return fig


def create_macd_chart(df: pd.DataFrame) -> go.Figure:
    """Create MACD chart."""
    fig = go.Figure()

    if 'macd' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['date'] if 'date' in df.columns else df.index,
                y=df['macd'],
                mode='lines',
                name='MACD',
                line=dict(color='blue', width=1)
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df['date'] if 'date' in df.columns else df.index,
                y=df['macd_signal'],
                mode='lines',
                name='Signal',
                line=dict(color='orange', width=1)
            )
        )

        # Histogram
        colors = ['green' if val >= 0 else 'red' for val in df['macd_histogram']]
        fig.add_trace(
            go.Bar(
                x=df['date'] if 'date' in df.columns else df.index,
                y=df['macd_histogram'],
                name='Histogram',
                marker_color=colors
            )
        )

    fig.update_layout(
        title='MACD',
        height=300,
        template='plotly_dark'
    )

    return fig


def display_signal_card(signal: dict, title: str):
    """Display a signal card with color coding."""
    action = signal.get('action_recommendation', {}).get('action', 'HOLD')

    if 'BUY' in action:
        color = 'green'
        emoji = '🟢'
    elif 'SELL' in action:
        color = 'red'
        emoji = '🔴'
    else:
        color = 'gray'
        emoji = '🟡'

    confidence = signal.get('action_recommendation', {}).get('confidence', 0)

    st.markdown(f"""
    <div style="
        background-color: rgba(128, 128, 128, 0.1);
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid {color};
    ">
        <h3>{emoji} {action}</h3>
        <p>Confidence: {confidence:.0%}</p>
        <p>Risk: {signal.get('action_recommendation', {}).get('risk_level', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)


def main():
    st.title("📈 S&P 500 Stock Analyzer")
    st.markdown("*Short-term trading analysis with technical, fundamental, and sentiment signals*")

    # Sidebar
    st.sidebar.header("Stock Selection")

    # Stock selection
    selected_stock = st.sidebar.selectbox(
        "Select a stock",
        options=config.SP500_TOP_COMPANIES,
        index=0
    )

    # Or enter custom symbol
    custom_symbol = st.sidebar.text_input("Or enter symbol:", "").upper()
    if custom_symbol:
        selected_stock = custom_symbol

    # Time period selection
    period = st.sidebar.selectbox(
        "Analysis Period",
        options=["1mo", "3mo", "6mo", "1y", "2y"],
        index=2
    )

    # Analysis button
    analyze_button = st.sidebar.button("🔍 Analyze Stock", type="primary", use_container_width=True)

    if analyze_button or selected_stock:
        with st.spinner(f"Analyzing {selected_stock}..."):
            try:
                # Fetch data
                info = stock_fetcher.get_stock_info(selected_stock)

                if "error" in info:
                    st.error(f"Error fetching data for {selected_stock}: {info['error']}")
                    return

                df = stock_fetcher.get_historical_data(selected_stock, period=period)

                if df.empty:
                    st.error(f"No historical data available for {selected_stock}")
                    return

                # Run technical analysis
                technical_analyzer = TechnicalAnalyzer(df)
                technical_analyzer.calculate_all()

                # Run fundamental analysis
                fundamentals_analyzer = FundamentalsAnalyzer(info)
                fundamentals = fundamentals_analyzer.analyze()

                # Get news and sentiment
                company_name = info.get("name", "")
                news = news_fetcher.get_all_news(selected_stock, company_name)
                sentiment = news_fetcher.get_sentiment_summary(selected_stock, company_name)

                # Generate signals
                signal_generator = SignalGenerator(
                    technical_analyzer,
                    fundamentals_analyzer,
                    sentiment
                )
                signals = signal_generator.generate_signals()

                # Display header info
                col1, col2, col3, col4 = st.columns(4)

                price = info.get('current_price', 0)
                prev_close = info.get('previous_close', 0)
                change = price - prev_close if prev_close else 0
                change_pct = (change / prev_close * 100) if prev_close else 0

                with col1:
                    st.metric(
                        label=f"{info.get('name', selected_stock)}",
                        value=f"${price:.2f}",
                        delta=f"{change:.2f} ({change_pct:.2f}%)"
                    )

                with col2:
                    st.metric(
                        label="Volume",
                        value=f"{info.get('volume', 0):,.0f}"
                    )

                with col3:
                    st.metric(
                        label="Market Cap",
                        value=f"${info.get('market_cap', 0)/1e9:.1f}B"
                    )

                with col4:
                    st.metric(
                        label="P/E Ratio",
                        value=f"{info.get('pe_ratio', 'N/A'):.1f}" if info.get('pe_ratio') else "N/A"
                    )

                # Signal summary
                st.markdown("---")
                st.subheader("📊 Trading Signal")

                sig_col1, sig_col2, sig_col3 = st.columns(3)

                with sig_col1:
                    display_signal_card(signals, "Overall Signal")

                with sig_col2:
                    tech_overall = signals['technical']['overall']
                    st.markdown(f"""
                    **Technical:** {'🟢' if tech_overall == 'bullish' else '🔴' if tech_overall == 'bearish' else '🟡'} {tech_overall.title()}

                    **Fundamental:** {'🟢' if signals['fundamental']['overall'] in ['strong_buy', 'buy'] else '🔴' if signals['fundamental']['overall'] in ['strong_sell', 'sell'] else '🟡'} {signals['fundamental']['overall'].replace('_', ' ').title()}

                    **Sentiment:** {'🟢' if signals['sentiment']['overall'] == 'positive' else '🔴' if signals['sentiment']['overall'] == 'negative' else '🟡'} {signals['sentiment']['overall'].title()}
                    """)

                with sig_col3:
                    combined = signals['combined']
                    st.markdown(f"""
                    **Combined Score:** {combined['combined_score']:.2f}

                    **Buy Signals:** {combined['buy_signals']}

                    **Sell Signals:** {combined['sell_signals']}
                    """)

                # Price chart
                st.markdown("---")
                st.subheader("📈 Price Chart with Indicators")

                chart_df = technical_analyzer.df
                fig = create_candlestick_chart(chart_df, selected_stock)
                st.plotly_chart(fig, use_container_width=True)

                # MACD Chart
                macd_fig = create_macd_chart(chart_df)
                st.plotly_chart(macd_fig, use_container_width=True)

                # Technical indicators
                st.markdown("---")
                st.subheader("🔧 Technical Indicators")

                indicators = technical_analyzer.get_latest_indicators()

                ind_col1, ind_col2, ind_col3, ind_col4 = st.columns(4)

                with ind_col1:
                    st.markdown("**Momentum**")
                    rsi = indicators['momentum'].get('rsi')
                    rsi_status = "Oversold 🟢" if rsi and rsi < 30 else "Overbought 🔴" if rsi and rsi > 70 else "Neutral"
                    st.write(f"RSI: {rsi:.1f} ({rsi_status})" if rsi else "RSI: N/A")
                    st.write(f"MACD: {indicators['momentum'].get('macd', 'N/A')}")
                    st.write(f"Stochastic K: {indicators['momentum'].get('stoch_k', 'N/A')}")

                with ind_col2:
                    st.markdown("**Moving Averages**")
                    st.write(f"SMA 20: ${indicators['moving_averages'].get('sma_20', 0):.2f}" if indicators['moving_averages'].get('sma_20') else "SMA 20: N/A")
                    st.write(f"SMA 50: ${indicators['moving_averages'].get('sma_50', 0):.2f}" if indicators['moving_averages'].get('sma_50') else "SMA 50: N/A")
                    st.write(f"EMA 20: ${indicators['moving_averages'].get('ema_20', 0):.2f}" if indicators['moving_averages'].get('ema_20') else "EMA 20: N/A")

                with ind_col3:
                    st.markdown("**Volatility**")
                    st.write(f"BB Upper: ${indicators['volatility'].get('bb_upper', 0):.2f}" if indicators['volatility'].get('bb_upper') else "BB Upper: N/A")
                    st.write(f"BB Lower: ${indicators['volatility'].get('bb_lower', 0):.2f}" if indicators['volatility'].get('bb_lower') else "BB Lower: N/A")
                    st.write(f"ATR: {indicators['volatility'].get('atr', 'N/A')}")

                with ind_col4:
                    st.markdown("**Volume**")
                    st.write(f"OBV: {indicators['volume'].get('obv', 'N/A')}")
                    st.write(f"VWAP: ${indicators['volume'].get('vwap', 0):.2f}" if indicators['volume'].get('vwap') else "VWAP: N/A")

                # Fundamental analysis
                st.markdown("---")
                st.subheader("💰 Fundamental Analysis")

                fund_col1, fund_col2, fund_col3 = st.columns(3)

                with fund_col1:
                    st.markdown("**Valuation**")
                    st.write(f"P/E Ratio: {info.get('pe_ratio', 'N/A')}")
                    st.write(f"Forward P/E: {info.get('forward_pe', 'N/A')}")
                    st.write(f"PEG Ratio: {info.get('peg_ratio', 'N/A')}")
                    st.write(f"Price/Book: {info.get('price_to_book', 'N/A')}")
                    st.write(f"Assessment: {fundamentals['valuation']['assessment']}")

                with fund_col2:
                    st.markdown("**Growth**")
                    rev_growth = info.get('revenue_growth')
                    earn_growth = info.get('earnings_growth')
                    st.write(f"Revenue Growth: {rev_growth:.1%}" if rev_growth else "Revenue Growth: N/A")
                    st.write(f"Earnings Growth: {earn_growth:.1%}" if earn_growth else "Earnings Growth: N/A")
                    st.write(f"Assessment: {fundamentals['growth']['assessment']}")

                with fund_col3:
                    st.markdown("**Analyst Ratings**")
                    st.write(f"Recommendation: {info.get('recommendation', 'N/A')}")
                    st.write(f"Target Price: ${info.get('target_mean_price', 0):.2f}" if info.get('target_mean_price') else "Target Price: N/A")
                    upside = fundamentals['analyst_ratings'].get('upside_percent')
                    st.write(f"Upside Potential: {upside:.1f}%" if upside else "Upside: N/A")
                    st.write(f"Analyst Count: {info.get('analyst_count', 0)}")

                # News and sentiment
                st.markdown("---")
                st.subheader("📰 News & Sentiment")

                sent_col1, sent_col2 = st.columns([1, 3])

                with sent_col1:
                    overall_sent = sentiment.get('overall_sentiment', 'neutral')
                    sent_emoji = '🟢' if overall_sent == 'positive' else '🔴' if overall_sent == 'negative' else '🟡'
                    st.markdown(f"### {sent_emoji} {overall_sent.title()}")
                    st.write(f"Average Score: {sentiment.get('average_score', 0):.2f}")
                    st.write(f"Positive: {sentiment.get('positive_count', 0)}")
                    st.write(f"Negative: {sentiment.get('negative_count', 0)}")
                    st.write(f"Neutral: {sentiment.get('neutral_count', 0)}")

                with sent_col2:
                    if news:
                        for article in news[:5]:
                            sent = article.get('sentiment', {})
                            sent_label = sent.get('label', 'neutral')
                            icon = '🟢' if sent_label == 'positive' else '🔴' if sent_label == 'negative' else '🟡'
                            st.markdown(f"{icon} [{article['title']}]({article['link']})")
                            st.caption(f"{article.get('source', 'Unknown')} | {article.get('published', '')[:10]}")
                    else:
                        st.write("No recent news found.")

                # Signal details
                st.markdown("---")
                with st.expander("📋 Detailed Signal Analysis"):
                    st.json(signals)

            except Exception as e:
                st.error(f"Error analyzing stock: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

    # Sidebar info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.markdown("""
    This tool analyzes S&P 500 stocks using:
    - **Technical Analysis**: RSI, MACD, Moving Averages, Bollinger Bands, etc.
    - **Fundamental Analysis**: P/E, Growth, Valuations
    - **Sentiment Analysis**: News sentiment scoring

    *For educational purposes only. Not financial advice.*
    """)


if __name__ == "__main__":
    main()
