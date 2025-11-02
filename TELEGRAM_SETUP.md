# 📱 Telegram Bot Setup Guide

## 🎯 Übersicht

Dein Bot sendet dir automatisch Telegram-Benachrichtigungen wenn:
- Ein API Key das Rate-Limit erreicht und gewechselt wird
- Alle API Keys erschöpft sind und das System pausiert
- Das System nach Pause wieder läuft

## 🚀 Setup in 5 Minuten

### **Schritt 1: Telegram Bot erstellen**

1. Öffne Telegram und suche nach **@BotFather**
2. Starte einen Chat und sende: `/newbot`
3. Folge den Anweisungen:
   - Bot Name (z.B. "Moon Dev Trading Bot")
   - Bot Username (z.B. "moondev_trading_bot")
4. Du erhältst einen **Bot Token** wie:
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789
   ```
5. **Speichere diesen Token!** ⚠️

### **Schritt 2: Chat ID herausfinden**

**Option A: Mit userinfobot (Einfachster Weg)**
1. Suche nach **@userinfobot** in Telegram
2. Starte einen Chat
3. Der Bot zeigt dir sofort deine Chat ID (z.B. `123456789`)

**Option B: Manuell über API**
1. Sende eine beliebige Nachricht an deinen Bot
2. Öffne im Browser:
   ```
   https://api.telegram.org/bot<DEIN_BOT_TOKEN>/getUpdates
   ```
   Ersetze `<DEIN_BOT_TOKEN>` mit dem Token aus Schritt 1
3. Suche in der JSON-Antwort nach `"chat":{"id":123456789`
4. Die Zahl ist deine Chat ID

### **Schritt 3: In .env eintragen**

Öffne deine `.env` Datei und füge hinzu:

```bash
# Telegram Bot Credentials
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789
TELEGRAM_CHAT_ID=123456789
```

### **Schritt 4: Testen**

Starte deinen Bot neu. Bei der ersten API-Key-Rotation solltest du eine Nachricht erhalten! 🎉

## 📱 Test-Script

Falls du testen willst ob alles funktioniert:

```python
# test_telegram.py
from src.utils.telegram_notifier import get_telegram_notifier

# Get notifier
notifier = get_telegram_notifier()

# Send test message
if notifier.enabled:
    notifier.send_message(
        "🌙 <b>Test Nachricht</b>\n\n"
        "Wenn du diese Nachricht siehst, funktioniert alles! ✅"
    )
    print("✅ Test-Nachricht gesendet!")
else:
    print("❌ Telegram nicht konfiguriert")
```

Ausführen:
```bash
python test_telegram.py
```

## 📬 Beispiel-Benachrichtigungen

### **Key Rotation Alert**
```
🔄 API Key Rotation

⏰ Time: 2025-11-01 16:45:23
🔑 Switched to Key: #2/11
🤖 Model: deepseek/deepseek-chat-v3-0324:free

ℹ️ Previous key reached rate limit.
✅ Continuing with next available key.

🌙 Moon Dev's AI Trading Bot
```

### **Rate Limit Alert**
```
🚨 OpenRouter Rate Limit Alert

⏰ Time: 2025-11-01 18:30:15
🔑 Keys Exhausted: 11/11
🤖 Model: deepseek/deepseek-chat-v3-0324:free

❌ All API keys have reached their daily limit (50 requests/key).

💡 Actions:
• System is now paused
• Will resume at 00:00 UTC (limit reset)
• Or add more API keys to .env

🌙 Moon Dev's AI Trading Bot
```

### **System Resumed Alert**
```
✅ System Resumed

⏰ Time: 2025-11-02 00:00:05
🤖 Model: deepseek/deepseek-chat-v3-0324:free

🔄 API key limits have been reset.
✅ System is now operational again.

🌙 Moon Dev's AI Trading Bot
```

## 🔒 Sicherheit

### **Bot Token schützen**
- ✅ Speichere Token nur in `.env` (nie ins Git!)
- ✅ Teile den Token mit niemandem
- ✅ Revoke Token bei @BotFather wenn kompromittiert

### **Chat ID**
- Die Chat ID ist deine persönliche Telegram-User-ID
- Nur du kannst Nachrichten von deinem Bot empfangen
- Andere können deinen Bot nicht nutzen ohne deine Chat ID

### **.env Datei**
```bash
# .env ist in .gitignore!
# Wird NICHT ins Repository committed
# Jeder Dev hat seine eigene .env
```

## 🛠️ Troubleshooting

### **Problem: "Telegram not enabled"**

```bash
# Prüfe .env Datei
cat .env | grep TELEGRAM

# Stelle sicher dass beide Werte gesetzt sind:
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

### **Problem: "Bot doesn't send messages"**

**Check 1: Bot Token korrekt?**
```bash
# Teste im Browser:
https://api.telegram.org/bot<DEIN_TOKEN>/getMe

# Sollte Info über deinen Bot zeigen
```

**Check 2: Chat ID korrekt?**
```bash
# Hast du eine Nachricht an den Bot gesendet?
# Manche Bots können erst antworten nachdem du sie kontaktiert hast
```

**Check 3: Firewall/Proxy?**
```python
# Test ob du Telegram API erreichen kannst
import requests
r = requests.get("https://api.telegram.org")
print(r.status_code)  # Sollte 200 oder 302 sein
```

### **Problem: Bot sendet, aber ich erhalte nichts**

1. Prüfe ob du den Bot gestartet hast (in Telegram)
2. Prüfe ob Chat ID korrekt ist (siehe Schritt 2)
3. Prüfe Telegram Privacy Settings

### **Problem: "401 Unauthorized"**

Dein Bot Token ist falsch oder revoked.
- Prüfe ob Token korrekt kopiert wurde
- Keine Leerzeichen vor/nach Token
- Erstelle neuen Bot bei @BotFather falls nötig

## 🎨 Nachricht Formatierung

Telegram unterstützt **HTML** und **Markdown**.

### **HTML Beispiele:**
```python
notifier.send_message(
    "<b>Fett</b> <i>Kursiv</i> <code>Code</code>\n"
    "<a href='https://example.com'>Link</a>"
)
```

### **Markdown Beispiele:**
```python
notifier.send_message(
    "*Fett* _Kursiv_ `Code`\n"
    "[Link](https://example.com)",
    parse_mode="Markdown"
)
```

## 📚 Weitere Features

### **Custom Notifications**

Du kannst eigene Benachrichtigungen hinzufügen:

```python
from src.utils.telegram_notifier import get_telegram_notifier

notifier = get_telegram_notifier()

# Trade executed
notifier.send_message(
    "💰 <b>Trade Executed</b>\n\n"
    f"Symbol: BTC-USDT\n"
    f"Side: BUY\n"
    f"Amount: 0.5 BTC\n"
    f"Price: $45,000\n"
)

# Profit Alert
notifier.send_message(
    "📈 <b>Profit Alert!</b>\n\n"
    f"Portfolio up +5% today\n"
    f"Total: $10,500"
)
```

### **Gruppen-Support**

Du kannst den Bot auch in einer Telegram-Gruppe nutzen:

1. Füge deinen Bot zur Gruppe hinzu
2. Hole die Gruppen Chat ID (negativ, z.B. `-123456789`)
3. Nutze diese Chat ID in `.env`

Dann erhalten alle Gruppenmitglieder die Notifications!

## 📞 Support

Bei Problemen:
1. Prüfe diese Anleitung nochmal durch
2. Teste mit dem Test-Script oben
3. Check die Logs in deinem Terminal

## 🔗 Links

- [Telegram Bot API Docs](https://core.telegram.org/bots/api)
- [BotFather Commands](https://core.telegram.org/bots#6-botfather)
- [HTML Formatting](https://core.telegram.org/bots/api#html-style)

---

**🌙 Built with love by Moon Dev 🚀**
