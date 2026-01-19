"""Technical analysis module with all major indicators."""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import config


class TechnicalAnalyzer:
    """Calculates technical indicators for stock analysis."""

    def __init__(self, df: pd.DataFrame):
        """Initialize with historical price data."""
        self.df = df.copy()
        self._ensure_columns()

    def _ensure_columns(self):
        """Ensure DataFrame has required columns."""
        required = ['close', 'high', 'low', 'volume']
        for col in required:
            if col not in self.df.columns:
                raise ValueError(f"Missing required column: {col}")

    def calculate_all(self) -> pd.DataFrame:
        """Calculate all technical indicators."""
        self.add_moving_averages()
        self.add_rsi()
        self.add_macd()
        self.add_bollinger_bands()
        self.add_atr()
        self.add_obv()
        self.add_vwap()
        self.add_stochastic()
        self.add_williams_r()
        self.add_cci()
        self.add_momentum()
        return self.df

    def add_moving_averages(self) -> pd.DataFrame:
        """Add Simple and Exponential Moving Averages."""
        # Simple Moving Averages
        self.df['sma_5'] = self.df['close'].rolling(window=5).mean()
        self.df['sma_10'] = self.df['close'].rolling(window=10).mean()
        self.df['sma_20'] = self.df['close'].rolling(window=config.SHORT_TERM_DAYS).mean()
        self.df['sma_50'] = self.df['close'].rolling(window=config.MEDIUM_TERM_DAYS).mean()
        self.df['sma_200'] = self.df['close'].rolling(window=config.LONG_TERM_DAYS).mean()

        # Exponential Moving Averages
        self.df['ema_9'] = self.df['close'].ewm(span=9, adjust=False).mean()
        self.df['ema_12'] = self.df['close'].ewm(span=12, adjust=False).mean()
        self.df['ema_20'] = self.df['close'].ewm(span=20, adjust=False).mean()
        self.df['ema_26'] = self.df['close'].ewm(span=26, adjust=False).mean()
        self.df['ema_50'] = self.df['close'].ewm(span=50, adjust=False).mean()

        return self.df

    def add_rsi(self, period: int = 14) -> pd.DataFrame:
        """Add Relative Strength Index."""
        delta = self.df['close'].diff()

        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        self.df['rsi'] = 100 - (100 / (1 + rs))

        # RSI signals
        self.df['rsi_oversold'] = self.df['rsi'] < config.RSI_OVERSOLD
        self.df['rsi_overbought'] = self.df['rsi'] > config.RSI_OVERBOUGHT

        return self.df

    def add_macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """Add MACD (Moving Average Convergence Divergence)."""
        ema_fast = self.df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = self.df['close'].ewm(span=slow, adjust=False).mean()

        self.df['macd'] = ema_fast - ema_slow
        self.df['macd_signal'] = self.df['macd'].ewm(span=signal, adjust=False).mean()
        self.df['macd_histogram'] = self.df['macd'] - self.df['macd_signal']

        # MACD crossover signals
        self.df['macd_bullish'] = (self.df['macd'] > self.df['macd_signal']) & \
                                   (self.df['macd'].shift(1) <= self.df['macd_signal'].shift(1))
        self.df['macd_bearish'] = (self.df['macd'] < self.df['macd_signal']) & \
                                   (self.df['macd'].shift(1) >= self.df['macd_signal'].shift(1))

        return self.df

    def add_bollinger_bands(self, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        """Add Bollinger Bands."""
        self.df['bb_middle'] = self.df['close'].rolling(window=period).mean()
        rolling_std = self.df['close'].rolling(window=period).std()

        self.df['bb_upper'] = self.df['bb_middle'] + (rolling_std * std_dev)
        self.df['bb_lower'] = self.df['bb_middle'] - (rolling_std * std_dev)

        # Bollinger Band width (volatility indicator)
        self.df['bb_width'] = (self.df['bb_upper'] - self.df['bb_lower']) / self.df['bb_middle']

        # Position within bands (0 = lower band, 1 = upper band)
        self.df['bb_position'] = (self.df['close'] - self.df['bb_lower']) / \
                                  (self.df['bb_upper'] - self.df['bb_lower'])

        return self.df

    def add_atr(self, period: int = 14) -> pd.DataFrame:
        """Add Average True Range (volatility indicator)."""
        high_low = self.df['high'] - self.df['low']
        high_close = np.abs(self.df['high'] - self.df['close'].shift())
        low_close = np.abs(self.df['low'] - self.df['close'].shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        self.df['atr'] = true_range.rolling(window=period).mean()

        # ATR percentage of price
        self.df['atr_percent'] = (self.df['atr'] / self.df['close']) * 100

        return self.df

    def add_obv(self) -> pd.DataFrame:
        """Add On-Balance Volume."""
        obv = [0]
        for i in range(1, len(self.df)):
            if self.df['close'].iloc[i] > self.df['close'].iloc[i-1]:
                obv.append(obv[-1] + self.df['volume'].iloc[i])
            elif self.df['close'].iloc[i] < self.df['close'].iloc[i-1]:
                obv.append(obv[-1] - self.df['volume'].iloc[i])
            else:
                obv.append(obv[-1])

        self.df['obv'] = obv
        self.df['obv_sma'] = self.df['obv'].rolling(window=20).mean()

        return self.df

    def add_vwap(self) -> pd.DataFrame:
        """Add Volume Weighted Average Price."""
        typical_price = (self.df['high'] + self.df['low'] + self.df['close']) / 3
        self.df['vwap'] = (typical_price * self.df['volume']).cumsum() / self.df['volume'].cumsum()

        return self.df

    def add_stochastic(self, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """Add Stochastic Oscillator."""
        low_min = self.df['low'].rolling(window=k_period).min()
        high_max = self.df['high'].rolling(window=k_period).max()

        self.df['stoch_k'] = 100 * (self.df['close'] - low_min) / (high_max - low_min)
        self.df['stoch_d'] = self.df['stoch_k'].rolling(window=d_period).mean()

        # Stochastic signals
        self.df['stoch_oversold'] = self.df['stoch_k'] < 20
        self.df['stoch_overbought'] = self.df['stoch_k'] > 80

        return self.df

    def add_williams_r(self, period: int = 14) -> pd.DataFrame:
        """Add Williams %R."""
        high_max = self.df['high'].rolling(window=period).max()
        low_min = self.df['low'].rolling(window=period).min()

        self.df['williams_r'] = -100 * (high_max - self.df['close']) / (high_max - low_min)

        return self.df

    def add_cci(self, period: int = 20) -> pd.DataFrame:
        """Add Commodity Channel Index."""
        typical_price = (self.df['high'] + self.df['low'] + self.df['close']) / 3
        sma = typical_price.rolling(window=period).mean()
        mad = typical_price.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())

        self.df['cci'] = (typical_price - sma) / (0.015 * mad)

        return self.df

    def add_momentum(self, period: int = 10) -> pd.DataFrame:
        """Add Momentum indicator."""
        self.df['momentum'] = self.df['close'] - self.df['close'].shift(period)
        self.df['roc'] = ((self.df['close'] - self.df['close'].shift(period)) /
                          self.df['close'].shift(period)) * 100

        return self.df

    def get_latest_indicators(self) -> Dict[str, Any]:
        """Get the most recent values of all indicators."""
        if len(self.df) == 0:
            return {}

        latest = self.df.iloc[-1]

        def safe_value(val):
            if pd.isna(val):
                return None
            if isinstance(val, (np.floating, float)):
                return round(float(val), 4)
            if isinstance(val, (np.integer, int)):
                return int(val)
            if isinstance(val, (np.bool_, bool)):
                return bool(val)
            return val

        indicators = {
            "price": {
                "close": safe_value(latest.get('close')),
                "high": safe_value(latest.get('high')),
                "low": safe_value(latest.get('low')),
                "volume": safe_value(latest.get('volume')),
            },
            "moving_averages": {
                "sma_5": safe_value(latest.get('sma_5')),
                "sma_10": safe_value(latest.get('sma_10')),
                "sma_20": safe_value(latest.get('sma_20')),
                "sma_50": safe_value(latest.get('sma_50')),
                "sma_200": safe_value(latest.get('sma_200')),
                "ema_9": safe_value(latest.get('ema_9')),
                "ema_20": safe_value(latest.get('ema_20')),
                "ema_50": safe_value(latest.get('ema_50')),
            },
            "momentum": {
                "rsi": safe_value(latest.get('rsi')),
                "rsi_oversold": safe_value(latest.get('rsi_oversold')),
                "rsi_overbought": safe_value(latest.get('rsi_overbought')),
                "macd": safe_value(latest.get('macd')),
                "macd_signal": safe_value(latest.get('macd_signal')),
                "macd_histogram": safe_value(latest.get('macd_histogram')),
                "stoch_k": safe_value(latest.get('stoch_k')),
                "stoch_d": safe_value(latest.get('stoch_d')),
                "williams_r": safe_value(latest.get('williams_r')),
                "cci": safe_value(latest.get('cci')),
                "momentum": safe_value(latest.get('momentum')),
                "roc": safe_value(latest.get('roc')),
            },
            "volatility": {
                "bb_upper": safe_value(latest.get('bb_upper')),
                "bb_middle": safe_value(latest.get('bb_middle')),
                "bb_lower": safe_value(latest.get('bb_lower')),
                "bb_width": safe_value(latest.get('bb_width')),
                "bb_position": safe_value(latest.get('bb_position')),
                "atr": safe_value(latest.get('atr')),
                "atr_percent": safe_value(latest.get('atr_percent')),
            },
            "volume": {
                "obv": safe_value(latest.get('obv')),
                "obv_sma": safe_value(latest.get('obv_sma')),
                "vwap": safe_value(latest.get('vwap')),
            }
        }

        return indicators

    def get_trend_analysis(self) -> Dict[str, Any]:
        """Analyze the current trend based on indicators."""
        if len(self.df) < 50:
            return {"trend": "insufficient_data"}

        latest = self.df.iloc[-1]
        close = latest['close']

        # Trend based on moving averages
        ma_signals = []

        if pd.notna(latest.get('sma_20')) and close > latest['sma_20']:
            ma_signals.append(1)
        else:
            ma_signals.append(-1)

        if pd.notna(latest.get('sma_50')) and close > latest['sma_50']:
            ma_signals.append(1)
        else:
            ma_signals.append(-1)

        if pd.notna(latest.get('sma_200')) and close > latest['sma_200']:
            ma_signals.append(1)
        else:
            ma_signals.append(-1)

        # Golden cross / Death cross
        golden_cross = False
        death_cross = False
        if pd.notna(latest.get('sma_50')) and pd.notna(latest.get('sma_200')):
            if latest['sma_50'] > latest['sma_200']:
                golden_cross = True
            else:
                death_cross = True

        # Overall trend
        avg_signal = sum(ma_signals) / len(ma_signals)
        if avg_signal > 0.5:
            trend = "bullish"
        elif avg_signal < -0.5:
            trend = "bearish"
        else:
            trend = "neutral"

        return {
            "trend": trend,
            "strength": abs(avg_signal),
            "above_sma_20": ma_signals[0] > 0,
            "above_sma_50": ma_signals[1] > 0,
            "above_sma_200": ma_signals[2] > 0,
            "golden_cross": golden_cross,
            "death_cross": death_cross,
        }
