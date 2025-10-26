"""
🌙 Moon Dev's Regime Detection Agent
Identifies distinct market regimes

Implements regime detection:
- Volatility regime (high/low/normal)
- Trend regime (trending/mean-reverting/neutral)
- Liquidity regime (liquid/normal/illiquid)
- Regime persistence (4-hour minimum)
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from termcolor import cprint

from src.agents.quant.base_quant_agent import BaseQuantAgent
from src.core.models import Event, EventType
from src.config import (
    REGIME_VOLATILITY_HIGH_MULTIPLIER,
    REGIME_VOLATILITY_LOW_MULTIPLIER,
    REGIME_VOLATILITY_WINDOW_DAYS,
    REGIME_TREND_ADX_TRENDING_THRESHOLD,
    REGIME_TREND_ADX_MEANREV_THRESHOLD,
    REGIME_LIQUIDITY_LIQUID_SPREAD_PCT,
    REGIME_LIQUIDITY_ILLIQUID_SPREAD_PCT,
    REGIME_MIN_PERSISTENCE_HOURS
)


@dataclass
class MarketRegime:
    """Market regime state for a token."""
    token: str
    volatility_regime: str = "normal"  # high, low, normal
    trend_regime: str = "neutral"  # trending, mean_reverting, neutral
    liquidity_regime: str = "normal"  # liquid, normal, illiquid
    regime_start: Optional[datetime] = None
    confidence: float = 0.0
    
    # Historical data
    price_history: List[float] = None
    timestamp_history: List[datetime] = None
    
    def __post_init__(self):
        if self.price_history is None:
            self.price_history = []
        if self.timestamp_history is None:
            self.timestamp_history = []


class RegimeDetectionAgent(BaseQuantAgent):
    """Detects market regime changes."""
    
    def __init__(self):
        super().__init__(
            agent_type="regime_detection",
            subscribed_topics=["price.tick"]
        )
        
        # Regime state per token
        self.regimes: Dict[str, MarketRegime] = {}
        
        # Pending regime changes (need persistence)
        self.pending_regime_changes: Dict[str, Dict] = {}
        
        cprint("✅ Regime Detection Agent initialized", "green")

    
    async def handle_price_tick(self, event: Event):
        """Analyze market regime from price tick."""
        token = event.token
        price = event.data.get('price')
        bid = event.data.get('bid')
        ask = event.data.get('ask')
        
        if not token or not price:
            return
        
        # Initialize regime if needed
        if token not in self.regimes:
            self.regimes[token] = MarketRegime(token=token)
        
        regime = self.regimes[token]
        
        # Update price history
        regime.price_history.append(price)
        regime.timestamp_history.append(event.timestamp)
        
        # Trim old data
        cutoff = datetime.utcnow() - timedelta(days=REGIME_VOLATILITY_WINDOW_DAYS * 2)
        valid_indices = [i for i, ts in enumerate(regime.timestamp_history) if ts > cutoff]
        regime.price_history = [regime.price_history[i] for i in valid_indices]
        regime.timestamp_history = [regime.timestamp_history[i] for i in valid_indices]
        
        # Need sufficient data
        if len(regime.price_history) < 30:
            return
        
        # Detect regimes
        await self._detect_volatility_regime(token, regime)
        await self._detect_trend_regime(token, regime)
        
        if bid and ask:
            await self._detect_liquidity_regime(token, regime, bid, ask)

    
    async def _detect_volatility_regime(self, token: str, regime: MarketRegime):
        """Detect volatility regime (high/low/normal)."""
        prices = np.array(regime.price_history)
        
        # Calculate log returns
        returns = np.diff(np.log(prices))
        
        if len(returns) < 30:
            return
        
        # Calculate realized volatility (annualized)
        realized_vol = np.std(returns) * np.sqrt(252)
        
        # Calculate 30-day rolling average volatility
        window_size = min(30, len(returns))
        rolling_vol = np.std(returns[-window_size:]) * np.sqrt(252)
        avg_vol = np.mean([np.std(returns[max(0, i-window_size):i]) * np.sqrt(252) 
                          for i in range(window_size, len(returns))])
        
        if avg_vol == 0:
            return
        
        # Classify regime
        new_regime = "normal"
        if realized_vol > avg_vol * REGIME_VOLATILITY_HIGH_MULTIPLIER:
            new_regime = "high"
        elif realized_vol < avg_vol * REGIME_VOLATILITY_LOW_MULTIPLIER:
            new_regime = "low"
        
        # Check for regime change
        if new_regime != regime.volatility_regime:
            await self._handle_regime_change(
                token=token,
                regime_type="volatility",
                old_regime=regime.volatility_regime,
                new_regime=new_regime,
                confidence=abs(realized_vol - avg_vol) / avg_vol,
                metrics={"realized_vol": realized_vol, "avg_vol": avg_vol}
            )
    
    async def _detect_trend_regime(self, token: str, regime: MarketRegime):
        """Detect trend regime using ADX."""
        prices = np.array(regime.price_history)
        
        if len(prices) < 14:
            return
        
        # Calculate ADX (simplified version)
        adx = self._calculate_adx(prices)
        
        # Classify regime
        new_regime = "neutral"
        if adx > REGIME_TREND_ADX_TRENDING_THRESHOLD:
            new_regime = "trending"
        elif adx < REGIME_TREND_ADX_MEANREV_THRESHOLD:
            new_regime = "mean_reverting"
        
        # Check for regime change
        if new_regime != regime.trend_regime:
            await self._handle_regime_change(
                token=token,
                regime_type="trend",
                old_regime=regime.trend_regime,
                new_regime=new_regime,
                confidence=adx / 100,
                metrics={"adx": adx}
            )
    
    def _calculate_adx(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate Average Directional Index (simplified)."""
        if len(prices) < period + 1:
            return 0.0
        
        # Calculate directional movement
        high = prices
        low = prices
        
        plus_dm = np.maximum(high[1:] - high[:-1], 0)
        minus_dm = np.maximum(low[:-1] - low[1:], 0)
        
        # Calculate true range
        tr = np.maximum(high[1:] - low[1:], 
                       np.maximum(abs(high[1:] - prices[:-1]),
                                 abs(low[1:] - prices[:-1])))
        
        # Smooth with EMA
        atr = np.mean(tr[-period:])
        
        if atr == 0:
            return 0.0
        
        plus_di = 100 * np.mean(plus_dm[-period:]) / atr
        minus_di = 100 * np.mean(minus_dm[-period:]) / atr
        
        # Calculate DX and ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        adx = dx  # Simplified (should be smoothed)
        
        return float(adx)

    
    async def _detect_liquidity_regime(self, token: str, regime: MarketRegime, bid: float, ask: float):
        """Detect liquidity regime based on bid-ask spread."""
        mid_price = (bid + ask) / 2
        
        if mid_price == 0:
            return
        
        # Calculate spread percentage
        spread_pct = (ask - bid) / mid_price * 100
        
        # Classify regime
        new_regime = "normal"
        if spread_pct < REGIME_LIQUIDITY_LIQUID_SPREAD_PCT:
            new_regime = "liquid"
        elif spread_pct > REGIME_LIQUIDITY_ILLIQUID_SPREAD_PCT:
            new_regime = "illiquid"
        
        # Check for regime change
        if new_regime != regime.liquidity_regime:
            await self._handle_regime_change(
                token=token,
                regime_type="liquidity",
                old_regime=regime.liquidity_regime,
                new_regime=new_regime,
                confidence=1.0 - min(spread_pct / 1.0, 1.0),  # Lower spread = higher confidence
                metrics={"spread_pct": spread_pct, "bid": bid, "ask": ask}
            )
    
    async def _handle_regime_change(
        self,
        token: str,
        regime_type: str,
        old_regime: str,
        new_regime: str,
        confidence: float,
        metrics: Dict
    ):
        """Handle potential regime change with persistence check."""
        change_key = f"{token}_{regime_type}"
        
        # Check if we already have a pending change
        if change_key in self.pending_regime_changes:
            pending = self.pending_regime_changes[change_key]
            
            # Check if still the same regime change
            if pending['new_regime'] == new_regime:
                # Check persistence duration
                duration = (datetime.utcnow() - pending['first_detected']).total_seconds() / 3600
                
                if duration >= REGIME_MIN_PERSISTENCE_HOURS:
                    # Regime change confirmed - emit event
                    await self._emit_regime_change(
                        token=token,
                        regime_type=regime_type,
                        old_regime=old_regime,
                        new_regime=new_regime,
                        confidence=confidence,
                        metrics=metrics,
                        duration_hours=duration
                    )
                    
                    # Update regime state
                    regime = self.regimes[token]
                    if regime_type == "volatility":
                        regime.volatility_regime = new_regime
                    elif regime_type == "trend":
                        regime.trend_regime = new_regime
                    elif regime_type == "liquidity":
                        regime.liquidity_regime = new_regime
                    
                    regime.regime_start = datetime.utcnow()
                    regime.confidence = confidence
                    
                    # Remove from pending
                    del self.pending_regime_changes[change_key]
            else:
                # Regime changed again before persistence - reset
                self.pending_regime_changes[change_key] = {
                    'new_regime': new_regime,
                    'first_detected': datetime.utcnow(),
                    'confidence': confidence
                }
        else:
            # New potential regime change - add to pending
            self.pending_regime_changes[change_key] = {
                'new_regime': new_regime,
                'first_detected': datetime.utcnow(),
                'confidence': confidence
            }
    
    async def _emit_regime_change(
        self,
        token: str,
        regime_type: str,
        old_regime: str,
        new_regime: str,
        confidence: float,
        metrics: Dict,
        duration_hours: float
    ):
        """Emit regime change event."""
        await self.emit_event(
            event_type=EventType.MARKET_REGIME_CHANGE,
            token=token,
            data={
                "regime_type": regime_type,
                "old_regime": old_regime,
                "new_regime": new_regime,
                "confidence": float(confidence),
                "persistence_hours": float(duration_hours),
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        cprint(f"🔄 Regime change for {token}: {regime_type} {old_regime} → {new_regime} (confidence={confidence:.2f})", "yellow")
    
    async def run_event_loop(self):
        """Override to register event handlers."""
        self._event_handlers[EventType.PRICE_TICK] = self.handle_price_tick
        await super().run_event_loop()


if __name__ == "__main__":
    agent = RegimeDetectionAgent()
    agent.run()
