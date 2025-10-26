"""
🌙 Moon Dev's AI Trading System
Main entry point for running trading agents
"""

import os
import sys
import asyncio
import threading
from termcolor import cprint
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta
from config import *

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import agents
from src.agents.trading_agent import TradingAgent
from src.agents.risk_agent import RiskAgent
from src.agents.strategy_agent import StrategyAgent
from src.agents.copybot_agent import CopyBotAgent
from src.agents.sentiment_agent import SentimentAgent

# Import quantitative agents
from src.agents.quant.anomaly_detection_agent import AnomalyDetectionAgent
from src.agents.quant.signal_aggregation_agent import SignalAggregationAgent
from src.agents.quant.transaction_cost_agent import TransactionCostAgent
from src.agents.quant.backtesting_validation_agent import BacktestingValidationAgent
from src.agents.quant.capacity_monitoring_agent import CapacityMonitoringAgent
from src.agents.quant.signal_decay_agent import SignalDecayAgent
from src.agents.quant.regime_detection_agent import RegimeDetectionAgent
from src.agents.quant.correlation_matrix_agent import CorrelationMatrixAgent
from src.agents.quant.portfolio_optimization_agent import PortfolioOptimizationAgent
from src.agents.quant.alternative_data_agent import AlternativeDataAgent

# Load environment variables
load_dotenv()

# Agent Configuration
ACTIVE_AGENTS = {
    'risk': False,      # Risk management agent
    'trading': False,   # LLM trading agent
    'strategy': False,  # Strategy-based trading agent
    'copybot': False,   # CopyBot agent
    'sentiment': False, # Run sentiment_agent.py directly instead
    # whale_agent is run from whale_agent.py
    
    # Quantitative Agents (Jim Simons-style)
    'quant_anomaly': False,         # Anomaly detection agent
    'quant_signal_agg': False,      # Signal aggregation agent
    'quant_transaction': False,     # Transaction cost analysis agent
    'quant_backtest': False,        # Backtesting validation agent
    'quant_capacity': False,        # Capacity monitoring agent
    'quant_decay': False,           # Signal decay monitoring agent
    'quant_regime': False,          # Market regime detection agent
    'quant_correlation': False,     # Correlation matrix agent
    'quant_portfolio': False,       # Portfolio optimization agent
    'quant_altdata': False,         # Alternative data agent
}

async def run_quant_agents():
    """Run quantitative agents in background"""
    import asyncio
    
    quant_agents = []
    
    if ACTIVE_AGENTS['quant_anomaly']:
        quant_agents.append(AnomalyDetectionAgent())
    if ACTIVE_AGENTS['quant_signal_agg']:
        quant_agents.append(SignalAggregationAgent())
    if ACTIVE_AGENTS['quant_transaction']:
        quant_agents.append(TransactionCostAgent())
    if ACTIVE_AGENTS['quant_backtest']:
        quant_agents.append(BacktestingValidationAgent())
    if ACTIVE_AGENTS['quant_capacity']:
        quant_agents.append(CapacityMonitoringAgent())
    if ACTIVE_AGENTS['quant_decay']:
        quant_agents.append(SignalDecayAgent())
    if ACTIVE_AGENTS['quant_regime']:
        quant_agents.append(RegimeDetectionAgent())
    if ACTIVE_AGENTS['quant_correlation']:
        quant_agents.append(CorrelationMatrixAgent())
    if ACTIVE_AGENTS['quant_portfolio']:
        quant_agents.append(PortfolioOptimizationAgent())
    if ACTIVE_AGENTS['quant_altdata']:
        quant_agents.append(AlternativeDataAgent())
    
    if quant_agents:
        cprint(f"\n🔬 Starting {len(quant_agents)} quantitative agents...", "cyan")
        
        # Initialize all agents
        for agent in quant_agents:
            await agent.initialize()
            cprint(f"✅ {agent.type} initialized", "green")
        
        # Run all agents concurrently in their event loops
        try:
            await asyncio.gather(*[agent.run_event_loop() for agent in quant_agents])
        except KeyboardInterrupt:
            cprint("\n⚠️ Quantitative agents interrupted by user", "yellow")
        finally:
            # Shutdown all agents
            for agent in quant_agents:
                await agent.shutdown()

