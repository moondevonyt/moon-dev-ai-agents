# 🚀 Quick Start Guide - OpenRouter Integratie

## Stap 1: OpenRouter API Key Verkrijgen

1. Ga naar: https://openrouter.ai/keys
2. Maak een gratis account
3. Kopieer je API key (begint met `sk-or-v1-`)

## Stap 2: Environment Setup

```bash
# Kopieer .env_example naar .env
cp .env_example .env

# Edit .env en voeg je key toe
nano .env

# Voeg toe:
OPENROUTER_API_KEY=sk-or-v1-YOUR-KEY-HERE
```

## Stap 3: Veiligheid Checken

```bash
# Run security check
python scripts/security_check.py

# Output moet geen kritieke issues tonen
```

## Stap 4: OpenRouter Testen

```bash
# Test OpenRouter connectivity
python scripts/test_openrouter.py

# Expected: "ALL TESTS PASSED! OpenRouter is working!"
```

## Stap 5: Systeem Gebruiken

```bash
# Activeer conda environment
conda activate tflow

# Run main orchestrator (alle agents)
python src/main.py

# Of run individuele agent
python src/agents/trading_agent.py
```

## 📊 Model Keuze

Edit `src/config.py` om het model te wijzigen:

```python
AI_PROVIDER = "openrouter"
AI_MODEL = "anthropic/claude-3.5-sonnet"  # Best balance

# Alternatieven:
# AI_MODEL = "mistralai/mistral-small"     # Goedkoopste
# AI_MODEL = "deepseek/deepseek-reasoner"  # Best reasoning
# AI_MODEL = "openai/gpt-4o"               # OpenAI flagship
```

## 🔧 Per Agent Customization

Voor specifieke agents kun je verschillende modellen gebruiken:

```python
from src.models.model_factory import ModelFactory

factory = ModelFactory()

# Kritieke trading decisions
model = factory.get_model('openrouter', 'anthropic/claude-3.5-sonnet')

# Simpele taken (tweets, chat)
model = factory.get_model('openrouter', 'mistralai/mistral-small')

# Heavy reasoning (strategy development)
model = factory.get_model('openrouter', 'deepseek/deepseek-reasoner')
```

## 💰 Kosten Monitoring

1. Dashboard: https://openrouter.ai/activity
2. Bekijk real-time spending per model
3. Stel budget alerts in

## 🆘 Troubleshooting

### "OpenRouter is not available"
- Check of `OPENROUTER_API_KEY` in `.env` staat
- Verificeer dat de key geldig is op https://openrouter.ai/keys

### "Insufficient credits"
- Voeg credits toe: https://openrouter.ai/credits
- Start met $50 voor testing

### Import errors
- Run: `pip install -r requirements.txt`
- Activeer: `conda activate tflow`

## 📚 Meer Informatie

- **Full Production Guide**: `PRODUCTION_SETUP.md`
- **Security Best Practices**: Run `python scripts/security_check.py`
- **Model Documentation**: `src/models/README.md`
- **Project Instructions**: `CLAUDE.md`

## ✅ Production Checklist

Voordat je live gaat:

- [ ] `.env` file bevat `OPENROUTER_API_KEY`
- [ ] Security check passed: `python scripts/security_check.py`
- [ ] OpenRouter test passed: `python scripts/test_openrouter.py`
- [ ] Model keuze gemaakt in `config.py`
- [ ] Budget limiet ingesteld op OpenRouter dashboard
- [ ] `.env` is in `.gitignore` en NIET in git

---

**Klaar om te beginnen? Run:**

```bash
python scripts/test_openrouter.py
```

Als alle tests slagen, ben je klaar voor productie! 🚀

**Built with 💖 by Moon Dev 🌙**
