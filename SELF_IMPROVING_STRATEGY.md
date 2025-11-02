# 🌙 Moon Dev's Self-Improving Trading Strategy

## Adaptive Learning System für Crypto Trading

Ein vollautomatisches System, das **während des Betriebs** aus schlechten Trades lernt und sich selbst verbessert.

---

## 🎯 Konzept

```
Schlechter Tag (< 30% Win Rate)
    ↓
LLM analysiert Fehler (DeepSeek)
    ↓
Research Agent validiert Verbesserungen
    ↓
System wendet Änderungen automatisch an
    ↓
Verbesserte Strategie läuft weiter
```

---

## 🏗️ System-Komponenten

### 1. **Trade Logger** (`src/utils/trade_logger.py`)
- Trackt JEDEN Trade mit vollem Kontext
- Speichert in `trades.txt` (append-only log)
- Berechnet tägliche Performance Metrics
- Triggert Improvement Cycle bei schlechter Performance

**Kriterien für "Schlechter Tag":**
- Win Rate < 30%
- Total P&L negativ
- ≥10 Trades aber <3 Winner

### 2. **LLM Strategy Improver** (`src/strategy/llm_strategy_improver.py`)
- Nutzt **DeepSeek Reasoner** für tiefe Analyse
- Analysiert Patterns in Losing Trades
- Identifiziert Root Causes
- Schlägt konkrete Verbesserungen vor (mit Zahlen/Thresholds)

**Beispiel Analyse:**
```
PATTERNS:
- 7/7 losing longs hatten funding_rate > 1.5%
- 6/7 hatten RSI > 75 (overbought)
- 5/7 hatten momentum_zscore < 0.5 (schwach)

ROOT CAUSE:
Strategie longt coins mit hohen Funding-Kosten während 
sie bereits overextended sind (RSI > 75).

IMPROVEMENTS:
1. Skip longs if funding_rate > 0.5%
2. Require momentum_zscore > 1.0 for entries
3. Avoid longs when RSI > 75
```

### 3. **Research Improver** (`src/strategy/research_improver.py`)
- Validiert LLM-Vorschläge durch Research
- Nutzt **Research Agent** für Fact-Checking
- Testet Improvements in Backtest (optional)
- Gibt Confidence Score (0-100%)

**Research Queries Beispiel:**
```python
"What is the optimal funding rate threshold for 
avoiding long positions in crypto momentum strategies? 
Historical data on funding rates vs future returns."
```

### 4. **Strategy Updater** (`src/strategy/strategy_updater.py`)
- Generiert Python Code für Improvements
- Erstellt Backup vor Änderungen
- Wendet Improvements an
- Git Commit für Versionierung
- Rollback Funktion bei Problemen

**Beispiel Auto-Generated Code:**
```python
# 🌙 Auto-improvement: Avoid longs with high funding
if side == 'long' and features.get('funding_rate', 0) > 0.5:
    logger.info(f"Skipping {symbol} - funding {funding_rate}% > 0.5%")
    return None  # Skip this trade
```

### 5. **Self-Improving Loop** (`src/strategy/self_improving_loop.py`)
- Orchestriert alle Komponenten
- End-to-End Improvement Cycle
- Kann simulierte Bad Days für Testing

---

## 🚀 Quick Start

### Installation

```bash
# Dependencies bereits in requirements.txt
pip install -r requirements.txt

# Environment Variables (.env)
DEEPSEEK_KEY=sk-xxxxx
OPENROUTER_API_KEY_1=sk-or-xxxxx  # Fallback
```

### Test Run (Demo)

```bash
cd src/strategy
python self_improving_loop.py
```

Das wird:
1. 10 Trades simulieren (3 winners, 7 losers)
2. LLM Analyse starten
3. Improvements vorschlagen
4. Research validieren
5. Code generieren (Dry-Run, keine echten Änderungen)

**Output:**
```
🧪 DEMO MODE - Simulating Bad Trading Day
✅ Simulated 10 trades (3 winners, 7 losers = 30% win rate)

📊 Daily Trading Summary
Total Trades: 10
Winners: 3 | Losers: 7
Win Rate: 30.0%
Total P&L: $-315.00
⚠️  BAD DAY DETECTED - Triggering Analysis

🧠 DEEPSEEK ANALYSIS
PATTERNS IDENTIFIED:
- All 7 losing longs had funding_rate > 1.4%
- 6/7 had RSI > 76 (severely overbought)
- Average momentum_zscore: 0.39 (weak)
...

✨ Extracted 3 improvement proposals:
1. Skip longs if funding_rate > 0.5%
2. Require momentum_zscore > 1.0 for all entries
3. Avoid longs when RSI > 75
```

