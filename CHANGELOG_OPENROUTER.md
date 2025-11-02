# 🚀 OpenRouter Integration - Changelog

## ✨ Neue Features

### **1. Automatische API Key Rotation** 🔄
- **11+ API Keys** gleichzeitig nutzen (bis zu 20 möglich)
- **Automatischer Wechsel** bei Rate-Limit-Fehler (429)
- **Intelligentes Tracking** - bereits erschöpfte Keys werden übersprungen
- **550+ Requests/Tag** kostenlos (11 Keys × 50 Requests)

### **2. Telegram Benachrichtigungen** 📱
- **Key-Rotation Alerts** - Benachrichtigung wenn Key gewechselt wird
- **Rate-Limit Alerts** - Warnung wenn alle Keys erschöpft sind
- **Resume Alerts** - Info wenn System wieder läuft

### **3. Automatische Pause & Resume** ⏸️
- **Auto-Pause** wenn alle API Keys das Limit erreicht haben
- **Countdown** bis zum nächsten Reset (00:00 UTC)
- **Auto-Resume** sobald Limits zurückgesetzt sind
- **Keine manuellen Eingriffe** notwendig

### **4. Free Models Support** 💰
- **DeepSeek Chat V3** (kostenlos, 50 req/Tag per Key)
- **DeepSeek Reasoner R1** (kostenlos, 50 req/Tag per Key)
- **200+ weitere Modelle** über OpenRouter verfügbar

## 📁 Neue Dateien

```
src/
├── models/
│   ├── openrouter_model.py          # ✅ Erweitert mit Key-Rotation
│   └── model_factory.py              # ✅ Lädt alle Keys automatisch
└── utils/
    ├── __init__.py                   # 🆕 NEU
    └── telegram_notifier.py          # 🆕 NEU

OPENROUTER_KEY_ROTATION.md            # 🆕 Dokumentation
TELEGRAM_SETUP.md                     # 🆕 Setup-Anleitung
CHANGELOG_OPENROUTER.md               # 🆕 Diese Datei
```

## 🔧 Geänderte Dateien

### **1. `.env_example`**
```bash
# Neue Variablen:
OPENROUTER_API_KEY_1=...
OPENROUTER_API_KEY_2=...
# ... bis _11 (oder _20)

TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

### **2. `src/models/openrouter_model.py`**
**Neue Features:**
- ✅ Multi-Key-Support (List[str] statt str)
- ✅ `rotate_to_next_key()` Methode
- ✅ `pause_until_reset()` Auto-Pause
- ✅ `check_if_should_resume()` Auto-Resume
- ✅ Telegram-Integration
- ✅ Rate-Limit-Tracking mit `failed_keys_today`

### **3. `src/models/model_factory.py`**
**Neue Features:**
- ✅ `_get_openrouter_api_keys()` lädt alle Keys aus .env
- ✅ OpenRouter wird standardmäßig initialisiert
- ✅ Spezielle Behandlung für Multi-Key-Support
- ✅ Standard-Modell: `deepseek/deepseek-chat-v3-0324:free`

## 🎯 Verwendung

### **Quick Start**

1. **API Keys in .env eintragen:**
```bash
OPENROUTER_API_KEY_1=sk-or-v1-xxxxx
OPENROUTER_API_KEY_2=sk-or-v1-xxxxx
# ... bis Key 11
```

2. **Telegram Setup (optional):**
```bash
TELEGRAM_BOT_TOKEN=123456:ABCdef...
TELEGRAM_CHAT_ID=123456789
```

3. **Code nutzen:**
```python
from src.models.model_factory import model_factory

# OpenRouter wird automatisch initialisiert
model = model_factory.get_model("openrouter")

# Generate response - Key-Rotation automatisch!
response = model.generate_response(
    system_prompt="Du bist ein hilfreicher Assistent.",
    user_content="Analysiere den Markt."
)
```

### **In Agents nutzen**

Ändere einfach die Model-Config in deinem Agent:

```python
# Vorher (DeepSeek direkt):
MODEL_TYPE = "deepseek"
MODEL_NAME = "deepseek-reasoner"

# Nachher (OpenRouter mit Free-Model):
MODEL_TYPE = "openrouter"
MODEL_NAME = "deepseek/deepseek-r1-0528:free"
```

Das System nutzt dann automatisch alle 11 API Keys mit Rotation! 🚀

## 📊 Kapazität

| Keys | Requests/Tag | Requests/Monat | Kosten |
|------|--------------|----------------|--------|
| 1    | 50           | 1,500          | $0     |
| 5    | 250          | 7,500          | $0     |
| 11   | 550          | 16,500         | $0     |
| 20   | 1,000        | 30,000         | $0     |

## 🔔 Benachrichtigungs-Flow

### **Normaler Betrieb**
```
Request #1-50  → Key #1 ✅
Request #51    → Rate Limit (429)
               → 🔄 Rotate to Key #2
               → 📱 Telegram: "Switched to Key #2/11"