def run_agents():
    """Run all active agents in sequence"""
    try:
        # Initialize active agents
        trading_agent = TradingAgent() if ACTIVE_AGENTS['trading'] else None
        risk_agent = RiskAgent() if ACTIVE_AGENTS['risk'] else None
        strategy_agent = StrategyAgent() if ACTIVE_AGENTS['strategy'] else None
        copybot_agent = CopyBotAgent() if ACTIVE_AGENTS['copybot'] else None
        sentiment_agent = SentimentAgent() if ACTIVE_AGENTS['sentiment'] else None
        
        # Start quantitative agents in separate thread if any are enabled
        quant_enabled = any([
            ACTIVE_AGENTS.get('quant_anomaly'),
            ACTIVE_AGENTS.get('quant_signal_agg'),
            ACTIVE_AGENTS.get('quant_transaction'),
            ACTIVE_AGENTS.get('quant_backtest'),
            ACTIVE_AGENTS.get('quant_capacity'),
            ACTIVE_AGENTS.get('quant_decay'),
            ACTIVE_AGENTS.get('quant_regime'),
            ACTIVE_AGENTS.get('quant_correlation'),
            ACTIVE_AGENTS.get('quant_portfolio'),
            ACTIVE_AGENTS.get('quant_altdata'),
        ])
        
        if quant_enabled:
            def run_async_agents():
                asyncio.run(run_quant_agents())
            
            quant_thread = threading.Thread(target=run_async_agents, daemon=True)
            quant_thread.start()
            cprint("✅ Quantitative agents running in background thread", "green")

        while True:
            try:
                # Run Risk Management
                if risk_agent:
                    cprint("\n🛡️ Running Risk Management...", "cyan")
                    risk_agent.run()

                # Run Trading Analysis
                if trading_agent:
                    cprint("\n🤖 Running Trading Analysis...", "cyan")
                    trading_agent.run()

                # Run Strategy Analysis
                if strategy_agent:
                    cprint("\n📊 Running Strategy Analysis...", "cyan")
                    for token in MONITORED_TOKENS:
                        if token not in EXCLUDED_TOKENS:  # Skip USDC and other excluded tokens
                            cprint(f"\n🔍 Analyzing {token}...", "cyan")
                            strategy_agent.get_signals(token)

                # Run CopyBot Analysis
                if copybot_agent:
                    cprint("\n🤖 Running CopyBot Portfolio Analysis...", "cyan")
                    copybot_agent.run_analysis_cycle()

                # Run Sentiment Analysis
                if sentiment_agent:
                    cprint("\n🎭 Running Sentiment Analysis...", "cyan")
                    sentiment_agent.run()

                # Sleep until next cycle
                next_run = datetime.now() + timedelta(minutes=SLEEP_BETWEEN_RUNS_MINUTES)
                cprint(f"\n😴 Sleeping until {next_run.strftime('%H:%M:%S')}", "cyan")
                time.sleep(60 * SLEEP_BETWEEN_RUNS_MINUTES)

            except Exception as e:
                cprint(f"\n❌ Error running agents: {str(e)}", "red")
                cprint("🔄 Continuing to next cycle...", "yellow")
                time.sleep(60)  # Sleep for 1 minute on error before retrying

    except KeyboardInterrupt:
        cprint("\n👋 Gracefully shutting down...", "yellow")
    except Exception as e:
        cprint(f"\n❌ Fatal error in main loop: {str(e)}", "red")
        raise

if __name__ == "__main__":
    cprint("\n🌙 Moon Dev AI Agent Trading System Starting...", "white", "on_blue")
    cprint("\n📊 Active Agents:", "white", "on_blue")
    for agent, active in ACTIVE_AGENTS.items():
        status = "✅ ON" if active else "❌ OFF"
        cprint(f"  • {agent.title()}: {status}", "white", "on_blue")
    print("\n")

    run_agents()