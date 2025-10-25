"""
Tests for the spec-driven agents.
"""

import pandas as pd
from src.spec_driven_agents.indicator_agent import IndicatorAgent

def test_rsi_calculation():
    """
    Tests that the RSI is calculated correctly.
    """
    data = {
        'close': [
            44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08,
            45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64
        ]
    }
    df = pd.DataFrame(data)
    agent = IndicatorAgent()
    rsi = agent.calculate_rsi(df, period=14)
    assert round(rsi.iloc[-1], 2) == 43.20
