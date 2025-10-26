"""
🌙 Moon Dev's Signal Decay Monitoring Agent
Detects and retires degraded signals

Implements signal performance tracking:
- Rolling 30-day Sharpe ratio calculation
- Decay detection (Sharpe < 0.5 for 14 days)
- Automatic weight reduction for degraded signals
- Signal retirement after 30 days of degradation
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from termcolor import cprint

from src.agents.quant.base_quant_agent import BaseQuantAgent
from src.agents.quant.statistical_utils import (
    calculate_sharpe_ratio,
    calculate_win_rate,
    calculate_profit_factor
)
from src.core.models import Event, EventType
from src.config import (
    SIGNAL_DECAY_WINDOW_DAYS,
    SIGNAL_DECAY_SHARPE_THRESHOLD,
    SIGNAL_DECAY_DEGRADED_DAYS,
    SIGNAL_DECAY_RETIREMENT_DAYS,
    SIGNAL_DECAY_MIN_WIN_RATE_PCT,
    SIGNAL_DECAY_WEIGHT_REDUCTION_PCT
)


@dataclass
class SignalPerformance:
    """Performance tracking for a signal source."""
    signal_source: str
    returns: List[float] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)
    rolling_sharpe: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    consecutive_degraded_days: int = 0
    status: str = "active"  # active, degraded, retired
    last_updated: Optional[datetime] = None
    degraded_since: Optional[datetime] = None


class SignalDecayAgent(BaseQuantAgent):
    """Monitors signal performance and detects decay."""
    
    def __init__(self):
        super().__init__(
            agent_type="signal_decay",
            subscribed_topics=["signal.generated", "trade.executed"]
        )
        
        # Signal performance tracking
        self.signal_performance: Dict[str, SignalPerformance] = {}
        
        # Pending signals (waiting for trade outcome)
        self.pending_signals: Dict[str, List[Dict]] = {}
        
        cprint("✅ Signal Decay Agent initialized", "green")

    
    async def initialize(self):
        """Initialize agent and load performance history."""
        await super().initialize()
        
        # Load performance history from Redis
        await self._load_performance_from_cache()
        
        # Start daily decay check task
        asyncio.create_task(self._daily_decay_check())
    
    async def _load_performance_from_cache(self):
        """Load signal performance from Redis cache."""
        try:
            perf_data = await self.cache.get("signal_performance")
            if perf_data:
                perf_dict = json.loads(perf_data)
                for source, data in perf_dict.items():
                    # Convert timestamp strings back to datetime
                    if 'timestamps' in data:
                        data['timestamps'] = [datetime.fromisoformat(ts) for ts in data['timestamps']]
                    if 'last_updated' in data and data['last_updated']:
                        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
                    if 'degraded_since' in data and data['degraded_since']:
                        data['degraded_since'] = datetime.fromisoformat(data['degraded_since'])
                    
                    self.signal_performance[source] = SignalPerformance(**data)
                
                cprint(f"✅ Loaded performance for {len(self.signal_performance)} signals", "green")
        except Exception as e:
            cprint(f"⚠️ Could not load performance from cache: {str(e)}", "yellow")
    
    async def _save_performance_to_cache(self):
        """Save signal performance to Redis cache."""
        try:
            perf_dict = {}
            for source, perf in self.signal_performance.items():
                data = asdict(perf)
                # Convert datetime objects to ISO strings
                data['timestamps'] = [ts.isoformat() for ts in data['timestamps']]
                if data['last_updated']:
                    data['last_updated'] = data['last_updated'].isoformat()
                if data['degraded_since']:
                    data['degraded_since'] = data['degraded_since'].isoformat()
                perf_dict[source] = data
            
            await self.cache.set("signal_performance", json.dumps(perf_dict))
        except Exception as e:
            cprint(f"⚠️ Could not save performance to cache: {str(e)}", "yellow")

    
    async def handle_signal_generated(self, event: Event):
        """Track signal for matching with trades."""
        signal_source = event.source
        token = event.token
        
        if not signal_source or not token:
            return
        
        # Store signal for matching
        if signal_source not in self.pending_signals:
            self.pending_signals[signal_source] = []
        
        self.pending_signals[signal_source].append({
            'timestamp': event.timestamp,
            'token': token,
            'direction': event.data.get('direction'),
            'confidence': event.data.get('confidence', 0.5),
            'correlation_id': event.correlation_id
        })
        
        # Initialize performance tracking if new source
        if signal_source not in self.signal_performance:
            self.signal_performance[signal_source] = SignalPerformance(
                signal_source=signal_source,
                last_updated=datetime.utcnow()
            )
    
    async def handle_trade_executed(self, event: Event):
        """Match trade to signal and update performance."""
        token = event.token
        return_pct = event.data.get('return_pct', 0)
        correlation_id = event.correlation_id
        
        if not token:
            return
        
        # Find matching signals
        for signal_source, signals in list(self.pending_signals.items()):
            matched_signals = []
            
            for signal in signals:
                # Match by token and correlation_id (if available)
                if signal['token'] == token:
                    if correlation_id and signal.get('correlation_id') == correlation_id:
                        matched_signals.append(signal)
                    elif not correlation_id:
                        # Match by timestamp proximity (within 1 minute)
                        time_diff = abs((event.timestamp - signal['timestamp']).total_seconds())
                        if time_diff < 60:
                            matched_signals.append(signal)
            
            # Update performance for matched signals
            for matched_signal in matched_signals:
                await self._update_signal_performance(signal_source, return_pct)
                
                # Remove matched signal from pending
                if matched_signal in signals:
                    signals.remove(matched_signal)
            
            # Clean up old pending signals (> 1 hour old)
            cutoff = datetime.utcnow() - timedelta(hours=1)
            self.pending_signals[signal_source] = [
                s for s in signals if s['timestamp'] > cutoff
            ]

    
    async def _update_signal_performance(self, signal_source: str, return_pct: float):
        """Update performance metrics for a signal source."""
        if signal_source not in self.signal_performance:
            return
        
        perf = self.signal_performance[signal_source]
        
        # Add return
        perf.returns.append(return_pct)
        perf.timestamps.append(datetime.utcnow())
        perf.total_trades += 1
        
        if return_pct > 0:
            perf.winning_trades += 1
        
        # Keep only last N days of data
        cutoff = datetime.utcnow() - timedelta(days=SIGNAL_DECAY_WINDOW_DAYS)
        valid_indices = [i for i, ts in enumerate(perf.timestamps) if ts > cutoff]
        perf.returns = [perf.returns[i] for i in valid_indices]
        perf.timestamps = [perf.timestamps[i] for i in valid_indices]
        
        # Calculate metrics if enough data
        if len(perf.returns) >= 10:
            perf.rolling_sharpe = calculate_sharpe_ratio(perf.returns)
            perf.win_rate = calculate_win_rate(perf.returns)
            perf.profit_factor = calculate_profit_factor(perf.returns)
        
        perf.last_updated = datetime.utcnow()
        
        # Check for decay
        await self._check_signal_decay(signal_source)
        
        # Save to cache
        await self._save_performance_to_cache()
        
        cprint(f"📊 {signal_source}: Sharpe={perf.rolling_sharpe:.2f}, WinRate={perf.win_rate:.1f}%", "cyan")
    
    async def _check_signal_decay(self, signal_source: str):
        """Check if signal is degrading."""
        perf = self.signal_performance.get(signal_source)
        if not perf or len(perf.returns) < 10:
            return
        
        # Check if Sharpe is below threshold
        if perf.rolling_sharpe < SIGNAL_DECAY_SHARPE_THRESHOLD:
            perf.consecutive_degraded_days += 1
            
            if not perf.degraded_since:
                perf.degraded_since = datetime.utcnow()
            
            # Mark as degraded after threshold days
            if perf.consecutive_degraded_days >= SIGNAL_DECAY_DEGRADED_DAYS and perf.status == "active":
                perf.status = "degraded"
                
                # Reduce weight immediately
                await self._reduce_signal_weight(signal_source)
                
                cprint(f"⚠️ Signal {signal_source} marked as DEGRADED (Sharpe={perf.rolling_sharpe:.2f})", "yellow")
            
            # Check retirement criteria
            days_degraded = (datetime.utcnow() - perf.degraded_since).days if perf.degraded_since else 0
            
            if (days_degraded >= SIGNAL_DECAY_RETIREMENT_DAYS or 
                perf.win_rate < SIGNAL_DECAY_MIN_WIN_RATE_PCT):
                
                await self._retire_signal(signal_source)
        else:
            # Signal recovered
            if perf.status == "degraded":
                perf.status = "active"
                perf.consecutive_degraded_days = 0
                perf.degraded_since = None
                cprint(f"✅ Signal {signal_source} RECOVERED (Sharpe={perf.rolling_sharpe:.2f})", "green")
    
    async def _reduce_signal_weight(self, signal_source: str):
        """Reduce weight for degraded signal."""
        try:
            # Get current weight from Signal Aggregation Agent's cache
            weights_data = await self.cache.get("signal_weights")
            if not weights_data:
                return
            
            weights = json.loads(weights_data)
            
            if signal_source in weights:
                current_weight = weights[signal_source].get('weight', 0.5)
                new_weight = current_weight * (1 - SIGNAL_DECAY_WEIGHT_REDUCTION_PCT / 100)
                
                weights[signal_source]['weight'] = new_weight
                weights[signal_source]['last_updated'] = datetime.utcnow().isoformat()
                
                await self.cache.set("signal_weights", json.dumps(weights))
                
                cprint(f"📉 Reduced weight for {signal_source}: {current_weight:.3f} → {new_weight:.3f}", "yellow")
                
                # Emit event to notify Signal Aggregation Agent
                await self.emit_event(
                    event_type=EventType.SIGNAL_CORRELATION,  # Reuse for weight update
                    token=None,
                    data={
                        "signal_source": signal_source,
                        "action": "weight_reduced",
                        "old_weight": current_weight,
                        "new_weight": new_weight,
                        "reason": "signal_degraded"
                    }
                )
        except Exception as e:
            cprint(f"⚠️ Error reducing weight for {signal_source}: {str(e)}", "yellow")
    
    async def _retire_signal(self, signal_source: str):
        """Retire a signal that has degraded beyond recovery."""
        perf = self.signal_performance.get(signal_source)
        if not perf or perf.status == "retired":
            return
        
        perf.status = "retired"
        
        # Emit retirement event
        await self.emit_event(
            event_type=EventType.SIGNAL_RETIRED,
            token=None,
            data={
                "signal_source": signal_source,
                "final_sharpe": perf.rolling_sharpe,
                "final_win_rate": perf.win_rate,
                "total_trades": perf.total_trades,
                "retirement_reason": self._get_retirement_reason(perf),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Update signal registry in Redis
        try:
            weights_data = await self.cache.get("signal_weights")
            if weights_data:
                weights = json.loads(weights_data)
                if signal_source in weights:
                    weights[signal_source]['status'] = 'retired'
                    weights[signal_source]['retired_at'] = datetime.utcnow().isoformat()
                    await self.cache.set("signal_weights", json.dumps(weights))
        except Exception as e:
            cprint(f"⚠️ Error updating signal registry: {str(e)}", "yellow")
        
        # Save performance to cache
        await self._save_performance_to_cache()
        
        cprint(f"🚫 Signal {signal_source} RETIRED (Sharpe={perf.rolling_sharpe:.2f}, WinRate={perf.win_rate:.1f}%)", "red")
    
    def _get_retirement_reason(self, perf: SignalPerformance) -> str:
        """Get human-readable retirement reason."""
        reasons = []
        
        days_degraded = (datetime.utcnow() - perf.degraded_since).days if perf.degraded_since else 0
        
        if days_degraded >= SIGNAL_DECAY_RETIREMENT_DAYS:
            reasons.append(f"degraded for {days_degraded} days")
        
        if perf.win_rate < SIGNAL_DECAY_MIN_WIN_RATE_PCT:
            reasons.append(f"win rate {perf.win_rate:.1f}% < {SIGNAL_DECAY_MIN_WIN_RATE_PCT}%")
        
        if perf.rolling_sharpe < SIGNAL_DECAY_SHARPE_THRESHOLD:
            reasons.append(f"Sharpe {perf.rolling_sharpe:.2f} < {SIGNAL_DECAY_SHARPE_THRESHOLD}")
        
        return ", ".join(reasons) if reasons else "unknown"
    
    async def _daily_decay_check(self):
        """Daily task to check all signals for decay."""
        while self.is_running:
            try:
                await asyncio.sleep(86400)  # 24 hours
                
                cprint("🔍 Running daily signal decay check...", "cyan")
                
                for signal_source in list(self.signal_performance.keys()):
                    await self._check_signal_decay(signal_source)
                
                # Generate weekly report (every 7 days)
                if datetime.utcnow().weekday() == 0:  # Monday
                    await self._generate_decay_report()
                
            except Exception as e:
                cprint(f"⚠️ Error in daily decay check: {str(e)}", "yellow")
    
    async def _generate_decay_report(self):
        """Generate weekly decay report."""
        active_signals = [s for s in self.signal_performance.values() if s.status == "active"]
        degraded_signals = [s for s in self.signal_performance.values() if s.status == "degraded"]
        retired_signals = [s for s in self.signal_performance.values() if s.status == "retired"]
        
        report = {
            "report_date": datetime.utcnow().isoformat(),
            "total_signals": len(self.signal_performance),
            "active_count": len(active_signals),
            "degraded_count": len(degraded_signals),
            "retired_count": len(retired_signals),
            "active_signals": [
                {
                    "source": s.signal_source,
                    "sharpe": s.rolling_sharpe,
                    "win_rate": s.win_rate,
                    "total_trades": s.total_trades
                }
                for s in sorted(active_signals, key=lambda x: x.rolling_sharpe, reverse=True)[:10]
            ],
            "degraded_signals": [
                {
                    "source": s.signal_source,
                    "sharpe": s.rolling_sharpe,
                    "win_rate": s.win_rate,
                    "days_degraded": (datetime.utcnow() - s.degraded_since).days if s.degraded_since else 0
                }
                for s in degraded_signals
            ]
        }
        
        # Store report in Redis
        await self.cache.set(
            f"signal_decay_report:{datetime.utcnow().strftime('%Y%m%d')}",
            json.dumps(report)
        )
        
        cprint(f"📊 Weekly Decay Report: {len(active_signals)} active, {len(degraded_signals)} degraded, {len(retired_signals)} retired", "cyan")
    
    async def run_event_loop(self):
        """Register event handlers and run loop."""
        self._event_handlers[EventType.SIGNAL_GENERATED] = self.handle_signal_generated
        self._event_handlers[EventType.TRADE_EXECUTED] = self.handle_trade_executed
        await super().run_event_loop()


if __name__ == "__main__":
    agent = SignalDecayAgent()
    agent.run()

    
    async def _reduce_signal_weight(self, signal_source: str):
        """Reduce signal weight when degraded."""
        # Notify Signal Aggregation Agent to reduce weight
        await self.emit_event(
            event_type=EventType.SIGNAL_RETIRED,  # Using this to signal weight reduction
            token=None,
            data={
                "signal_source": signal_source,
                "action": "reduce_weight",
                "reduction_pct": SIGNAL_DECAY_WEIGHT_REDUCTION_PCT,
                "reason": "Signal degraded",
                "current_sharpe": self.signal_performance[signal_source].rolling_sharpe
            }
        )
    
    async def _retire_signal(self, signal_source: str):
        """Retire a degraded signal."""
        perf = self.signal_performance.get(signal_source)
        if not perf:
            return
        
        perf.status = "retired"
        
        # Emit retirement event
        await self.emit_event(
            event_type=EventType.SIGNAL_RETIRED,
            token=None,
            data={
                "signal_source": signal_source,
                "action": "retire",
                "final_sharpe": float(perf.rolling_sharpe),
                "final_win_rate": float(perf.win_rate),
                "final_profit_factor": float(perf.profit_factor),
                "total_trades": perf.total_trades,
                "days_degraded": (datetime.utcnow() - perf.degraded_since).days if perf.degraded_since else 0,
                "reason": f"Degraded for {SIGNAL_DECAY_RETIREMENT_DAYS} days or win rate < {SIGNAL_DECAY_MIN_WIN_RATE_PCT}%"
            }
        )
        
        cprint(f"🚫 Signal {signal_source} RETIRED (Sharpe={perf.rolling_sharpe:.2f}, WinRate={perf.win_rate:.1f}%)", "red")
        
        # Save to cache
        await self._save_performance_to_cache()
    
    async def _daily_decay_check(self):
        """Daily check for signal decay."""
        while self.is_running:
            await asyncio.sleep(86400)  # Run daily
            
            cprint("🔄 Running daily signal decay check...", "cyan")
            
            for signal_source in list(self.signal_performance.keys()):
                await self._check_signal_decay(signal_source)
            
            # Generate weekly report (every 7 days)
            if datetime.utcnow().weekday() == 0:  # Monday
                await self._generate_decay_report()
    
    async def _generate_decay_report(self):
        """Generate weekly decay report."""
        active_signals = [s for s in self.signal_performance.values() if s.status == "active"]
        degraded_signals = [s for s in self.signal_performance.values() if s.status == "degraded"]
        retired_signals = [s for s in self.signal_performance.values() if s.status == "retired"]
        
        report = {
            "report_date": datetime.utcnow().isoformat(),
            "total_signals": len(self.signal_performance),
            "active_signals": len(active_signals),
            "degraded_signals": len(degraded_signals),
            "retired_signals": len(retired_signals),
            "top_performers": [
                {
                    "source": s.signal_source,
                    "sharpe": s.rolling_sharpe,
                    "win_rate": s.win_rate
                }
                for s in sorted(active_signals, key=lambda x: x.rolling_sharpe, reverse=True)[:5]
            ],
            "worst_performers": [
                {
                    "source": s.signal_source,
                    "sharpe": s.rolling_sharpe,
                    "win_rate": s.win_rate
                }
                for s in sorted(active_signals, key=lambda x: x.rolling_sharpe)[:5]
            ]
        }
        
        cprint(f"📊 Weekly Decay Report: {len(active_signals)} active, {len(degraded_signals)} degraded, {len(retired_signals)} retired", "cyan")
        
        # Store report in cache
        await self.cache.set("signal_decay_report", json.dumps(report))
    
    async def run_event_loop(self):
        """Override to register event handlers."""
        self._event_handlers[EventType.SIGNAL_GENERATED] = self.handle_signal_generated
        self._event_handlers[EventType.TRADE_EXECUTED] = self.handle_trade_executed
        await super().run_event_loop()


if __name__ == "__main__":
    agent = SignalDecayAgent()
    agent.run()
