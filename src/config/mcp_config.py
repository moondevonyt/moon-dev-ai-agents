"""
🌙 BB1151's MCP Configuration
Configuration for MCP servers (Smithery, deep-research, etc.)
"""
import os

# MCP Server Configuration
MCP_ENABLED = True  # Set to False to disable MCP research

# MCP Deep Research Configuration
SMITHERY_CONFIG = {
    "command": "npx",
    "args": ["-y", "mcp-deep-research@latest"],
    "env": {
        "TAVILY_API_KEY": "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",
        "MAX_SEARCH_KEYWORDS": "5",
        "MAX_PLANNING_ROUNDS": "5"
    },
    "timeout": 60  # seconds - increased for deep research
}

# Research Query Template
RESEARCH_QUERY_TEMPLATE = """
Analyze the crypto trading landscape in the last 24-48 hours:
1. Notable liquidation clusters or cascades (BTC/ETH/SOL)
2. Funding rate anomalies or extreme deviations
3. Volume spikes or unusual trading patterns
4. Volatility regime changes
5. Key technical breakouts or breakdowns
6. Sentiment shifts in social media or forums

Focus on ACTIONABLE insights that could inform a trading strategy.
Return a concise summary with key facts and sources.
"""

# Fallback context if MCP fails
FALLBACK_CONTEXT = """
Market context unavailable. Focus on robust technical analysis strategies 
that work across different market conditions.
"""
