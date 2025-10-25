"""
Decision Agent

This agent is responsible for aggregating signals from other specialized agents
and making a final trading decision.
"""

from src.models.model_factory import model_factory

class DecisionAgent:
    def __init__(self, model_type='gemini', model_name='gemini-flash'):
        self.model = model_factory.get_model(model_type, model_name)

    def make_decision(self, indicator_signals, pattern_analysis):
        """
        Makes a trading decision based on the provided signals.
        """
        prompt = f"""
        Given the following signals, make a trading decision (BUY, SELL, or HOLD).

        Indicator Signals:
        {indicator_signals}

        Pattern Analysis:
        {pattern_analysis}
        """
        response = self.model.generate_response(prompt)
        return response
