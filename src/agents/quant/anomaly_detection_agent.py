"""
🌙 Moon Dev's Anomaly Detection Agent
Detects statistically significant market anomalies

Implements Jim Simons-style anomaly detection:
- Mean reversion detection (z-score based)
- Correlation anomaly detection
- Autocorrelation pattern detection
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from termcolor import cprint

from src.agents.quant.base_quant_agent import BaseQuantAgent
from src.agents.quant.statistical_utils import (
    calculate_zscore, rolling_mean, rolling_std,
    calculate_correlation, calculate_correlation_pvalue,
    calculate_autocorrelation, ttest_significance
)
from src.core.models import Event, EventType
from src.config import (
    ANOMALY_DETECTION_WINDOW_DAYS,
    ANOMALY_DETECTION_SIGMA_THRESHOLD,
    ANOMALY_DETECTION_P_VALUE_THRESHOLD,
    ANOMALY_CORRELATION_CHANGE_THRESHOLD,
    ANOMALY_CORRELATION_WINDOW_DAYS
)


class AnomalyDetectionAgent(BaseQuantAgent):
    """Detects statistical anomalies in market data."""
    
    def __init__(self):
        super().__init__(
            agent_type="anomaly_detection",
            subscribed_topics=["price.tick"]
        )
        
        # Price history buffers (token -> list of prices)
        self.price_history: Dict[str, List[float]] = {}
        self.timestamp_history: Dict[str, List[datetime]] = {}
        
        # Correlation tracking (token_pair -> correlation)
        self.correlation_history: Dict[str, List[float]] = {}
        
        cprint("✅ Anomaly Detection Agent initialized", "green")

    async def handle_price_tick(self, event: Event):
        """Handle incoming price tick events."""
        token = event.token
        price = event.data.get('price')
        
        if not token or not price:
            return
        
        # Update price history
        if token not in self.price_history:
            self.price_history[token] = []
            self.timestamp_history[token] = []
        
        self.price_history[token].append(price)
        self.timestamp_history[token].append(event.timestamp)
        
        # Keep only last N days of data
        await self._trim_history(token)
        
        # Run anomaly detection
        await self.detect_mean_reversion_anomaly(token)
        await self.detect_correlation_anomalies(token)
        await self.detect_autocorrelation_patterns(token)
    
    async def _trim_history(self, token: str):
        """Trim history to keep only recent data."""
        if token not in self.timestamp_history:
            return
        
        cutoff_time = datetime.utcnow() - timedelta(days=ANOMALY_DETECTION_WINDOW_DAYS * 2)
        
        # Find index to trim from
        timestamps = self.timestamp_history[token]
        trim_idx = 0
        for i, ts in enumerate(timestamps):
            if ts > cutoff_time:
                trim_idx = i
                break
        
        # Trim both lists
        if trim_idx > 0:
            self.price_history[token] = self.price_history[token][trim_idx:]
            self.timestamp_history[token] = self.timestamp_history[token][trim_idx:]

    async def detect_mean_reversion_anomaly(self, token: str):
        """Detect mean reversion anomalies using z-score."""
        prices = self.price_history.get(token, [])
        
        if len(prices) < ANOMALY_DETECTION_WINDOW_DAYS:
            return
        
        # Calculate rolling statistics
        window = min(ANOMALY_DETECTION_WINDOW_DAYS, len(prices))
        recent_prices = prices[-window:]
        
        mean = np.mean(recent_prices)
        std = np.std(recent_prices)
        current_price = prices[-1]
        
        # Calculate z-score
        z_score = calculate_zscore(current_price, mean, std)
        
        # Check if anomaly (> threshold sigma)
        if abs(z_score) > ANOMALY_DETECTION_SIGMA_THRESHOLD:
            # Perform statistical significance test
            returns = np.diff(recent_prices) / recent_prices[:-1]
            t_stat, p_value = ttest_significance(returns)
            
            if p_value < ANOMALY_DETECTION_P_VALUE_THRESHOLD:
                # Emit anomaly event
                await self.emit_event(
                    event_type=EventType.SIGNAL_ANOMALY,
                    token=token,
                    data={
                        "anomaly_type": "mean_reversion",
                        "z_score": float(z_score),
                        "current_price": float(current_price),
                        "mean": float(mean),
                        "std": float(std),
                        "p_value": float(p_value),
                        "t_statistic": float(t_stat),
                        "direction": "above" if z_score > 0 else "below",
                        "confidence": 1 - p_value
                    }
                )
                
                cprint(f"🔔 Mean reversion anomaly detected for {token}: z={z_score:.2f}, p={p_value:.4f}", "yellow")

    async def detect_correlation_anomalies(self, token: str):
        """Detect correlation anomalies between token pairs."""
        # Get all tokens with sufficient history
        tokens_with_history = [
            t for t in self.price_history.keys()
            if len(self.price_history[t]) >= ANOMALY_CORRELATION_WINDOW_DAYS
        ]
        
        if token not in tokens_with_history or len(tokens_with_history) < 2:
            return
        
        # Check correlations with other tokens
        for other_token in tokens_with_history:
            if other_token == token:
                continue
            
            pair_key = f"{min(token, other_token)}_{max(token, other_token)}"
            
            # Get aligned price data
            prices1 = self.price_history[token][-ANOMALY_CORRELATION_WINDOW_DAYS:]
            prices2 = self.price_history[other_token][-ANOMALY_CORRELATION_WINDOW_DAYS:]
            
            # Align lengths
            min_len = min(len(prices1), len(prices2))
            prices1 = prices1[-min_len:]
            prices2 = prices2[-min_len:]
            
            if min_len < 7:
                continue
            
            # Calculate current correlation
            current_corr, p_value = calculate_correlation_pvalue(prices1, prices2)
            
            # Initialize history if needed
            if pair_key not in self.correlation_history:
                self.correlation_history[pair_key] = []
            
            # Store correlation
            self.correlation_history[pair_key].append(current_corr)
            
            # Keep only recent history
            if len(self.correlation_history[pair_key]) > ANOMALY_CORRELATION_WINDOW_DAYS:
                self.correlation_history[pair_key] = self.correlation_history[pair_key][-ANOMALY_CORRELATION_WINDOW_DAYS:]
            
            # Check for correlation change
            if len(self.correlation_history[pair_key]) >= 2:
                prev_corr = self.correlation_history[pair_key][-2]
                corr_change = abs(current_corr - prev_corr)
                
                if corr_change > ANOMALY_CORRELATION_CHANGE_THRESHOLD:
                    # Emit correlation anomaly event
                    await self.emit_event(
                        event_type=EventType.SIGNAL_CORRELATION,
                        token=token,
                        data={
                            "anomaly_type": "correlation_change",
                            "token_1": token,
                            "token_2": other_token,
                            "current_correlation": float(current_corr),
                            "previous_correlation": float(prev_corr),
                            "correlation_change": float(corr_change),
                            "p_value": float(p_value),
                            "window_days": ANOMALY_CORRELATION_WINDOW_DAYS
                        }
                    )
                    
                    cprint(f"🔔 Correlation anomaly: {token}-{other_token} changed by {corr_change:.2f}", "yellow")

    async def detect_autocorrelation_patterns(self, token: str):
        """Detect autocorrelation patterns (momentum vs mean-reversion)."""
        prices = self.price_history.get(token, [])
        
        if len(prices) < 20:
            return
        
        # Calculate returns
        returns = np.diff(prices) / prices[:-1]
        
        if len(returns) < 10:
            return
        
        # Calculate autocorrelation
        acf = calculate_autocorrelation(returns, max_lags=min(10, len(returns) - 1))
        
        # Check first lag (most important)
        lag1_acf = acf[1] if len(acf) > 1 else 0
        
        # Calculate confidence interval (95%)
        conf_interval = 1.96 / np.sqrt(len(returns))
        
        # Detect significant autocorrelation
        if abs(lag1_acf) > conf_interval:
            regime = "momentum" if lag1_acf > 0 else "mean_reversion"
            
            # Emit autocorrelation pattern event
            await self.emit_event(
                event_type=EventType.SIGNAL_ANOMALY,
                token=token,
                data={
                    "anomaly_type": "autocorrelation_pattern",
                    "regime": regime,
                    "lag1_acf": float(lag1_acf),
                    "confidence_interval": float(conf_interval),
                    "significance": abs(lag1_acf) / conf_interval,
                    "acf_values": [float(x) for x in acf[:5]]
                }
            )
            
            cprint(f"🔔 Autocorrelation pattern for {token}: {regime} (ACF={lag1_acf:.3f})", "yellow")
    
    async def run_event_loop(self):
        """Override to register event handlers."""
        # Register event handlers
        self._event_handlers[EventType.PRICE_TICK] = self.handle_price_tick
        
        # Run parent event loop
        await super().run_event_loop()


# Entry point for running agent standalone
if __name__ == "__main__":
    agent = AnomalyDetectionAgent()
    agent.run()