---

## 📊 Integration in Echte Strategie

### Beispiel: Momentum Strategy Integration

```python
from src.utils.trade_logger import get_trade_logger
from src.strategy.self_improving_loop import SelfImprovingLoop

class MomentumStrategy:
    def __init__(self):
        self.trade_logger = get_trade_logger()
        self.improver = SelfImprovingLoop()
    
    def execute_trade(self, symbol, side, entry_price, features):
        """Execute a trade and log it"""
        
        # ... your trading logic ...
        
        # Calculate P&L
        exit_price = self.get_exit_price(symbol)
        pnl = (exit_price - entry_price) * quantity
        pnl_pct = (exit_price / entry_price - 1) * 100
        
        # LOG TRADE (Important!)
        self.trade_logger.log_trade(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            pnl=pnl,
            pnl_pct=pnl_pct,
            entry_time=entry_time,
            exit_time=datetime.now(),
            features={
                'momentum_zscore': features['momentum'],
                'funding_rate': features['funding'],
                'volatility': features['vol'],
                'rsi': features['rsi'],
                'volume_zscore': features['volume']
            },
            reason="Momentum breakout signal"
        )
    
    def end_of_day_check(self):
        """Run at end of trading day"""
        
        # Check if improvement needed
        if self.improver.check_daily_performance():
            print("⚠️  Bad day - Running improvement cycle")
            
            # Run improvement (dry_run=False for production)
            self.improver.run_full_improvement_cycle(dry_run=False)
        else:
            print("✅ Good day - No improvements needed")
```

### Integration Points

**1. Trade Execution:**
```python
# After EVERY trade completes
trade_logger.log_trade(
    symbol=symbol,
    side=side,
    entry_price=entry,
    exit_price=exit,
    quantity=qty,
    pnl=pnl,
    pnl_pct=pnl_pct,
    entry_time=entry_time,
    exit_time=exit_time,
    features={
        'momentum_zscore': ...,
        'funding_rate': ...,
        'volatility': ...,
        'rsi': ...,
        'volume_zscore': ...
    },
    reason="Why we entered this trade"
)
```

**2. End of Day:**
```python
# Run once per day (e.g., 23:59 UTC)
improver = SelfImprovingLoop()
improver.run_full_improvement_cycle(dry_run=False)
```

**3. Strategy File Structure:**
```python
def should_take_trade(symbol, side, features):
    """Trading logic with auto-improvement filters"""
    
    # Original strategy logic
    if features['momentum_zscore'] < 0.5:
        return False
    
    # AUTO-IMPROVEMENT FILTERS
    # (This section gets auto-updated by the system)
    
    # 🌙 Auto-improvement: Avoid longs with high funding
    if side == 'long' and features.get('funding_rate', 0) > 0.5:
        return False
    
    # 🌙 Auto-improvement: Require stronger momentum
    if features.get('momentum_zscore', 0) < 1.0:
        return False
    
    # 🌙 Auto-improvement: Avoid overextended entries
    rsi = features.get('rsi', 50)
    if side == 'long' and rsi > 75:
        return False
    
    return True
```

---

## 📁 Data Files

### trades.txt
```json
{"timestamp": "2025-11-01T17:30:00", "symbol": "BTC/USDT", "side": "long", ...}
{"timestamp": "2025-11-01T18:45:00", "symbol": "ETH/USDT", "side": "short", ...}
```

### daily_summary.csv
```csv
date,total_trades,winning_trades,losing_trades,win_rate,avg_pnl,total_pnl,sharpe,needs_improvement
2025-11-01,10,3,7,30.0%,-31.50,-315.00,0.23,True
2025-11-02,12,8,4,66.7%,42.30,507.60,1.85,False
```

### improvements.json
```json
[
  {
    "timestamp": "2025-11-01T20:00:00",
    "daily_summary": {...},
    "llm_analysis": "PATTERNS: ...",
    "proposed_improvements": [
      {
        "description": "Skip longs if funding_rate > 0.5%",
        "status": "proposed"
      }
    ],
    "status": "awaiting_validation"
  }
]
```

### validated_improvements.json
```json
[
  {
    "timestamp": "2025-11-01T20:30:00",
    "validated_improvements": [
      {
        "improvement": {...},
        "research_findings": [...],
        "validated": true,
        "confidence": 0.85
      }
    ],
    "ready_for_deployment": true
  }
]
```

### deployments.json
```json
[
  {
    "timestamp": "2025-11-01T21:00:00",
    "improvements_applied": [...],
    "backup_file": "strategy_backups/momentum_strategy_backup_20251101_210000.py",
    "status": "deployed"
  }
]
```

