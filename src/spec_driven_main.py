"""
Main entry point for the new Spec-Driven Trading Agent System.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from termcolor import cprint
import pandas as pd
import time

# Import the new specialized agents
from src.spec_driven_agents.indicator_agent import IndicatorAgent
from src.spec_driven_agents.pattern_agent import PatternAgent
from src.spec_driven_agents.lob_agent import LOBAgent
from src.spec_driven_agents.decision_agent import DecisionAgent
from src.data.tick_collector import TickCollector

class SpecDrivenTrader:
    def __init__(self, symbol='BTC'):
        self.symbol = symbol
        # Instantiate agents
        self.indicator_agent = IndicatorAgent()
        self.pattern_agent = PatternAgent()
        self.lob_agent = LOBAgent()
        self.decision_agent = DecisionAgent()
        self.tick_collector = TickCollector(self.symbol)
        self.market_data = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

        cprint("🚀 Spec-Driven Trading System Initialized!", "green")
        cprint(f"🎯 Trading Symbol: {self.symbol}", "cyan")

    async def run_cycle(self):
        """
        Runs a single trading decision cycle.
        """
        cprint("\n" + "="*50, "yellow")
        cprint(f"🕯️  Starting new trading cycle for {self.symbol}...", "yellow")

        # 1. Get real-time data
        cprint("1. Fetching Market Data...", "cyan")
        tick = self.tick_collector.get_latest_tick()

        if tick and 'data' in tick and tick['data']:
            # For now, let's just append the tick to our market data
            # In a real system, we'd aggregate ticks into bars
            trade = tick['data'][0]
            new_row = {'open': float(trade['px']), 'high': float(trade['px']), 'low': float(trade['px']), 'close': float(trade['px']), 'volume': float(trade['sz'])}
            self.market_data = self.market_data._append(new_row, ignore_index=True)
            cprint("   ✅ Got market data.", "green")
        else:
            cprint("   ⚠️ No new market data.", "yellow")
            return

        # 2. Run specialized agents to get signals
        cprint("2. Analyzing signals from specialized agents...", "cyan")
        if len(self.market_data) > 14:
            indicator_signals = self.indicator_agent.run(self.market_data)
            if indicator_signals and 'rsi' in indicator_signals and not indicator_signals['rsi'].empty:
                cprint(f"   - Indicator Agent Signals: {indicator_signals['rsi'].iloc[-1]:.2f} RSI", "white")
        else:
            cprint("   - Not enough data to calculate indicators.", "yellow")
            indicator_signals = None

        pattern_analysis = self.pattern_agent.analyze_patterns(self.market_data)
        cprint(f"   - Pattern Agent Analysis: {pattern_analysis}", "white")

        lob_imbalance = self.lob_agent.run(self.symbol)
        cprint(f"   - LOB Agent Imbalance: {lob_imbalance:.2f}", "white")

        # 3. Aggregate signals and make a decision
        cprint("3. Aggregating signals and making a decision...", "cyan")
        final_decision = self.decision_agent.make_decision(
            indicator_signals,
            pattern_analysis
        )
        cprint(f"   ✅ Decision Agent's final call: {final_decision}", "green", attrs=['bold'])

        cprint("="*50 + "\n", "yellow")


async def main():
    trader = SpecDrivenTrader(symbol='BTC')
    trader.tick_collector.start()

    # Wait for the WebSocket to connect
    while not trader.tick_collector.is_connected:
        await asyncio.sleep(1)

    # Run the trading cycle every 5 seconds
    while True:
        await trader.run_cycle()
        await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
