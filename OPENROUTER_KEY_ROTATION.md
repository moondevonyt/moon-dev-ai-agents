# 🔄 OpenRouter API Key Rotation System

## 📋 Übersicht

Das System unterstützt **automatische API-Key-Rotation** für OpenRouter, um das 50-Requests-pro-Tag-Limit der Free-Modelle zu umgehen.

## 🎯 Funktionsweise

### **Automatische Key-Rotation**
- System startet mit `OPENROUTER_API_KEY_1`
- Bei Rate-Limit-Fehler (429) wechselt es automatisch zu `OPENROUTER_API_KEY_2`
- Fortsetzung bis alle 11 Keys (oder mehr) durchlaufen sind
- **550 kostenlose Requests/Tag** mit 11 Keys (11 × 50)

### **Intelligentes Tracking**
- Keys, die das Limit erreicht haben, werden für den aktuellen Tag markiert
- System überspringt markierte Keys bei Rotation
- Keine doppelten Versuche mit erschöpften Keys

### **Automatische Pause & Telegram-Benachrichtigungen** 🆕
- 📱 **Telegram-Alerts** bei Key-Rotation und wenn alle Keys erschöpft sind
- ⏸️ **Auto-Pause**: System pausiert automatisch wenn alle Keys das Limit erreicht haben
- ⏰ **Auto-Resume**: Startet automatisch um 00:00 UTC neu (wenn Limits zurückgesetzt werden)
- 📬 Du erhältst eine Nachricht wenn das System wieder läuft

👉 **Setup:** Siehe [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md) für 5-Minuten-Anleitung

## 🔧 Konfiguration

### **1. API Keys in .env hinzufügen**

Kopiere deine `.env_example` zu `.env` und füge deine OpenRouter API Keys ein:

```bash
# OpenRouter API Keys (with automatic rotation for free models)
# Free models have 50 requests/day limit per key
# System automatically rotates to next key when limit is reached
# Add up to 20 keys: OPENROUTER_API_KEY_1 to OPENROUTER_API_KEY_20

OPENROUTER_API_KEY_1=sk-or-v1-xxxxxxxxxxxxx
OPENROUTER_API_KEY_2=sk-or-v1-xxxxxxxxxxxxx
OPENROUTER_API_KEY_3=sk-or-v1-xxxxxxxxxxxxx
OPENROUTER_API_KEY_4=sk-or-v1-xxxxxxxxxxxxx
OPENROUTER_API_KEY_5=sk-or-v1-xxxxxxxxxxxxx
OPENROUTER_API_KEY_6=sk-or-v1-xxxxxxxxxxxxx
OPENROUTER_API_KEY_7=sk-or-v1-xxxxxxxxxxxxx
OPENROUTER_API_KEY_8=sk-or-v1-xxxxxxxxxxxxx
OPENROUTER_API_KEY_9=sk-or-v1-xxxxxxxxxxxxx
OPENROUTER_API_KEY_10=sk-or-v1-xxxxxxxxxxxxx
OPENROUTER_API_KEY_11=sk-or-v1-xxxxxxxxxxxxx
# Add more keys if needed (up to OPENROUTER_API_KEY_20)
```

### **2. Keys generieren**