Request #51    → Key #2 ✅
...
```

### **Alle Keys erschöpft**
```
Request #551   → All keys exhausted
               → ⏸️ System PAUSED
               → 📱 Telegram: "All keys exhausted, pausing until 00:00 UTC"
               → ⏰ Wait until midnight...
00:00 UTC      → Limits reset
               → ✅ System RESUMED
               → 📱 Telegram: "System operational again"
```

## 🛠️ Technische Details

### **Key-Rotation-Algorithmus**

```python
1. Start mit Key #0 (OPENROUTER_API_KEY_1)
2. Request durchführen
3. Wenn 429 Error:
   a. Markiere aktuellen Key als "failed_today"
   b. Suche nächsten Key der nicht "failed_today" ist
   c. Update OpenAI client mit neuem Key
   d. Sende Telegram-Alert (optional)
   e. Retry Request
4. Wenn alle Keys failed:
   a. Berechne Zeit bis 00:00 UTC
   b. Pause System
   c. Sende Telegram-Alert
   d. Warte bis Resume-Zeit
5. Bei Resume:
   a. Lösche "failed_today" Set
   b. Reset zu Key #0
   c. Sende Telegram-Alert
```

### **Rate Limit Details**

OpenRouter Free Models:
- **Limit:** 50 Requests pro Tag pro API Key
- **Reset:** 00:00 UTC jeden Tag
- **Scope:** Pro Key, nicht pro Account
- **Models:** Nur `:free` Modelle betroffen

### **Pause-Mechanismus**

```python
# Berechne Zeit bis nächster UTC Midnight
now = datetime.now(timezone.utc)
next_midnight = datetime(...) + timedelta(days=1)
seconds = (next_midnight - now).total_seconds()

# Setze Pause-Flag
self.is_paused = True
self.pause_until = now + timedelta(seconds=seconds)

# Bei jedem Request prüfen:
if self.is_paused:
    if datetime.now() >= self.pause_until:
        # Resume!
        self.is_paused = False
        self.failed_keys_today.clear()
```

## 📚 Dokumentation

- **[OPENROUTER_KEY_ROTATION.md](OPENROUTER_KEY_ROTATION.md)** - Vollständige Anleitung
- **[TELEGRAM_SETUP.md](TELEGRAM_SETUP.md)** - Telegram Bot Setup in 5 Minuten
- **[.env_example](.env_example)** - Template mit allen Variablen

## 🔐 Sicherheit

- ✅ API Keys nur in `.env` (nie im Code!)
- ✅ `.env` ist in `.gitignore`
- ✅ Telegram Bot Token sicher aufbewahren
- ✅ Keys regelmäßig rotieren (alle paar Monate)

## 🐛 Bekannte Einschränkungen

1. **Rate Limits gelten pro Key** - 50 Requests/Tag per Key
2. **Reset um 00:00 UTC** - nicht lokale Zeitzone
3. **Keine Token-Limits** - Free Models haben unbegrenzte Tokens
4. **Test-Request bei Init** - Verbraucht 1 Request beim Start

## 🚀 Nächste Schritte

### **Phase 1: Setup** ✅
- [x] API Keys generieren
- [x] Keys in .env eintragen
- [x] Telegram Bot erstellen (optional)
- [x] System testen

### **Phase 2: Migration**
- [ ] Agents auf OpenRouter umstellen
- [ ] Model-Configs anpassen
- [ ] Monitoring einrichten

### **Phase 3: Optimierung**
- [ ] Mehr Keys hinzufügen (bis zu 20)
- [ ] Custom Telegram-Alerts erstellen
- [ ] Statistiken über Key-Nutzung sammeln

## 💡 Best Practices

### **DO ✅**
- Nutze mehrere Keys (mindestens 5-10)
- Setze Telegram-Benachrichtigungen auf
- Prüfe Logs regelmäßig
- Teste mit wenigen Requests zuerst

### **DON'T ❌**
- Committe niemals `.env` ins Git
- Teile Keys nicht öffentlich
- Verlasse dich nicht auf einen einzelnen Key
- Ignoriere Telegram-Alerts nicht

## 🎉 Zusammenfassung

Mit diesem Update kannst du:

- ✅ **550+ kostenlose Requests/Tag** mit 11 Keys
- ✅ **Automatische Key-Rotation** ohne manuelle Eingriffe
- ✅ **Telegram-Benachrichtigungen** über System-Status
- ✅ **Auto-Pause/Resume** bei Rate-Limits
- ✅ **Free DeepSeek Models** nutzen

**Keine Kosten, volle Power! 🚀**

---

**🌙 Built with love by Moon Dev 🚀**

*Letzte Aktualisierung: 1. November 2025*
