"""
🌙 Moon Dev's Base Agent
Parent class for all trading agents with unified exchange support
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd
from termcolor import cprint

class BaseAgent:
    def __init__(self, agent_type, use_exchange_manager=False):
        """
        Initialize base agent with type and optional exchange manager

        Args:
            agent_type: Type of agent (e.g., 'trading', 'risk', 'strategy')
            use_exchange_manager: If True, initialize ExchangeManager for unified trading
        """
        self.type = agent_type
        self.start_time = datetime.now()
        self.em = None  # Exchange manager instance

        # Initialize exchange manager if requested
        if use_exchange_manager:
            try:
                from src.exchange_manager import ExchangeManager
                from src.config import EXCHANGE

                self.em = ExchangeManager()
                cprint(f"✅ {agent_type.capitalize()} agent initialized with {EXCHANGE} exchange", "green")

                # Store exchange type for convenience
                self.exchange = EXCHANGE

            except Exception as e:
                cprint(f"⚠️ Could not initialize ExchangeManager: {str(e)}", "yellow")
                cprint("   Falling back to direct nice_funcs imports", "yellow")

                # Fallback to direct imports
                from src import nice_funcs as n
                self.n = n
                self.exchange = 'solana'  # Default fallback

    def get_active_tokens(self):
        """Get the appropriate token/symbol list based on active exchange"""
        try:
            from src.config import get_active_tokens
            return get_active_tokens()
        except:
            from src.config import MONITORED_TOKENS
            return MONITORED_TOKENS

    def run(self):
        """Default run method - should be overridden by child classes"""
        raise NotImplementedError("Each agent must implement its own run method") 