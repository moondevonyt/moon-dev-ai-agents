# 🚀 OpenRouter Integration - Quick Start

## ⚡ In 3 Schritten loslegen

### **1️⃣ OpenRouter API Keys generieren**

1. Gehe zu [OpenRouter Keys](https://openrouter.ai/keys)
2. Erstelle **11 API Keys** (oder mehr, bis zu 20)
3. Kopiere jeden Key

### **2️⃣ Keys in .env eintragen**

Öffne deine `.env` Datei und füge hinzu:

```bash
# OpenRouter API Keys (11 Keys = 550 kostenlose Requests/Tag)
OPENROUTER_API_KEY_1=sk-or-v1-dein-erster-key-hier
OPENROUTER_API_KEY_2=sk-or-v1-dein-zweiter-key-hier
OPENROUTER_API_KEY_3=sk-or-v1-dein-dritter-key-hier
OPENROUTER_API_KEY_4=sk-or-v1-...
OPENROUTER_API_KEY_5=sk-or-v1-...
OPENROUTER_API_KEY_6=sk-or-v1-...
OPENROUTER_API_KEY_7=sk-or-v1-...
OPENROUTER_API_KEY_8=sk-or-v1-...
OPENROUTER_API_KEY_9=sk-or-v1-...
OPENROUTER_API_KEY_10=sk-or-v1-...
OPENROUTER_API_KEY_11=sk-or-v1-...
```

### **3️⃣ Telegram Bot erstellen (Optional)**

Für Benachrichtigungen wenn Keys das Limit erreichen:

```bash
# Telegram Credentials
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

**Setup-Anleitung:** [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md) (dauert 5 Minuten)

## ✅ System testen

```bash
python test_openrouter_rotation.py
```

Das Script testet:
- ✅ API Keys konfiguriert
- ✅ Telegram funktioniert (optional)
- ✅ OpenRouter Model antwortet
- ✅ Key-Rotation funktioniert

## 🎯 Verwendung

### **Option A: Automatisch (Empfohlen)**

Das System nutzt OpenRouter standardmäßig - einfach starten! 🚀

```python
from src.models.model_factory import model_factory

# Model wird automatisch mit allen Keys initialisiert
model = model_factory.get_model("openrouter")

# Key-Rotation passiert automatisch!
response = model.generate_response(
    system_prompt="Du bist ein Trading-Experte.",
    user_content="Analysiere BTC."
)
```

### **Option B: In Agents nutzen**

Ändere einfach die Model-Config:

```python
# Vorher:
MODEL_TYPE = "deepseek"
MODEL_NAME = "deepseek-reasoner"

# Nachher:
MODEL_TYPE = "openrouter"
MODEL_NAME = "deepseek/deepseek-chat-v3-0324:free"
```

Fertig! Das System nutzt jetzt automatisch alle 11 Keys mit Rotation! 🎉

## 📊 Was du bekommst

| Feature | Beschreibung |
|---------|--------------|
| **550+ Requests/Tag** | Mit 11 Keys × 50 Requests |
| **Automatische Key-Rotation** | Bei Rate-Limit (429) wechselt System automatisch |
| **Telegram-Benachrichtigungen** | Alert bei Key-Rotation & System-Pause |
| **Auto-Pause** | System pausiert wenn alle Keys erschöpft sind |
| **Auto-Resume** | Startet automatisch um 00:00 UTC neu |
| **100% Kostenlos** | Free DeepSeek Models |

## 🔔 Benachrichtigungs-Flow

```
Request 1-50   → Key #1 ✅
Request 51     → Key #1 limit reached (429)
               → 🔄 Auto-rotate to Key #2
               → 📱 Telegram: "Switched to Key #2/11"
               
Request 51-100 → Key #2 ✅
...

Request 551    → All 11 keys exhausted
               → ⏸️ System PAUSED
               → 📱 Telegram: "All keys exhausted, pausing until 00:00 UTC"
               → ⏰ Wait for reset...
               
00:00 UTC      → Rate limits reset
               → ✅ System RESUMED  
               → 📱 Telegram: "System operational again"
```

## 🆘 Troubleshooting

### **Problem: "No API keys found"**

```bash
# Prüfe .env Datei:
cat .env | grep OPENROUTER_API_KEY

# Stelle sicher dass Keys nummeriert sind (1, 2, 3, ...)
```

### **Problem: "Telegram not enabled"**

```bash
# Prüfe Telegram Credentials:
cat .env | grep TELEGRAM

# Optional - System funktioniert auch ohne Telegram!
```

### **Problem: Keys funktionieren nicht**

```bash
# Teste Keys einzeln:
python test_openrouter_rotation.py

# Oder manuell testen:
# 1. Gehe zu https://openrouter.ai/keys
# 2. Prüfe ob Keys aktiv sind
# 3. Erstelle neue Keys falls nötig
```

## 📚 Vollständige Dokumentation

- **[OPENROUTER_KEY_ROTATION.md](OPENROUTER_KEY_ROTATION.md)** - Detaillierte Anleitung
- **[TELEGRAM_SETUP.md](TELEGRAM_SETUP.md)** - Telegram Bot Setup
- **[CHANGELOG_OPENROUTER.md](CHANGELOG_OPENROUTER.md)** - Was wurde geändert
- **[test_openrouter_rotation.py](test_openrouter_rotation.py)** - Test-Script

## 💡 Pro-Tips

### **Mehr Kapazität gewünscht?**

Füge einfach mehr Keys hinzu (bis zu 20):

```bash
OPENROUTER_API_KEY_12=sk-or-v1-...
OPENROUTER_API_KEY_13=sk-or-v1-...
# ... bis 20
```

= **1,000 Requests/Tag kostenlos!** 🚀

### **Verschiedene Modelle nutzen?**

```python
# DeepSeek Chat (Standard)
model = model_factory.get_model(
    "openrouter",
    "deepseek/deepseek-chat-v3-0324:free"
)

# DeepSeek Reasoner (für komplexe Analysen)
model = model_factory.get_model(
    "openrouter", 
    "deepseek/deepseek-r1-0528:free"
)
```

### **Custom Telegram-Alerts?**

```python
from src.utils.telegram_notifier import get_telegram_notifier

notifier = get_telegram_notifier()

# Trade executed
notifier.send_message(
    "💰 <b>Trade Executed</b>\n"
    f"BTC-USDT: +5% profit!"
)
```

## 🎉 Fertig!

Du hast jetzt:
- ✅ Automatische Key-Rotation
- ✅ 550+ kostenlose Requests/Tag
- ✅ Telegram-Benachrichtigungen
- ✅ Auto-Pause/Resume

**Keine monatlichen Kosten, volle Power! 🌙**

---

## 🔗 Support & Links

- [OpenRouter Dokumentation](https://openrouter.ai/docs)
- [OpenRouter API Keys](https://openrouter.ai/keys)
- [Telegram Bot API](https://core.telegram.org/bots/api)

**Bei Fragen:** Siehe vollständige Docs oben ☝️

---

**🌙 Built with love by Moon Dev 🚀**
