# 🔄 Agent Update Guide - OpenRouter Migration

Dit document helpt bij het updaten van agents naar het nieuwe OpenRouter/ModelFactory pattern.

## ✅ Status Overzicht

### Agents Geüpdatet voor OpenRouter
- ✅ `risk_agent.py` - Updated to use `get_risk_model()`
- ✅ `trading_agent.py` - Already uses `model_factory.get_model()`

### Agents die ModelFactory al Gebruiken
Deze agents gebruiken al `model_factory.get_model()` en werken met OpenRouter:
- `rbi_agent.py`
- `rbi_agent_v2.py`
- `rbi_agent_v3.py`
- `research_agent.py`
- `million_agent.py`
- `focus_agent.py`
- `code_runner_agent.py`
- `compliance_agent.py`
- `clips_agent.py`
- `chat_agent_ad.py`
- `chat_agent_og.py`
- `realtime_clips_agent.py`
- `stream_agent.py`
- `tiktok_agent.py`

Deze agents zijn **compatible** met OpenRouter zonder wijzigingen, maar kunnen worden geoptimaliseerd met de nieuwe helper functions.

---

## 🔧 Update Pattern

### Oude Pattern (Direct API Clients)

```python
import anthropic
import openai

class MyAgent:
    def __init__(self):
        anthropic_key = os.getenv("ANTHROPIC_KEY")
        self.client = anthropic.Anthropic(api_key=anthropic_key)

    def analyze(self, data):
        message = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": "Analyze this data..."
            }]
        )
        return message.content
```

### Nieuwe Pattern (OpenRouter via Helper)

```python
from src.agents.model_helper import get_agent_model, get_model_for_task

class MyAgent:
    def __init__(self):
        # Option 1: Use config defaults (RECOMMENDED)
        self.model = get_agent_model()

        # Option 2: Task-optimized model
        self.model = get_model_for_task('trading')  # or 'risk', 'research', 'chat', etc.

        # Option 3: Specific model override
        self.model = get_agent_model(
            provider='openrouter',
            model_name='deepseek/deepseek-reasoner'
        )

        if not self.model:
            raise ValueError("Failed to initialize AI model!")

    def analyze(self, data):
        response = self.model.generate_response(
            system_prompt="You are an AI assistant...",
            user_content="Analyze this data...",
            temperature=0.7,
            max_tokens=1024
        )

        # Handle response
        if response and hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
```

---

## 📋 Update Checklist

Voor elke agent die je update:

### 1. **Imports Wijzigen**

```python
# REMOVE deze imports:
import anthropic
import openai
from anthropic import Anthropic
from openai import OpenAI

# ADD deze import:
from src.agents.model_helper import get_agent_model
# Or task-specific:
from src.agents.model_helper import get_trading_model, get_risk_model, get_research_model
```

### 2. **Initialization Updaten**

```python
# OUDE CODE (REMOVE):
anthropic_key = os.getenv("ANTHROPIC_KEY")
if not anthropic_key:
    raise ValueError("ANTHROPIC_KEY not found!")
self.client = anthropic.Anthropic(api_key=anthropic_key)

# NIEUWE CODE (ADD):
self.model = get_agent_model()  # Uses config.py defaults
if not self.model:
    raise ValueError("Failed to initialize AI model!")
```

### 3. **API Calls Vervangen**

```python
# OUDE ANTHROPIC CODE (REMOVE):
message = self.client.messages.create(
    model="claude-3-haiku-20240307",
    max_tokens=1024,
    temperature=0.7,
    messages=[{
        "role": "user",
        "content": prompt
    }]
)
response_text = message.content

# OUDE OPENAI CODE (REMOVE):
response = self.client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=1024
)
response_text = response.choices[0].message.content

# NIEUWE CODE (ADD):
response = self.model.generate_response(
    system_prompt="You are...",
    user_content=prompt,
    temperature=0.7,
    max_tokens=1024
)

if response and hasattr(response, 'content'):
    response_text = response.content
else:
    response_text = str(response)
```

### 4. **Config Parameters**

```python
# Use config.py for parameters
from src import config

temperature = config.AI_TEMPERATURE
max_tokens = config.AI_MAX_TOKENS
```

---

## 🎯 Task-Specific Optimization

Voor betere cost/performance optimization, gebruik task-specific helpers:

### Trading Decisions (High Stakes)
```python
from src.agents.model_helper import get_trading_model

self.model = get_trading_model()
# Uses: anthropic/claude-3.5-sonnet via OpenRouter
```

