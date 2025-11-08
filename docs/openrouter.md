# OpenRouter Integration

Access 200+ AI models through a single API key.

## What It Does
- Unified access to all major AI models
- Single API key for Claude, GPT, Gemini, Qwen, GLM, and 200+ others
- Easy model switching without code changes
- Cost-effective pricing across providers

## Supported Models
### Currently Configured

**Google Gemini:**
- `google/gemini-2.5-pro` - Advanced reasoning, 128k context
- `google/gemini-2.5-flash` - Fast multimodal, 1M context

**Qwen:**
- `qwen/qwen3-vl-32b-instruct` - Vision & Language, 32k context
- `qwen/qwen3-max` - Flagship Qwen model, 32k context

**Zhipu AI:**
- `z-ai/glm-4.6` - Zhipu AI, 128k context

**DeepSeek:**
- `deepseek/deepseek-r1-0528` - Advanced reasoning, 64k context

**OpenAI GPT:**
- `openai/gpt-4.5-preview` - Latest OpenAI flagship, 128k context
- `openai/gpt-5` - Next-gen model, 200k context
- `openai/gpt-5-mini` - Fast & efficient, 128k context
- `openai/gpt-5-nano` - Ultra-fast & cheap, 64k context

**Anthropic Claude:**
- `anthropic/claude-sonnet-4.5` - Balanced performance, 200k context
- `anthropic/claude-haiku-4.5` - Fast & efficient, 200k context
- `anthropic/claude-opus-4.1` - Most powerful, 200k context

### Adding More Models
See https://openrouter.ai/docs for 200+ available models.

Add models to `src/models/openrouter_model.py`:
```python
AVAILABLE_MODELS = {
    "provider/model-name": {
        "description": "Model description",
        "input_price": "$X.XX/1M tokens",
        "output_price": "$X.XX/1M tokens"
    }
}
```

## Setup
1. Get API key from https://openrouter.ai/keys
2. Add to `.env`:
```bash
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

## Usage
### In RBI Agent
Edit `src/agents/rbi_agent_pp_multi.py`:
```python
RESEARCH_CONFIG = {
    "type": "openrouter",
    "name": "google/gemini-2.5-flash"
}

BACKTEST_CONFIG = {
    "type": "openrouter",
    "name": "google/gemini-2.5-pro"
}
```

### In Any Agent
```python
from src.models.model_factory import model_factory

model = model_factory.get_model("openrouter", "qwen/qwen3-max")
response = model.generate_response(system_prompt, user_content)
```

## Current Configuration
**RBI Agent (rbi_agent_pp_multi.py):**
- Research: Gemini 2.5 Flash (fast strategy analysis)
- Backtest Code: Gemini 2.5 Pro (advanced reasoning)
- Debugging: Qwen 3 VL 32B (vision & language)
- Package Check: GLM 4.6 (Zhipu AI)
- Optimization: GLM 4.6 (Zhipu AI)

## Pricing
See current pricing at https://openrouter.ai/docs

Examples:
- Gemini 2.5 Flash: $0.10 input / $0.40 output per 1M tokens
- Gemini 2.5 Pro: $1.25 input / $5.00 output per 1M tokens
- Qwen 3 VL 32B: $0.25 input / $0.25 output per 1M tokens
- GLM 4.6: $0.50 input / $0.50 output per 1M tokens

## Benefits
- No need to manage multiple API keys
- Easy A/B testing between models
- Automatic failover and load balancing
- Access to latest models as they release
- Unified billing across all providers

## Implementation Details
- Uses OpenAI-compatible SDK (`openai` package)
- Base URL: `https://openrouter.ai/api/v1`
- Follows same pattern as other model providers
- Fully integrated with Moon Dev's ModelFactory

## Files
- `src/models/openrouter_model.py` - OpenRouter implementation
- `src/models/model_factory.py` - Factory registration
- `.env` - API key storage
