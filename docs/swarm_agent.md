# Swarm Agent

🌙 Moon Dev's Multi-Model AI Consensus System

## Overview
The Swarm Agent queries multiple AI models in parallel and returns:
1. **Individual responses** from each AI model
2. **AI Consensus Summary** - A 3-sentence synthesis by Claude 4.5

Perfect for getting diverse AI perspectives on trading decisions, validating strategies, or any decision that benefits from multiple viewpoints.

## Active Models (6 Total)
- **Claude 4.5 Sonnet** - Latest Anthropic model with advanced reasoning
- **GPT-5** - OpenAI's most advanced model with breakthrough capabilities
- **Gemini 2.5 Flash** - Google's newest fast model with superior capabilities
- **Grok-4 Fast** - xAI's reasoning model
- **DeepSeek Chat** - Advanced reasoning model (API)
- **DeepSeek-R1** - Local reasoning model via Ollama (free!)

## How to Use

### Method 1: Run Directly (Simplest)
```bash
# Just run it - it will ask for your prompt
python src/agents/swarm_agent.py

# It will prompt you:
# 💭 What would you like to ask the AI swarm?
# 🌙 Prompt > [type your question here]

# Then shows all individual responses + consensus
```

### Method 2: Import in Other Agents
```python
from src.agents.swarm_agent import SwarmAgent

# Initialize once
swarm = SwarmAgent()

# Get responses from all AI models
result = swarm.query("Should I buy Bitcoin at $100k?")

# Access AI consensus summary (3 sentences by Claude 4.5)
consensus = result["consensus_summary"]
print(consensus)

# Access individual model responses
for provider, data in result["responses"].items():
    if data["success"]:
        print(f"{provider}: {data['response']}")

# Check model mapping
for ai_num, provider in result["model_mapping"].items():
    print(f"{ai_num} = {provider}")
```

## Response Structure

### Full Response (Clean JSON)
```json
{
    "timestamp": "2025-01-20T10:30:00",
    "prompt": "Your query here",
    "consensus_summary": "All models recommend Solana (SOL) as the top alternative to BTC/ETH, citing high throughput, low fees, and strong developer ecosystem. Notable concerns include past network outages and centralization risks. General agreement that due diligence is essential before investing.",
    "model_mapping": {
        "AI #1": "XAI",
        "AI #2": "GEMINI",
        "AI #3": "CLAUDE",
        "AI #4": "DEEPSEEK",
        "AI #5": "OLLAMA",
        "AI #6": "OPENAI"
    },
    "responses": {
        "claude": {
            "response": "Clean text response from Claude...",
            "response_time": 9.05,
            "success": true
        },
        "openai": {
            "response": "Clean text response from GPT-5...",
            "response_time": 44.67,
            "success": true
        },
        "gemini": {
            "response": "Clean text response from Gemini...",
            "response_time": 5.1,
            "success": true
        },
        "xai": {
            "response": "Clean text response from Grok...",
            "response_time": 4.07,
            "success": true
        },
        "deepseek": {
            "response": "Clean text response from DeepSeek...",
            "response_time": 18.72,
            "success": true
        },
        "ollama": {
            "response": null,
            "error": "Connection timeout",
            "response_time": 30.0,
            "success": false
        }
    },
    "metadata": {
        "total_models": 6,
        "successful_responses": 5,
        "total_time": 45.2
    }
}
```

## Configuration

Edit `src/agents/swarm_agent.py` to customize:

```python
# Enable/disable models in swarm
SWARM_MODELS = {
    "claude": (True, "claude", "claude-sonnet-4-5"),
    "openai": (True, "openai", "gpt-5"),
    "gemini": (True, "gemini", "gemini-2.5-flash"),
    "xai": (True, "xai", "grok-4-fast-reasoning"),
    "deepseek": (True, "deepseek", "deepseek-chat"),
    "ollama": (True, "ollama", "DeepSeek-R1:latest"),
    # ... set to False to disable
}

# Consensus Reviewer - AI that synthesizes all responses
CONSENSUS_REVIEWER_MODEL = ("claude", "claude-sonnet-4-5")  # (model_type, model_name)

# Customize the consensus reviewer prompt
CONSENSUS_REVIEWER_PROMPT = """You are a consensus analyzer reviewing multiple AI responses.

Below are responses from {num_models} different AI models to the same question.

{responses}

Your task: Provide a clear, concise 3-sentence maximum consensus response that:
1. Synthesizes the common themes across all responses
2. Highlights any notable agreements or disagreements
3. Gives a balanced, actionable summary

Keep it under 3 sentences. Be direct and clear."""

# Adjust parameters
DEFAULT_TEMPERATURE = 0.7    # 0.0-1.0 (higher = more creative)
DEFAULT_MAX_TOKENS = 2048    # Response length limit (Gemini needs 2048+ minimum)
```

## Output Location
All swarm queries are automatically saved to:
```
src/data/swarm_agent/swarm_result_YYYYMMDD_HHMMSS.json
```

## Use Cases

### Trading Decisions
Ask the swarm about potential trades and get diverse AI perspectives:
- "Should I buy SOL at current price of $100?"
- "Is now a good time to enter BTC?"

### Risk Assessment
Validate risk decisions across multiple AI models:
- "Is 10x leverage too risky for BTC right now?"
- "Should I set a stop loss at -5% for this ETH position?"

### Market Analysis
Get consensus on market conditions:
- "What's the market sentiment for memecoins today?"
- "Is the current market bullish or bearish?"

### Strategy Validation
Validate trading strategies before implementing:
- "Is RSI divergence a reliable signal for ETH?"
- "Should I use MACD crossover for my day trading strategy?"

## Performance Notes
- Queries run in parallel (typically 2-5 seconds total)
- Individual model timeouts: 30 seconds
- Failed models don't block others
- Consensus calculated only from successful responses

## Cost Estimates (per query)
- Claude 4.5 Sonnet: ~$0.004
- GPT-5: ~$0.015
- Gemini 2.5 Flash: ~$0.0002
- Grok-4: ~$0.001
- DeepSeek (API): ~$0.0005
- DeepSeek-R1 (Ollama): **FREE** (runs locally)
- **Total: ~$0.021 per swarm query**

## Example: Using in Other Agents

```python
# Quick example
from src.agents.swarm_agent import SwarmAgent

swarm = SwarmAgent()
result = swarm.query("Should I buy SOL at $100?")

# Get AI-generated consensus summary (3 sentences by Claude 4.5)
print(result["consensus_summary"])
# "All models recommend considering Solana due to its high throughput..."

# Get individual clean responses (no ModelResponse objects!)
for provider, data in result["responses"].items():
    if data["success"]:
        print(f"{provider}: {data['response']}")

# Check model mapping to see which AI is which
for ai_num, provider in result["model_mapping"].items():
    print(f"{ai_num} = {provider}")
```

## Tips
- Consensus summary is generated by Claude 4.5 reviewing all responses
- Individual responses are stripped of `<think>` tags for clean output
- Adjust `DEFAULT_MAX_TOKENS` (currently 2048) if you need longer/shorter responses
- Failed models don't block the swarm - you'll get results from successful models
- **Import and use in other agents** - perfect for validating trading decisions with AI consensus
- All queries are automatically saved to `src/data/swarm_agent/` for later review

Built by Moon Dev - Harnessing collective AI intelligence 🌙