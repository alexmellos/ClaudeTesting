"""Signal generation module combining all analysis types."""
from typing import Dict, Any, List
from .technical import TechnicalAnalyzer
from .fundamentals import FundamentalsAnalyzer
import pandas as pd


class SignalGenerator:
    """Generates trading signals based on multiple analysis types."""

    def __init__(
        self,
        technical_analyzer: TechnicalAnalyzer,
        fundamentals_analyzer: FundamentalsAnalyzer,
        news_sentiment: Dict[str, Any]
    ):
        self.technical = technical_analyzer
        self.fundamentals = fundamentals_analyzer
        self.sentiment = news_sentiment

    def generate_signals(self) -> Dict[str, Any]:
        """Generate comprehensive trading signals."""
        technical_signals = self._generate_technical_signals()
        fundamental_signals = self._generate_fundamental_signals()
        sentiment_signals = self._generate_sentiment_signals()

        # Combine all signals
        combined = self._combine_signals(
            technical_signals,
            fundamental_signals,
            sentiment_signals
        )

        return {
            "technical": technical_signals,
            "fundamental": fundamental_signals,
            "sentiment": sentiment_signals,
            "combined": combined,
            "action_recommendation": self._get_action_recommendation(combined)
        }

    def _generate_technical_signals(self) -> Dict[str, Any]:
        """Generate signals from technical analysis."""
        indicators = self.technical.get_latest_indicators()
        trend = self.technical.get_trend_analysis()

        signals = []
        score = 0

        # RSI signals
        momentum = indicators.get('momentum', {})
        rsi = momentum.get('rsi')
        if rsi is not None:
            if rsi < 30:
                signals.append({
                    "indicator": "RSI",
                    "signal": "oversold",
                    "value": rsi,
                    "action": "buy",
                    "strength": 0.8
                })
                score += 0.8
            elif rsi > 70:
                signals.append({
                    "indicator": "RSI",
                    "signal": "overbought",
                    "value": rsi,
                    "action": "sell",
                    "strength": 0.8
                })
                score -= 0.8
            elif 30 <= rsi <= 40:
                signals.append({
                    "indicator": "RSI",
                    "signal": "approaching_oversold",
                    "value": rsi,
                    "action": "watch_buy",
                    "strength": 0.3
                })
                score += 0.3
            elif 60 <= rsi <= 70:
                signals.append({
                    "indicator": "RSI",
                    "signal": "approaching_overbought",
                    "value": rsi,
                    "action": "watch_sell",
                    "strength": 0.3
                })
                score -= 0.3

        # MACD signals
        macd = momentum.get('macd')
        macd_signal = momentum.get('macd_signal')
        macd_histogram = momentum.get('macd_histogram')

        if macd is not None and macd_signal is not None:
            if macd > macd_signal and macd_histogram > 0:
                signals.append({
                    "indicator": "MACD",
                    "signal": "bullish",
                    "value": macd_histogram,
                    "action": "buy",
                    "strength": 0.6
                })
                score += 0.6
            elif macd < macd_signal and macd_histogram < 0:
                signals.append({
                    "indicator": "MACD",
                    "signal": "bearish",
                    "value": macd_histogram,
                    "action": "sell",
                    "strength": 0.6
                })
                score -= 0.6

        # Moving Average signals
        if trend.get('above_sma_20') and trend.get('above_sma_50'):
            signals.append({
                "indicator": "Moving Averages",
                "signal": "bullish_trend",
                "action": "buy",
                "strength": 0.5
            })
            score += 0.5
        elif not trend.get('above_sma_20') and not trend.get('above_sma_50'):
            signals.append({
                "indicator": "Moving Averages",
                "signal": "bearish_trend",
                "action": "sell",
                "strength": 0.5
            })
            score -= 0.5

        # Golden/Death cross
        if trend.get('golden_cross'):
            signals.append({
                "indicator": "MA Cross",
                "signal": "golden_cross",
                "action": "strong_buy",
                "strength": 0.9
            })
            score += 0.9
        elif trend.get('death_cross'):
            signals.append({
                "indicator": "MA Cross",
                "signal": "death_cross",
                "action": "strong_sell",
                "strength": 0.9
            })
            score -= 0.9

        # Bollinger Bands
        volatility = indicators.get('volatility', {})
        bb_position = volatility.get('bb_position')
        if bb_position is not None:
            if bb_position < 0.1:
                signals.append({
                    "indicator": "Bollinger Bands",
                    "signal": "near_lower_band",
                    "value": bb_position,
                    "action": "buy",
                    "strength": 0.5
                })
                score += 0.5
            elif bb_position > 0.9:
                signals.append({
                    "indicator": "Bollinger Bands",
                    "signal": "near_upper_band",
                    "value": bb_position,
                    "action": "sell",
                    "strength": 0.5
                })
                score -= 0.5

        # Stochastic
        stoch_k = momentum.get('stoch_k')
        stoch_d = momentum.get('stoch_d')
        if stoch_k is not None:
            if stoch_k < 20:
                signals.append({
                    "indicator": "Stochastic",
                    "signal": "oversold",
                    "value": stoch_k,
                    "action": "buy",
                    "strength": 0.5
                })
                score += 0.5
            elif stoch_k > 80:
                signals.append({
                    "indicator": "Stochastic",
                    "signal": "overbought",
                    "value": stoch_k,
                    "action": "sell",
                    "strength": 0.5
                })
                score -= 0.5

        # Normalize score
        max_possible = 4.3  # Sum of all possible positive strengths
        normalized_score = score / max_possible if max_possible > 0 else 0

        return {
            "signals": signals,
            "score": round(normalized_score, 2),
            "trend": trend.get('trend', 'neutral'),
            "signal_count": len(signals),
            "overall": "bullish" if normalized_score > 0.2 else "bearish" if normalized_score < -0.2 else "neutral"
        }

    def _generate_fundamental_signals(self) -> Dict[str, Any]:
        """Generate signals from fundamental analysis."""
        analysis = self.fundamentals.analyze()

        signals = []
        overall_score = analysis['overall_score']['score']

        # Valuation signal
        valuation = analysis['valuation']
        if valuation['assessment'] == 'undervalued':
            signals.append({
                "indicator": "Valuation",
                "signal": "undervalued",
                "action": "buy",
                "strength": 0.7
            })
        elif valuation['assessment'] == 'overvalued':
            signals.append({
                "indicator": "Valuation",
                "signal": "overvalued",
                "action": "sell",
                "strength": 0.7
            })

        # Growth signal
        growth = analysis['growth']
        if growth['assessment'] == 'growing':
            signals.append({
                "indicator": "Growth",
                "signal": "positive_growth",
                "action": "buy",
                "strength": 0.6
            })
        elif growth['assessment'] == 'declining':
            signals.append({
                "indicator": "Growth",
                "signal": "negative_growth",
                "action": "sell",
                "strength": 0.6
            })

        # Analyst signal
        analyst = analysis['analyst_ratings']
        if analyst['assessment'] == 'bullish':
            signals.append({
                "indicator": "Analyst Ratings",
                "signal": "bullish",
                "action": "buy",
                "strength": 0.5
            })
        elif analyst['assessment'] == 'bearish':
            signals.append({
                "indicator": "Analyst Ratings",
                "signal": "bearish",
                "action": "sell",
                "strength": 0.5
            })

        return {
            "signals": signals,
            "score": overall_score,
            "overall": analysis['overall_score']['assessment'],
            "signal_count": len(signals)
        }

    def _generate_sentiment_signals(self) -> Dict[str, Any]:
        """Generate signals from news sentiment."""
        signals = []

        overall_sentiment = self.sentiment.get('overall_sentiment', 'neutral')
        avg_score = self.sentiment.get('average_score', 0)
        news_count = self.sentiment.get('news_count', 0)

        if news_count < 3:
            return {
                "signals": [],
                "score": 0,
                "overall": "insufficient_data",
                "signal_count": 0
            }

        if overall_sentiment == 'positive' and avg_score > 0.2:
            signals.append({
                "indicator": "News Sentiment",
                "signal": "strongly_positive",
                "value": avg_score,
                "action": "buy",
                "strength": 0.6
            })
        elif overall_sentiment == 'positive':
            signals.append({
                "indicator": "News Sentiment",
                "signal": "positive",
                "value": avg_score,
                "action": "buy",
                "strength": 0.3
            })
        elif overall_sentiment == 'negative' and avg_score < -0.2:
            signals.append({
                "indicator": "News Sentiment",
                "signal": "strongly_negative",
                "value": avg_score,
                "action": "sell",
                "strength": 0.6
            })
        elif overall_sentiment == 'negative':
            signals.append({
                "indicator": "News Sentiment",
                "signal": "negative",
                "value": avg_score,
                "action": "sell",
                "strength": 0.3
            })

        # Sentiment score normalized
        sentiment_score = avg_score  # Already between -1 and 1

        return {
            "signals": signals,
            "score": round(sentiment_score, 2),
            "overall": overall_sentiment,
            "news_count": news_count,
            "signal_count": len(signals)
        }

    def _combine_signals(
        self,
        technical: Dict[str, Any],
        fundamental: Dict[str, Any],
        sentiment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine all signals with weighted scoring."""
        # Weights for different signal types (for short-term trading)
        weights = {
            'technical': 0.5,    # Most important for short-term
            'fundamental': 0.25,  # Still relevant
            'sentiment': 0.25    # News can move stocks quickly
        }

        combined_score = (
            technical['score'] * weights['technical'] +
            fundamental['score'] * weights['fundamental'] +
            sentiment['score'] * weights['sentiment']
        )

        # Count buy vs sell signals
        all_signals = (
            technical['signals'] +
            fundamental['signals'] +
            sentiment['signals']
        )

        buy_signals = sum(1 for s in all_signals if 'buy' in s.get('action', ''))
        sell_signals = sum(1 for s in all_signals if 'sell' in s.get('action', ''))

        return {
            "combined_score": round(combined_score, 2),
            "total_signals": len(all_signals),
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "signal_ratio": round(buy_signals / sell_signals, 2) if sell_signals > 0 else buy_signals,
            "component_scores": {
                "technical": technical['score'],
                "fundamental": fundamental['score'],
                "sentiment": sentiment['score']
            }
        }

    def _get_action_recommendation(self, combined: Dict[str, Any]) -> Dict[str, Any]:
        """Get final action recommendation."""
        score = combined['combined_score']
        buy_signals = combined['buy_signals']
        sell_signals = combined['sell_signals']
        total = combined['total_signals']

        # Determine action
        if score > 0.4 and buy_signals > sell_signals:
            action = "STRONG_BUY"
            confidence = min(0.9, 0.5 + score)
        elif score > 0.2 and buy_signals >= sell_signals:
            action = "BUY"
            confidence = min(0.75, 0.4 + score)
        elif score < -0.4 and sell_signals > buy_signals:
            action = "STRONG_SELL"
            confidence = min(0.9, 0.5 + abs(score))
        elif score < -0.2 and sell_signals >= buy_signals:
            action = "SELL"
            confidence = min(0.75, 0.4 + abs(score))
        else:
            action = "HOLD"
            confidence = 0.5

        # Risk assessment
        if abs(score) < 0.1 and total < 5:
            risk = "high"
            risk_note = "Low signal count and weak signals"
        elif abs(score) > 0.3 and buy_signals > 0 and sell_signals > 0:
            risk = "medium"
            risk_note = "Mixed signals present"
        elif abs(score) > 0.4:
            risk = "low"
            risk_note = "Strong consensus among signals"
        else:
            risk = "medium"
            risk_note = "Moderate signal strength"

        return {
            "action": action,
            "confidence": round(confidence, 2),
            "risk_level": risk,
            "risk_note": risk_note,
            "reasoning": f"{buy_signals} buy signals vs {sell_signals} sell signals, combined score: {score}"
        }
