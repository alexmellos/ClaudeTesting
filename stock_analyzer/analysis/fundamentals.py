"""Fundamental analysis module."""
from typing import Dict, Any, Optional
import config


class FundamentalsAnalyzer:
    """Analyzes fundamental metrics for stock evaluation."""

    def __init__(self, stock_info: Dict[str, Any]):
        """Initialize with stock info data."""
        self.info = stock_info

    def analyze(self) -> Dict[str, Any]:
        """Perform comprehensive fundamental analysis."""
        return {
            "valuation": self._analyze_valuation(),
            "profitability": self._analyze_profitability(),
            "growth": self._analyze_growth(),
            "analyst_ratings": self._analyze_analyst_ratings(),
            "risk_metrics": self._analyze_risk(),
            "overall_score": self._calculate_overall_score(),
        }

    def _analyze_valuation(self) -> Dict[str, Any]:
        """Analyze valuation metrics."""
        pe_ratio = self.info.get('pe_ratio')
        forward_pe = self.info.get('forward_pe')
        peg_ratio = self.info.get('peg_ratio')
        price_to_book = self.info.get('price_to_book')

        # Valuation assessment
        valuation_signals = []

        if pe_ratio is not None:
            if pe_ratio < 15:
                valuation_signals.append(("pe_ratio", "undervalued", 1))
            elif pe_ratio < 25:
                valuation_signals.append(("pe_ratio", "fair", 0))
            else:
                valuation_signals.append(("pe_ratio", "overvalued", -1))

        if peg_ratio is not None:
            if peg_ratio < 1:
                valuation_signals.append(("peg_ratio", "attractive", 1))
            elif peg_ratio < 2:
                valuation_signals.append(("peg_ratio", "fair", 0))
            else:
                valuation_signals.append(("peg_ratio", "expensive", -1))

        if price_to_book is not None:
            if price_to_book < 1:
                valuation_signals.append(("price_to_book", "undervalued", 1))
            elif price_to_book < 3:
                valuation_signals.append(("price_to_book", "fair", 0))
            else:
                valuation_signals.append(("price_to_book", "premium", -1))

        # Calculate valuation score
        if valuation_signals:
            score = sum(s[2] for s in valuation_signals) / len(valuation_signals)
        else:
            score = 0

        return {
            "pe_ratio": pe_ratio,
            "forward_pe": forward_pe,
            "peg_ratio": peg_ratio,
            "price_to_book": price_to_book,
            "signals": valuation_signals,
            "score": round(score, 2),
            "assessment": "undervalued" if score > 0.3 else "overvalued" if score < -0.3 else "fair"
        }

    def _analyze_profitability(self) -> Dict[str, Any]:
        """Analyze profitability metrics."""
        profit_margins = self.info.get('profit_margins')
        eps = self.info.get('eps')

        signals = []

        if profit_margins is not None:
            if profit_margins > 0.2:
                signals.append(("profit_margins", "excellent", 1))
            elif profit_margins > 0.1:
                signals.append(("profit_margins", "good", 0.5))
            elif profit_margins > 0:
                signals.append(("profit_margins", "low", 0))
            else:
                signals.append(("profit_margins", "negative", -1))

        if eps is not None:
            if eps > 0:
                signals.append(("eps", "positive", 1))
            else:
                signals.append(("eps", "negative", -1))

        score = sum(s[2] for s in signals) / len(signals) if signals else 0

        return {
            "profit_margins": profit_margins,
            "eps": eps,
            "signals": signals,
            "score": round(score, 2),
            "assessment": "profitable" if score > 0 else "unprofitable"
        }

    def _analyze_growth(self) -> Dict[str, Any]:
        """Analyze growth metrics."""
        revenue_growth = self.info.get('revenue_growth')
        earnings_growth = self.info.get('earnings_growth')

        signals = []

        if revenue_growth is not None:
            if revenue_growth > 0.2:
                signals.append(("revenue_growth", "high_growth", 1))
            elif revenue_growth > 0.1:
                signals.append(("revenue_growth", "moderate_growth", 0.5))
            elif revenue_growth > 0:
                signals.append(("revenue_growth", "slow_growth", 0))
            else:
                signals.append(("revenue_growth", "declining", -1))

        if earnings_growth is not None:
            if earnings_growth > 0.2:
                signals.append(("earnings_growth", "high_growth", 1))
            elif earnings_growth > 0.1:
                signals.append(("earnings_growth", "moderate_growth", 0.5))
            elif earnings_growth > 0:
                signals.append(("earnings_growth", "slow_growth", 0))
            else:
                signals.append(("earnings_growth", "declining", -1))

        score = sum(s[2] for s in signals) / len(signals) if signals else 0

        return {
            "revenue_growth": revenue_growth,
            "earnings_growth": earnings_growth,
            "signals": signals,
            "score": round(score, 2),
            "assessment": "growing" if score > 0.3 else "declining" if score < -0.3 else "stable"
        }

    def _analyze_analyst_ratings(self) -> Dict[str, Any]:
        """Analyze analyst recommendations."""
        recommendation = self.info.get('recommendation', 'N/A')
        target_price = self.info.get('target_mean_price')
        current_price = self.info.get('current_price', 0)
        analyst_count = self.info.get('analyst_count', 0)

        # Calculate upside potential
        upside = None
        if target_price and current_price and current_price > 0:
            upside = ((target_price - current_price) / current_price) * 100

        # Score based on recommendation
        rec_scores = {
            'strongBuy': 1,
            'buy': 0.5,
            'hold': 0,
            'sell': -0.5,
            'strongSell': -1
        }
        rec_score = rec_scores.get(recommendation, 0)

        # Adjust score based on upside
        if upside is not None:
            if upside > 20:
                upside_score = 1
            elif upside > 10:
                upside_score = 0.5
            elif upside > 0:
                upside_score = 0
            else:
                upside_score = -0.5
        else:
            upside_score = 0

        combined_score = (rec_score + upside_score) / 2

        return {
            "recommendation": recommendation,
            "target_price": target_price,
            "current_price": current_price,
            "upside_percent": round(upside, 2) if upside else None,
            "analyst_count": analyst_count,
            "score": round(combined_score, 2),
            "assessment": "bullish" if combined_score > 0.3 else "bearish" if combined_score < -0.3 else "neutral"
        }

    def _analyze_risk(self) -> Dict[str, Any]:
        """Analyze risk metrics."""
        beta = self.info.get('beta')
        fifty_two_week_high = self.info.get('fifty_two_week_high', 0)
        fifty_two_week_low = self.info.get('fifty_two_week_low', 0)
        current_price = self.info.get('current_price', 0)

        # Calculate distance from 52-week high/low
        distance_from_high = None
        distance_from_low = None

        if fifty_two_week_high and current_price:
            distance_from_high = ((current_price - fifty_two_week_high) / fifty_two_week_high) * 100

        if fifty_two_week_low and current_price:
            distance_from_low = ((current_price - fifty_two_week_low) / fifty_two_week_low) * 100

        # Volatility assessment
        if fifty_two_week_high and fifty_two_week_low and fifty_two_week_low > 0:
            volatility_range = ((fifty_two_week_high - fifty_two_week_low) / fifty_two_week_low) * 100
        else:
            volatility_range = None

        # Risk score based on beta
        if beta is not None:
            if beta > 1.5:
                risk_level = "high"
                risk_score = -1
            elif beta > 1:
                risk_level = "moderate"
                risk_score = 0
            else:
                risk_level = "low"
                risk_score = 1
        else:
            risk_level = "unknown"
            risk_score = 0

        return {
            "beta": beta,
            "risk_level": risk_level,
            "fifty_two_week_high": fifty_two_week_high,
            "fifty_two_week_low": fifty_two_week_low,
            "distance_from_high_percent": round(distance_from_high, 2) if distance_from_high else None,
            "distance_from_low_percent": round(distance_from_low, 2) if distance_from_low else None,
            "volatility_range_percent": round(volatility_range, 2) if volatility_range else None,
            "score": risk_score
        }

    def _calculate_overall_score(self) -> Dict[str, Any]:
        """Calculate an overall fundamental score."""
        valuation = self._analyze_valuation()
        profitability = self._analyze_profitability()
        growth = self._analyze_growth()
        analyst = self._analyze_analyst_ratings()
        risk = self._analyze_risk()

        # Weighted average of scores
        weights = {
            'valuation': 0.25,
            'profitability': 0.2,
            'growth': 0.25,
            'analyst': 0.2,
            'risk': 0.1
        }

        scores = {
            'valuation': valuation['score'],
            'profitability': profitability['score'],
            'growth': growth['score'],
            'analyst': analyst['score'],
            'risk': risk['score']
        }

        overall = sum(scores[k] * weights[k] for k in weights)

        if overall > 0.3:
            assessment = "strong_buy"
        elif overall > 0.1:
            assessment = "buy"
        elif overall > -0.1:
            assessment = "hold"
        elif overall > -0.3:
            assessment = "sell"
        else:
            assessment = "strong_sell"

        return {
            "score": round(overall, 2),
            "assessment": assessment,
            "component_scores": scores
        }