---

## 🔧 Configuration

### Trigger Thresholds

Passe in `trade_logger.py` an:

```python
needs_improvement = (
    win_rate < 0.30 or        # < 30% win rate
    total_pnl < 0 or          # Negative P&L
    (total >= 10 and winners < 3)  # Min 10 trades, <3 winners
)
```

### LLM Model

Wechsel in `llm_strategy_improver.py`:

```python
self.llm = DeepSeekModel(
    api_key=api_key,
    model_name="deepseek-chat"  # oder "deepseek-reasoner"
)
```

### Auto-Apply

Production Mode (echte Änderungen):
```python
improver.run_full_improvement_cycle(dry_run=False)
```

---

## 🛡️ Safety Features

### 1. Backups
- Jede Änderung wird gebackupt
- Backups in `strategy_backups/`
- Timestamped für einfaches Tracking

### 2. Git Versioning
- Automatische Git Commits
- Commit Message enthält alle Improvements
- `git log` zeigt komplette History

### 3. Rollback
```python
updater = StrategyUpdater()
updater.rollback_last_deployment()
```

### 4. Dry-Run Mode
- Teste Änderungen ohne Apply
- Review Code vor Deployment
- Validate Logic

---

## 📈 Expected Results

### Scenario: High Funding Trap

**Before Improvement:**
```
Day 1: 10 trades, 30% win rate, -$315 P&L
Pattern: 7 losing longs mit funding > 1.4%
```

**After Improvement:**
```
Filter applied: Skip longs if funding > 0.5%

Day 2: 8 trades, 62% win rate, +$420 P&L
Result: Avoided 5 high-funding traps
```

### Continuous Learning

```
Week 1: Learned to avoid high funding longs
Week 2: Learned to require stronger momentum (z > 1.0)
Week 3: Learned to skip overextended entries (RSI > 75)
Week 4: Learned optimal volatility threshold
...
```

---

## 🧪 Testing

### Unit Tests
```bash
# Test individual components
python src/utils/trade_logger.py
python src/strategy/llm_strategy_improver.py
python src/strategy/research_improver.py
python src/strategy/strategy_updater.py
```

### Integration Test
```bash
# Full cycle with simulation
python src/strategy/self_improving_loop.py
```

### Backtest Validation
```python
# Before/After comparison
from src.strategy.backtest_validator import BacktestValidator

validator = BacktestValidator()
results = validator.compare_strategies(
    original_strategy="momentum_v1",
    improved_strategy="momentum_v2_auto_improved",
    start_date="2024-01-01",
    end_date="2025-01-01"
)
print(results)  # Sharpe, Drawdown, Win Rate comparison
```

---

## 🚨 Troubleshooting

### "No improvements generated"
- Check if trades were logged with `features` dict
- Verify losing_trades list is not empty
- Ensure LLM API key is valid

### "Research validation failed"
- OpenRouter API keys exhausted (check rate limits)
- Network issues
- Run with fewer research queries

### "Strategy update failed"
- Backup exists? Check `strategy_backups/`
- Insertion marker missing in strategy file
- Add `# AUTO-IMPROVEMENT FILTERS` comment

### "Git commit failed"
- Git not initialized? Run `git init`
- Conflicts? Resolve and retry
- Permissions? Check file access

---

## 🎯 Best Practices

1. **Always log features**: Momentum, funding, RSI, vol, etc.
2. **Review before apply**: Use dry_run=True first
3. **Monitor deployments**: Check git log regularly
4. **Validate backtests**: Test improvements on historical data
5. **Keep backups**: Never delete backup files
6. **Track metrics**: Monitor win rate, Sharpe, drawdown over time

---

## 🔮 Future Enhancements

- [ ] Multi-Strategy Learning (share learnings across strategies)
- [ ] Reinforcement Learning Optimizer (RL-based parameter tuning)
- [ ] A/B Testing Framework (test old vs new in parallel)
- [ ] Automated Backtest Validation (before apply)
- [ ] Telegram Notifications (alert on improvements)
- [ ] Web Dashboard (visualize learning progress)
- [ ] ML Model Retraining (update predictive models)

---

## 📚 Related Files

- `src/agents/research_agent.py` - Research Agent für Validierung
- `src/models/deepseek_model.py` - DeepSeek LLM Integration
- `src/models/openrouter_model.py` - OpenRouter mit Key Rotation
- `test_openrouter_rotation.py` - Test OpenRouter Setup

---

## 🌙 Moon Dev's Philosophy

> "The best trading system is one that learns from its mistakes and improves itself automatically." 

**Self-improving = Sustainable Alpha**

---

Built with ❤️ by Moon Dev 🚀
