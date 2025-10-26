"""
🌙 Moon Dev's Correlation Matrix Agent
Discovers hidden correlations across assets

Implements correlation analysis:
- Rolling correlation matrices (30, 90, 180 days)
- Correlation change detection
- Time-lagged correlation analysis
- Non-linear relationship detection (mutual information)
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from termcolor import cprint

from src.agents.quant.base_quant_agent import BaseQuantAgent
from src.agents.quant.statistical_utils import (
    calculate_correlation,
    calculate_correlation_pvalue,
    correlation_significance_test,
    calculate_mutual_information
)
from src.core.models import Event, EventType
from src.config import (
    CORRELATION_WINDOWS_DAYS,
    CORRELATION_CHANGE_THRESHOLD,
    CORRELATION_CHANGE_LOOKBACK_DAYS,
    CORRELATION_LAG_MIN_MINUTES,
    CORRELATION_LAG_MAX_HOURS,
    CORRELATION_LAG_INCREMENT_MINUTES
)


class CorrelationMatrixAgent(BaseQuantAgent):
    """Analyzes correlations between assets."""
    
    def __init__(self):
        super().__init__(
            agent_type="correlation_matrix",
            subscribed_topics=["price.tick"]
        )
        
        # Price history per token
        self.price_history: Dict[str, List[float]] = {}
        self.timestamp_history: Dict[str, List[datetime]] = {}
        
        # Correlation matrices (window_days -> token_pair -> correlation)
        self.correlation_matrices: Dict[int, Dict[str, float]] = {
            window: {} for window in CORRELATION_WINDOWS_DAYS
        }
        
        # Historical correlations for change detection
        self.correlation_history: Dict[str, List[Tuple[datetime, float]]] = {}
        
        cprint("✅ Correlation Matrix Agent initialized", "green")
    
    async def handle_price_tick(self, event: Event):
        """Update correlation matrix from price tick."""
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
        
        # Trim old data (keep max window + buffer)
        max_window = max(CORRELATION_WINDOWS_DAYS)
        cutoff = datetime.utcnow() - timedelta(days=max_window * 2)
        
        valid_indices = [i for i, ts in enumerate(self.timestamp_history[token]) if ts > cutoff]
        self.price_history[token] = [self.price_history[token][i] for i in valid_indices]
        self.timestamp_history[token] = [self.timestamp_history[token][i] for i in valid_indices]
        
        # Update correlations periodically (every 100 ticks)
        if len(self.price_history[token]) % 100 == 0:
            await self._update_correlations()
    
    async def _update_correlations(self):
        """Update correlation matrices for all windows."""
        tokens = list(self.price_history.keys())
        
        if len(tokens) < 2:
            return
        
        for window_days in CORRELATION_WINDOWS_DAYS:
            await self._calculate_correlations_for_window(tokens, window_days)
    
    async def _calculate_correlations_for_window(self, tokens: List[str], window_days: int):
        """Calculate correlations for a specific window."""
        cutoff = datetime.utcnow() - timedelta(days=window_days)
        
        for i, token1 in enumerate(tokens):
            for token2 in tokens[i+1:]:
                # Get aligned price data
                prices1, prices2 = self._align_prices(token1, token2, cutoff)
                
                if len(prices1) < 10:
                    continue
                
                # Calculate correlation
                corr, p_value = calculate_correlation_pvalue(prices1, prices2)
                
                # Store in matrix
                pair_key = f"{min(token1, token2)}_{max(token1, token2)}"
                self.correlation_matrices[window_days][pair_key] = corr
                
                # Check for significant changes
                await self._check_correlation_change(pair_key, token1, token2, corr, window_days)
                
                # Calculate mutual information for non-linear relationships
                if window_days == CORRELATION_WINDOWS_DAYS[0]:  # Only for shortest window
                    mi = calculate_mutual_information(prices1, prices2)
                    
                    # Detect non-linear relationships (MI > correlation)
                    if mi > abs(corr) + 0.2:
                        await self.emit_event(
                            event_type=EventType.SIGNAL_CORRELATION,
                            token=token1,
                            data={
                                "correlation_type": "non_linear",
                                "token_1": token1,
                                "token_2": token2,
                                "correlation": float(corr),
                                "mutual_information": float(mi),
                                "window_days": window_days
                            }
                        )
    
    def _align_prices(self, token1: str, token2: str, cutoff: datetime) -> Tuple[List[float], List[float]]:
        """Align price data for two tokens."""
        # Get prices after cutoff
        indices1 = [i for i, ts in enumerate(self.timestamp_history[token1]) if ts > cutoff]
        indices2 = [i for i, ts in enumerate(self.timestamp_history[token2]) if ts > cutoff]
        
        prices1 = [self.price_history[token1][i] for i in indices1]
        prices2 = [self.price_history[token2][i] for i in indices2]
        
        # Align lengths
        min_len = min(len(prices1), len(prices2))
        return prices1[-min_len:], prices2[-min_len:]
    
    async def _check_correlation_change(self, pair_key: str, token1: str, token2: str, current_corr: float, window_days: int):
        """Check for significant correlation changes."""
        # Initialize history if needed
        if pair_key not in self.correlation_history:
            self.correlation_history[pair_key] = []
        
        # Add current correlation
        self.correlation_history[pair_key].append((datetime.utcnow(), current_corr))
        
        # Keep only recent history
        cutoff = datetime.utcnow() - timedelta(days=CORRELATION_CHANGE_LOOKBACK_DAYS * 2)
        self.correlation_history[pair_key] = [
            (ts, corr) for ts, corr in self.correlation_history[pair_key] if ts > cutoff
        ]
        
        # Check for change
        if len(self.correlation_history[pair_key]) < 2:
            return
        
        # Get correlation from lookback period
        lookback_cutoff = datetime.utcnow() - timedelta(days=CORRELATION_CHANGE_LOOKBACK_DAYS)
        past_corrs = [corr for ts, corr in self.correlation_history[pair_key] if ts < lookback_cutoff]
        
        if not past_corrs:
            return
        
        previous_corr = past_corrs[-1]
        corr_change = abs(current_corr - previous_corr)
        
        if corr_change > CORRELATION_CHANGE_THRESHOLD:
            # Test statistical significance
            z_stat, is_significant = correlation_significance_test(previous_corr, current_corr, len(past_corrs))
            
            if is_significant:
                await self.emit_event(
                    event_type=EventType.SIGNAL_CORRELATION,
                    token=token1,
                    data={
                        "correlation_type": "change_detected",
                        "token_1": token1,
                        "token_2": token2,
                        "current_correlation": float(current_corr),
                        "previous_correlation": float(previous_corr),
                        "correlation_change": float(corr_change),
                        "z_statistic": float(z_stat),
                        "window_days": window_days
                    }
                )
                
                cprint(f"🔔 Correlation change: {token1}-{token2} {previous_corr:.2f} → {current_corr:.2f}", "yellow")
    
    async def run_event_loop(self):
        """Override to register event handlers."""
        self._event_handlers[EventType.PRICE_TICK] = self.handle_price_tick
        await super().run_event_loop()


if __name__ == "__main__":
    agent = CorrelationMatrixAgent()
    agent.run()
