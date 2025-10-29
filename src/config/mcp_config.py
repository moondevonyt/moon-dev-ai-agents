"""
🌙 BB1151's MCP Configuration
Configuration for MCP servers (Smithery, deep-research, etc.)
"""
import os

# MCP Server Configuration
MCP_ENABLED = True  # Set to False to disable MCP research

# Smithery Deep Research Configuration
SMITHERY_CONFIG = {
    "command": "npx",
    "args": [
        "-y",
        "@smithery/cli@latest",
        "run",
        "@baranwang/mcp-deep-research",
        "--key",
        "7d9bcb4f-45e8-4ac1-8cae-7886b4222548",
        "--profile",
        "circular-catshark-yb728x",
    ],
    "timeout": 30  # seconds
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
