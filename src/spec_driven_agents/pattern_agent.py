"""
Pattern Agent

This agent is responsible for analyzing short-term candlestick patterns.
"""

import pandas as pd
from src.models.model_factory import model_factory

class PatternAgent:
    def __init__(self, model_type='openai', model_name=None):
        self.model = model_factory.get_model(model_type, model_name)

    def analyze_patterns(self, data):
        """
        Analyzes candlestick patterns using a multimodal LLM.
        """
        # For now, we'll use a simplified approach.
        # In the future, this will be replaced with a multimodal LLM.
        prompt = f"""
        Analyze the following candlestick data and identify any significant patterns.
        Return a JSON object with the identified patterns and a confidence score.

        {data.to_string()}
        """
        response = self.model.generate_response(system_prompt="", user_content=prompt)
        return response
