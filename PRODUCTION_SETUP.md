# 🚀 Production Setup Guide
## Moon Dev AI Trading Agents - Veilige Productie Deployment

Deze guide helpt je het systeem veilig en efficiënt in productie te nemen met OpenRouter als unified LLM provider.

---

## 📋 Pre-Productie Checklist

### 1. API Keys Veiligheid

#### ✅ Verplichte Security Checks:

```bash
# Check of .env NIET in git zit
git check-ignore .env
# Output moet zijn: .env

# Scan voor exposed secrets in git history
git log --all --full-history -- .env
# Output moet LEEG zijn

# Check voor hardcoded API keys in code
grep -r "sk-" src/ --include="*.py" | grep -v ".env"
grep -r "api_key.*=" src/ --include="*.py" | grep -v "os.getenv"
# Output moet LEEG zijn of alleen os.getenv() calls tonen
```

#### 🔐 API Key Best Practices:

**NOOIT:**
- API keys in code hardcoden
- API keys in git committen
- API keys in screenshots/videos tonen
- API keys via unsecure channels delen

**ALTIJD:**
- Gebruik `.env` voor alle secrets
- Gebruik environment variables in productie
- Roteer keys regelmatig (elke 90 dagen)
- Gebruik verschillende keys voor dev/staging/prod
- Monitor API usage voor onverwachte spikes

---

## 🌐 OpenRouter Setup (RECOMMENDED)

### Waarom OpenRouter voor Productie?

**Kosten Besparing:**
- Eén API key in plaats van 5+ keys beheren
- Eenvoudiger billing en cost tracking
- Automatisch de goedkoopste provider kiezen per model

**Betrouwbaarheid:**
- Automatische failover als één provider down is
- Load balancing over meerdere providers
- Geen vendor lock-in

**Eenvoud:**
- Eén integration point
- Consistent API over alle models
- Makkelijker rate limit management

### Stap 1: OpenRouter Account

1. Ga naar: https://openrouter.ai/keys
2. Maak een account (gratis)
3. Voeg credits toe: https://openrouter.ai/credits
   - **Aanbeveling**: Start met $50 voor testing
   - Productie: $200-500 afhankelijk van volume
4. Genereer API key

### Stap 2: Environment Configuration

```bash
# Kopieer example naar .env
cp .env_example .env

# Edit .env en voeg toe:
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Verifieer .env is in .gitignore
cat .gitignore | grep .env
```

### Stap 3: Config Aanpassen

Open `src/config.py` en verifieer:

```python
# AI Model Settings 🤖
AI_PROVIDER = "openrouter"  # Gebruik OpenRouter
AI_MODEL = "anthropic/claude-3.5-sonnet"  # Of kies je preferred model
AI_MAX_TOKENS = 4096
AI_TEMPERATURE = 0.7
```

**Model Keuze voor Productie:**

| Use Case | Model | Cost | Speed |
|----------|-------|------|-------|
| **Best Balance** | `anthropic/claude-3.5-sonnet` | $3/$15 per 1M | Fast |
| **Cheapest** | `mistralai/mistral-small` | $0.20/$0.60 per 1M | Very Fast |
| **Best Reasoning** | `deepseek/deepseek-reasoner` | $0.55/$2.19 per 1M | Fast |
| **Fastest** | `anthropic/claude-3-haiku` | $0.25/$1.25 per 1M | Very Fast |
| **Most Powerful** | `openai/o1` | $15/$60 per 1M | Slow |

### Stap 4: Test de Setup

```bash
# Activeer environment
conda activate tflow

# Test OpenRouter connectivity
python -c "
from src.models.model_factory import ModelFactory
factory = ModelFactory()
model = factory.get_model('openrouter', 'anthropic/claude-3.5-sonnet')
response = model.generate_response(
    'You are a test assistant',
    'Say hello if you can read this',
    temperature=0.7,
    max_tokens=100
)
print(response.content)
"
```

Expected output: Model geeft een greeting response terug.

---

## 🛡️ Security Hardening

### Environment Variables voor Productie

Voor productie servers (Linux/Docker), gebruik systemd environment files:

```bash
# /etc/systemd/system/moon-trading.env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
BIRDEYE_API_KEY=your-key-here
RPC_ENDPOINT=your-rpc-here
SOLANA_PRIVATE_KEY=your-key-here
```

```bash
# Set restrictive permissions
sudo chmod 600 /etc/systemd/system/moon-trading.env
sudo chown moon-trading:moon-trading /etc/systemd/system/moon-trading.env
```

### Docker Secrets (Recommended voor Docker)

```yaml
# docker-compose.yml
version: '3.8'
services:
  moon-trading:
    image: moon-trading:latest
    env_file:
      - .env.production
    secrets:
      - openrouter_key
      - solana_key

secrets:
  openrouter_key:
    file: ./secrets/openrouter_key.txt
  solana_key:
    file: ./secrets/solana_key.txt
```

### Cloud Secrets Management

**AWS Secrets Manager:**
```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# In je code:
secrets = get_secret('moon-trading/production')
OPENROUTER_API_KEY = secrets['OPENROUTER_API_KEY']
```

**Google Cloud Secret Manager:**
```python
from google.cloud import secretmanager

def get_secret(project_id, secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8')

OPENROUTER_API_KEY = get_secret('my-project', 'openrouter-key')
```

---

## 📊 Monitoring & Cost Control

### OpenRouter Dashboard

1. Login op https://openrouter.ai
2. Dashboard toont:
   - Real-time spending
   - Requests per model
   - Error rates
   - Latency metrics