1. Gehe zu [OpenRouter Keys](https://openrouter.ai/keys)
2. Erstelle 11 (oder mehr) API Keys
3. Füge sie in deine `.env` Datei ein

⚠️ **Wichtig:** Nummerierung muss fortlaufend sein (1, 2, 3, ..., 11)

### **3. Telegram Bot Setup (Optional aber empfohlen)**

Für Benachrichtigungen bei Key-Rotation und System-Pause:

```bash
# In .env hinzufügen:
TELEGRAM_BOT_TOKEN=dein_bot_token_hier
TELEGRAM_CHAT_ID=deine_chat_id_hier
```

📱 **Komplette Anleitung:** [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md)

## 📊 Verfügbare Free-Modelle

Das System nutzt standardmäßig:

```python
# DeepSeek Chat FREE - 50 requests pro Tag pro Key
"deepseek/deepseek-chat-v3-0324:free"

# DeepSeek Reasoner FREE - 50 requests pro Tag pro Key  
"deepseek/deepseek-r1-0528:free"
```

### **Modell wechseln**

```python
from src.models.model_factory import model_factory

# Hole OpenRouter Model mit anderem Modell
model = model_factory.get_model(
    "openrouter", 
    model_name="deepseek/deepseek-r1-0528:free"  # Reasoner Model
)
```

## 💡 Verwendung im Code

### **Automatische Nutzung**

Das System ist bereits in `ModelFactory` integriert:

```python
from src.models.model_factory import model_factory

# Model wird mit allen verfügbaren Keys initialisiert
model = model_factory.get_model("openrouter")

# Generate response - Key-Rotation erfolgt automatisch bei Limit
response = model.generate_response(
    system_prompt="Du bist ein hilfreicher Assistent.",
    user_content="Analysiere den Markt.",
    temperature=0.7
)
```

### **Manuelle Initialisierung**

Falls du `OpenRouterModel` direkt nutzen willst:

```python
from src.models.openrouter_model import OpenRouterModel
import os

# Lade alle Keys aus Environment
keys = [
    os.getenv(f"OPENROUTER_API_KEY_{i}") 
    for i in range(1, 12)
    if os.getenv(f"OPENROUTER_API_KEY_{i}")
]

# Initialisiere mit Key-Liste
model = OpenRouterModel(
    api_keys=keys,
    model_name="deepseek/deepseek-chat-v3-0324:free"
)
```

## 🔍 Log-Ausgaben

Das System zeigt detaillierte Informationen:

```
🌙 Moon Dev's OpenRouter Model Initialization
🔑 API Keys validation:
  ├─ Total keys provided: 11
  ├─ Key 1: 64 chars - Starts with 'sk-or-': yes
  ├─ Key 2: 64 chars - Starts with 'sk-or-': yes
  ...
  └─ ✅ Key rotation system initialized

🔌 Initializing OpenRouter client...
  ├─ Using API Key #1 of 11
  └─ ✅ OpenRouter client created

⚠️  OpenRouter rate limit exceeded for Key #1
   Model: deepseek/deepseek-chat-v3-0324:free
   
🔄 Rotating to API Key #2
✅ Successfully switched to Key #2
   💡 Retrying with next API key...
```

## 📈 Kapazität

Mit 11 Keys erhältst du:

- **550 Requests/Tag** (11 × 50)
- **16,500 Requests/Monat** (550 × 30)
- **Unbegrenzte Tokens** (keine Token-Limits bei Free-Modellen)

### **Mehr Keys hinzufügen**

Das System unterstützt bis zu **20 Keys**:

```bash
OPENROUTER_API_KEY_12=sk-or-v1-xxxxxxxxxxxxx
OPENROUTER_API_KEY_13=sk-or-v1-xxxxxxxxxxxxx
...
OPENROUTER_API_KEY_20=sk-or-v1-xxxxxxxxxxxxx
```

= **1,000 Requests/Tag** mit 20 Keys! 🚀

## 🛠️ Technische Details

### **Code-Struktur**

```
src/models/
├── openrouter_model.py     # OpenRouterModel mit Key-Rotation
└── model_factory.py         # Factory lädt alle Keys automatisch

.env                          # Deine API Keys hier
.env_example                  # Template mit Anleitung
```

### **Key-Rotation-Logik**

1. **Initialization**: Lädt alle `OPENROUTER_API_KEY_*` Keys aus `.env`
2. **Request**: Nutzt aktuellen Key (startet mit Index 0)
3. **Rate Limit (429)**: 
   - Markiert aktuellen Key als erschöpft
   - Rotiert zu nächstem verfügbaren Key
   - Retry mit neuem Key
4. **Alle Keys erschöpft**: Gibt `None` zurück

### **Fehlerbehandlung**

```python
# System behandelt automatisch:
# - 429: Rate Limit → Key-Rotation
# - 402: Keine Credits → Error (nicht bei Free-Modellen)
# - 401: Ungültiger Key → Skip zu nächstem Key
# - 503: Service unavailable → Exception (für Retry-Logik)
```

## 🎓 Best Practices

### **Key-Management**

1. ✅ **Nutze separate Keys** - Erstelle für jede Anwendung eigene Keys
2. ✅ **Rotiere regelmäßig** - Erneuere Keys alle paar Monate
3. ✅ **Sichere Speicherung** - `.env` nie ins Git committen!
4. ✅ **Monitoring** - Behalte Log-Outputs im Auge

### **Performance-Optimierung**

```python
# Wenn du weißt, dass viele Requests kommen:
# Füge mehr Keys hinzu BEVOR du startest
# System nutzt dann automatisch alle verfügbaren Keys
```

### **Debugging**

```python
# Prüfe welcher Key aktuell genutzt wird:
print(f"Current key index: {model.current_key_index + 1}")
print(f"Failed keys today: {model.failed_keys_today}")
print(f"Total keys: {len(model.api_keys)}")
```

## 🚨 Troubleshooting

### **Problem: "No API keys found"**

```bash
# Prüfe .env Datei
cat .env | grep OPENROUTER

# Stelle sicher dass Keys nummeriert sind (1, 2, 3, ...)
# NICHT (0, 1, 2, ...) oder (01, 02, 03, ...)
```

### **Problem: "All keys exhausted"**

Das bedeutet alle 11 Keys haben ihr Tageslimit erreicht.

**Lösungen:**
1. Warte bis nächster Tag (Limit resettet um 00:00 UTC)
2. Füge mehr Keys hinzu (bis zu 20 möglich)
3. Upgrade zu OpenRouter Credits für unbegrenzte Requests

### **Problem: Keys funktionieren nicht**

```python
# Teste Keys einzeln:
import os
from openai import OpenAI

for i in range(1, 12):
    key = os.getenv(f"OPENROUTER_API_KEY_{i}")
    if key:
        try:
            client = OpenAI(
                api_key=key,
                base_url="https://openrouter.ai/api/v1"
            )
            response = client.chat.completions.create(
                model="deepseek/deepseek-chat-v3-0324:free",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )
            print(f"✅ Key {i} works")
        except Exception as e:
            print(f"❌ Key {i} failed: {e}")
```

## 📚 Weiterführende Links

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/docs#models)
- [OpenRouter API Keys](https://openrouter.ai/keys)
- [DeepSeek Models Info](https://openrouter.ai/models/deepseek)

---

**🌙 Built with love by Moon Dev 🚀**