### Risk Management
```python
from src.agents.model_helper import get_risk_model

self.model = get_risk_model()
# Uses: anthropic/claude-3.5-sonnet via OpenRouter
```

### Research & Strategy Development
```python
from src.agents.model_helper import get_research_model

self.model = get_research_model()
# Uses: deepseek/deepseek-reasoner via OpenRouter (best reasoning value)
```

### Chat, Tweets, Simple Content
```python
from src.agents.model_helper import get_chat_model

self.model = get_chat_model()
# Uses: mistralai/mistral-small via OpenRouter (cheapest)
```

### Video/Content Creation
```python
from src.agents.model_helper import get_content_model

self.model = get_content_model()
# Uses: anthropic/claude-3-haiku via OpenRouter (fast & creative)
```

---

## 🧪 Testing Updated Agent

```python
# Test standalone
python src/agents/your_agent.py

# Check for errors
# - Model initialization should work
# - API calls should succeed
# - Response parsing should work
```

---

## 📝 Example: Complete Before/After

### Before (risk_agent.py - Old Pattern)

```python
import anthropic
import openai

class RiskAgent:
    def __init__(self):
        anthropic_key = os.getenv("ANTHROPIC_KEY")
        openai_key = os.getenv("OPENAI_KEY")

        if not anthropic_key:
            raise ValueError("ANTHROPIC_KEY not found!")

        self.client = anthropic.Anthropic(api_key=anthropic_key)
        self.ai_model = "claude-3-haiku-20240307"

    def check_risk(self, data):
        message = self.client.messages.create(
            model=self.ai_model,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"Analyze risk: {data}"
            }]
        )
        return str(message.content)
```

### After (risk_agent.py - New Pattern)

```python
from src.agents.model_helper import get_risk_model
from src import config

class RiskAgent:
    def __init__(self):
        # Get risk-optimized model (uses OpenRouter)
        self.model = get_risk_model()

        if not self.model:
            raise ValueError("Failed to initialize AI model!")

        self.ai_temperature = config.AI_TEMPERATURE
        self.ai_max_tokens = config.AI_MAX_TOKENS

    def check_risk(self, data):
        response = self.model.generate_response(
            system_prompt="You are a risk management AI.",
            user_content=f"Analyze risk: {data}",
            temperature=self.ai_temperature,
            max_tokens=self.ai_max_tokens
        )

        if response and hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
```

---

## ✅ Benefits of New Pattern

1. **Één API Key** - `OPENROUTER_API_KEY` in plaats van 5+ keys
2. **Automatische Failover** - Als provider down is, switched OpenRouter automatisch
3. **Cost Optimization** - Kies beste model per agent/taak
4. **Unified Interface** - Zelfde code werkt voor alle providers
5. **Easy Testing** - Switch tussen providers voor testing
6. **Better Monitoring** - Centraal OpenRouter dashboard voor alle usage

---

## 🆘 Common Issues

### Issue: "Failed to initialize AI model"
**Solution**: Check `.env` has `OPENROUTER_API_KEY` set

### Issue: "No module named 'model_helper'"
**Solution**: Make sure you're importing from correct path:
```python
from src.agents.model_helper import get_agent_model
```

### Issue: Response format different
**Solution**: Always handle response consistently:
```python
if response and hasattr(response, 'content'):
    text = response.content
else:
    text = str(response)
```

---

## 📊 Priority Update Order

Update agents in this order:

### High Priority (Business Critical)
1. ✅ `risk_agent.py` - DONE
2. ✅ `trading_agent.py` - Already uses ModelFactory
3. `sentiment_agent.py`
4. `whale_agent.py`
5. `funding_agent.py`

### Medium Priority (Frequently Used)
6. `chartanalysis_agent.py`
7. `copybot_agent.py`
8. `tweet_agent.py`
9. `chat_agent.py`

### Low Priority (Less Frequently Used)
10. Other specialized agents

---

## 💡 Pro Tips

1. **Start with config defaults** - Let `get_agent_model()` use config.py settings
2. **Optimize per agent** - Use task-specific helpers for better cost/performance
3. **Test thoroughly** - Run agent standalone after updating
4. **Check response format** - Different providers may return slightly different formats
5. **Monitor costs** - Use OpenRouter dashboard to track spending per model

---

**Need Help?** Check:
- `src/agents/model_helper.py` - Helper implementation
- `src/agents/risk_agent.py` - Reference updated agent
- `src/models/README.md` - Model documentation
- `QUICKSTART.md` - OpenRouter setup

**Built with 💖 by Moon Dev 🌙**