### Cost Alerts Setup

```python
# src/monitoring/cost_tracker.py
import os
from datetime import datetime

class CostTracker:
    def __init__(self, daily_budget=50):
        self.daily_budget = daily_budget
        self.log_file = 'src/data/cost_log.csv'

    def check_budget(self):
        """Check if we're within budget"""
        # Implement tracking logic
        pass

    def alert_if_over_budget(self):
        """Send alert if over budget"""
        pass
```

### Rate Limiting

```python
# src/config.py toevoegen:

# Rate Limiting (prevent runaway costs)
MAX_API_CALLS_PER_HOUR = 1000
MAX_DAILY_COST_USD = 100

# Agent Sleep Times (prevent overuse)
SLEEP_BETWEEN_RUNS_MINUTES = 15  # Al ingesteld
```

---

## 🔄 Deployment Workflow

### Development → Staging → Production

```bash
# 1. Development (lokaal)
AI_PROVIDER=openrouter
AI_MODEL=mistralai/mistral-small  # Goedkoop voor testing

# 2. Staging
AI_PROVIDER=openrouter
AI_MODEL=anthropic/claude-3-haiku  # Balance cost/quality

# 3. Production
AI_PROVIDER=openrouter
AI_MODEL=anthropic/claude-3.5-sonnet  # Best quality
```

### Continuous Deployment

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Deploy
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          SOLANA_PRIVATE_KEY: ${{ secrets.SOLANA_PRIVATE_KEY }}
        run: |
          # Je deployment script
          ./deploy.sh
```

---

## 🚨 Incident Response

### API Key Compromised

**Immediate Actions:**
1. Revoke compromised key via provider dashboard
2. Generate new key
3. Update `.env` en herstart services
4. Check audit logs voor ongeautoriseerd gebruik
5. File support ticket als er ongeautoriseerde charges zijn

**OpenRouter Key Rotation:**
```bash
# 1. Generate new key at https://openrouter.ai/keys
# 2. Update .env
OPENROUTER_API_KEY=sk-or-v1-NEW-KEY-HERE

# 3. Restart services
systemctl restart moon-trading

# 4. Revoke old key
```

### High Costs Alert

```bash
# Check OpenRouter dashboard:
https://openrouter.ai/activity

# Check which agent is using most tokens:
grep "tokens" src/data/*/logs/*.log | sort -t: -k3 -n

# Temporarily disable high-cost agents in main.py:
ACTIVE_AGENTS = {
    "risk_agent": True,
    "trading_agent": False,  # Disabled until costs reviewed
    # ...
}
```

---

## 📈 Performance Optimization

### Model Selection per Agent

Niet alle agents hebben dezelfde LLM kracht nodig:

```python
# In each agent file, customize:

# High-stakes decisions (trading_agent, risk_agent)
model = factory.get_model("openrouter", "anthropic/claude-3.5-sonnet")

# Medium complexity (sentiment_agent, chart_agent)
model = factory.get_model("openrouter", "anthropic/claude-3-haiku")

# Simple tasks (tweet_agent, chat_agent)
model = factory.get_model("openrouter", "mistralai/mistral-small")

# Heavy reasoning (rbi_agent, research_agent)
model = factory.get_model("openrouter", "deepseek/deepseek-reasoner")
```

### Caching Strategy

```python
# Implement response caching for repeated queries
import hashlib
import json

def cached_llm_call(prompt, cache_hours=24):
    cache_key = hashlib.md5(prompt.encode()).hexdigest()
    cache_file = f'src/data/cache/{cache_key}.json'

    # Check cache
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            cached = json.load(f)
            if time.time() - cached['timestamp'] < cache_hours * 3600:
                return cached['response']

    # Make API call
    response = model.generate_response(...)

    # Save to cache
    with open(cache_file, 'w') as f:
        json.dump({
            'timestamp': time.time(),
            'response': response
        }, f)

    return response
```

---

## ✅ Production Checklist

Voordat je live gaat:

- [ ] `.env` file bestaat en bevat `OPENROUTER_API_KEY`
- [ ] `.env` is in `.gitignore` en NIET in git
- [ ] API key getest en werkt
- [ ] Model keuze gemaakt (zie tabel hierboven)
- [ ] Cost alerts ingesteld op OpenRouter dashboard
- [ ] Daily budget limiet ingesteld
- [ ] Monitoring/logging actief
- [ ] Backup API key gegenereerd en veilig opgeslagen
- [ ] Incident response plan bekend bij team
- [ ] Rate limiting geconfigureerd
- [ ] Agent sleep times ingesteld (voorkomen overtrading)
- [ ] Alle tests passed: `python -m pytest tests/`

---

## 🆘 Support

**OpenRouter Issues:**
- Dashboard: https://openrouter.ai
- Docs: https://openrouter.ai/docs
- Discord: https://discord.gg/openrouter

**Moon Dev Community:**
- Discord: Join via Moon Dev's YouTube
- GitHub Issues: https://github.com/moon-dev-ai-agents-for-trading/issues
- YouTube: [@moondevonyt](https://www.youtube.com/@moondevonyt)

---

## 📚 Aanvullende Resources

- [OpenRouter Models List](https://openrouter.ai/models)
- [OpenRouter Pricing](https://openrouter.ai/models)
- [API Key Security Best Practices](https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_password)
- [Moon Dev's Model Factory README](src/models/README.md)

---

**Built with 💖 by Moon Dev 🌙**

*Laatste update: November 2025*
