"""
Indicator Agent

This agent is responsible for calculating low-latency technical indicators.
"""

import pandas as pd
import pandas_ta as ta

class IndicatorAgent:
    def __init__(self):
        pass

    def calculate_rsi(self, data, period=14):
        """Calculates the Relative Strength Index (RSI)"""
        return ta.rsi(data['close'], length=period)

    def calculate_rate_of_change(self, data, period=14):
        """Calculates the Rate of Change (ROC)"""
        roc = ((data['close'] - data['close'].shift(period)) / data['close'].shift(period)) * 100
        return roc

    def run(self, data):
        """Calculates all indicators and returns them as a dictionary"""
        indicators = {
            'rsi': self.calculate_rsi(data),
            'roc': self.calculate_rate_of_change(data)
        }
        return indicators
