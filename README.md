# 🤖 AI AGENTS FOR TRADING

<p align="center">
  <a href="https://www.moondev.com/"><img src="moondev.png" width="300" alt="Moon Dev"></a>
</p>

## 🎯 Vision

ai agents are clearly the future and the entire workforce will be replaced or atleast using ai agents. while i am a quant and building agents for algo trading i will be contributing to all different types of ai agent flows and placing all of the agents here for free, 100% open sourced because i beleive code is the great equalizer and we have never seen a regime shift like this so i need to get this code to the people

feel free to join [our discord](https://discord.gg/8UPuVZ53bh) if you beleive ai agents will be integrated into the workforce

## Video Updates & Training

⭐️ [first full concise documentation video (watch here)](https://youtu.be/RlqzkSgDKDc)

## 🔌 Multi-Provider LLM Support

This project now includes a provider-agnostic LLM client interface that supports multiple LLM providers including OpenAI, Groq, and Ollama. You can easily switch between providers without changing your code.

### Configuration

Set up your LLM provider using environment variables:

#### Using OpenAI:
```bash
export LLM_PROVIDER=openai
export LLM_API_KEY=your_openai_api_key
export LLM_MODEL=gpt-4
```

#### Using Groq:
```bash
export LLM_PROVIDER=groq
export LLM_API_KEY=your_groq_api_key
export LLM_MODEL=mixtral-8x7b-32768
```

#### Using Ollama (local):
```bash
export LLM_PROVIDER=ollama
export LLM_BASE_URL=http://localhost:11434  # Optional, defaults to localhost:11434
export LLM_MODEL=llama2
```

### Usage Example

```python
from src.llm import LLMClientFactory, ChatMessage

# Create client from environment variables
client = LLMClientFactory.create_from_env()

# Or create with explicit configuration
client = LLMClientFactory.create_client(
    provider="groq",
    config={"api_key": "your_api_key"}
)

# Use the client
messages = [ChatMessage(role="user", content="Hello!")]
response = client.chat(messages, model="mixtral-8x7b-32768")
print(response.content)
```

### Supported Providers

- **OpenAI**: Official OpenAI API (GPT-4, GPT-3.5, etc.)
- **OpenAI-Compatible**: Any OpenAI-compatible API (xAI, DeepSeek, etc.) - set custom `base_url`
- **Groq**: Fast inference with Mixtral, Llama, and other models
- **Ollama**: Local model inference

### Running Tests

```bash
pytest tests/test_llm_client.py
```

---

*For more information about the trading agents and other features, please refer to the sections below.*
