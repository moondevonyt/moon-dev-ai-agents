# 🚀 High-Frequency Multi-Timeframe Trading System

## Self-Improving HFT mit DeepSeek

Ein vollautomatisches High-Frequency Trading System das:
- **Multi-Timeframe nutzt** (1h Trend → 5m Execution)
- **Stündlich Performance analysiert**
- **Sich selbst mit DeepSeek verbessert**
- **Nur DeepSeek nutzt** (kein OpenRouter!)

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────┐
│  1H TIMEFRAME (Informative - Trend Direction)       │
│  • Bullish → Only LONG entries on 1m/5m            │
│  • Bearish → Only SHORT entries on 1m/5m           │
│  • Neutral → No trading                             │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  1M/5M TIMEFRAME (Primary - Entry Signals)         │
│  • Momentum breakouts                               │
│  • Volume confirmation                              │
│  • RSI filter                                       │
│  • Tight stops: 0.5%                                │
│  • Quick targets: 1%                                │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  TRADE EXECUTION                                    │
│  • Log every trade with features                   │
│  • Track: Entry, Exit, P&L, Features               │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼ (Every 1 hour)
┌─────────────────────────────────────────────────────┐
│  HOURLY PERFORMANCE CHECK                           │
│  • Win Rate < 50%? → Trigger Analysis               │
│  • Win Rate ≥ 50%? → Continue Trading               │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼ (If < 50% Win Rate)
┌─────────────────────────────────────────────────────┐
│  DEEPSEEK ANALYSIS (deepseek-reasoner)              │
│  • Analyze losing patterns                          │
│  • Identify root causes                             │
│  • Suggest specific improvements                    │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  AUTO-APPLY IMPROVEMENTS                            │
│  • Update strategy filters                          │
│  • Apply for next hour                              │
│  • Continue trading                                 │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Key Features

### 1. **Multi-Timeframe Alignment**

**1h Timeframe (Informative):**
- Bestimmt Trend-Richtung
- Berechnet: EMA 20/50, RSI, Volume Trend
- Output: `'bullish'`, `'bearish'`, oder `'neutral'`

**5m Timeframe (Primary):**
- Generiert Entry-Signale
- Nur wenn aligned mit 1h Trend
- Features: Momentum Z-Score, RSI, Volume Spike, Volatility

**Alignment Rules:**
```python
IF 1h_trend == 'bullish':
    ONLY take LONG entries on 5m
    
IF 1h_trend == 'bearish':
    ONLY take SHORT entries on 5m
    
IF 1h_trend == 'neutral':
    NO trading
```

### 2. **High-Frequency Execution**

**Position Sizing:**
- Klein: 0.01 BTC pro Trade
- Hohe Frequenz: 15-25 Trades/Stunde

**Risk Management:**
- Stop Loss: 0.5% (tight)
- Take Profit: 1.0% (quick)
- Risk/Reward: 1:2

**Entry Filters:**
```python
# Momentum Breakout
momentum_zscore > 1.0

# RSI Range
50 < RSI < 70 (for longs)
30 < RSI < 50 (for shorts)

# Volume Confirmation
volume_spike > 1.3x

# AUTO-IMPROVEMENT FILTERS
# (Diese werden stündlich angepasst)
if side == 'long' and rsi > 75:
    skip  # Overbought
    
if momentum_zscore < 0.8:
    skip  # Zu schwach
```

### 3. **Stündliche Performance Checks**

**Metrics berechnet:**
- Total Trades
- Win Rate
- Total P&L
- Winners vs Losers

**Trigger Threshold:**
```python
needs_improvement = (
    win_rate < 0.50 or    # < 50% Win Rate (HFT braucht >50%)
    total_pnl < 0         # Negative P&L
)
```

### 4. **DeepSeek Analysis** (Nur bei < 50% WR)

**Input an DeepSeek:**
```
HOURLY PERFORMANCE:
- Total Trades: 20
- Win Rate: 40% (POOR)
- P&L: -$50

TRADES:
Trade 1 (LOSS):
  Side: LONG
  Features:
    - Momentum: 0.6 (weak)
    - RSI: 48
    - Volume: 1.1x (low)
...
```

**DeepSeek Output:**
```
ANALYSIS:
- Most losses had momentum_zscore < 0.8
- Low volume confirmation (< 1.5x) led to false breakouts
- RSI near 50 (indecision zone) resulted in reversals

LOSING PATTERNS:
- 60% of losing longs had weak momentum (< 0.8)
- 80% had volume spike < 1.3x

IMPROVEMENTS:
1. Require momentum_zscore > 1.2 for entries
2. Require volume_spike > 1.5x for confirmation
3. Avoid trades when 45 < RSI < 55 (indecision zone)
```

### 5. **Auto-Apply Improvements**

Verbesserungen werden automatisch für die nächste Stunde angewendet:

```python
# 🌙 Auto-improvement: Stronger momentum required
if features.get('momentum_zscore', 0) < 1.2:
    return False  # Skip trade

# 🌙 Auto-improvement: Better volume confirmation
if features.get('volume_spike', 0) < 1.5:
    return False  # Skip trade

# 🌙 Auto-improvement: Avoid indecision zone
rsi = features.get('rsi', 50)
if 45 < rsi < 55:
    return False  # Skip trade
```

---

## 🚀 Quick Start

### Installation

```bash
# Environment Variable
echo "DEEPSEEK_KEY=sk-xxxxx" >> .env
```

### Test Run

```bash
cd src/strategy
python hft_self_improving_loop.py
```

**Was passiert:**
1. ✅ HFT System initialisiert
2. ✅ 1h Trend analysiert (bullish/bearish)
3. ✅ 60 Minuten Trading simuliert (~20 Trades)
4. ✅ Stündliche Performance Check
5. ✅ DeepSeek Analyse (wenn < 50% WR)
6. ✅ Verbesserungen angewendet

---

## 📁 Components

### 1. `hft_multi_timeframe.py`
Main HFT Strategy Klasse

**Methods:**
- `analyze_1h_trend()` - 1h Trend bestimmen
- `generate_signal_1m()` - 5m Entry Signale
- `should_take_trade()` - Trade Alignment Check
- `execute_trade()` - Trade Execution
- `check_hourly_performance()` - Performance Stats

### 2. `hft_improver_deepseek.py`
DeepSeek-basierte Verbesserung

**Methods:**
- `analyze_hourly_trades()` - Trades analysieren mit DeepSeek
- `_extract_improvements()` - Improvements extrahieren
- `get_latest_improvements()` - Letzte Verbesserungen holen

**DeepSeek Models:**
- `deepseek-reasoner` - Best für tiefe Analyse (empfohlen)
- `deepseek-chat` - Schneller aber weniger detailliert

### 3. `hft_self_improving_loop.py`
Complete End-to-End System

**Methods:**
- `simulate_hft_session()` - Trading Session simulieren
- `run_hourly_improvement_cycle()` - Stündlicher Check
- `should_run_hourly_check()` - Timer Check

---

## 📊 Data Files

### `src/data/trades/trades.txt`
Alle Trades (append-only log):
```json
{"timestamp": "2025-11-01T20:15:00", "symbol": "BTC/USDT", "side": "long", ...}
{"timestamp": "2025-11-01T20:18:00", "symbol": "BTC/USDT", "side": "short", ...}
```

### `src/data/trades/hft_hourly_analysis.json`
Stündliche DeepSeek Analysen:
```json
[
  {
    "timestamp": "2025-11-01T21:00:00",
    "hour": "2025-11-01 20:00",
    "stats": {
      "total_trades": 20,
      "win_rate": 0.40,
      "total_pnl": -50.0
    },
    "analysis": "ANALYSIS: Most losses had momentum < 0.8...",
    "improvements": [
      "Require momentum_zscore > 1.2",
      "Require volume_spike > 1.5x"
    ]
  }
]
```

### `src/data/trades/daily_summary.csv`
Tägliche Zusammenfassung:
```csv
date,total_trades,winning_trades,losing_trades,win_rate,avg_pnl,total_pnl
2025-11-01,180,95,85,52.8%,12.50,2250.00
```

---

## 🔧 Configuration

### Timeframes

Ändere in `hft_self_improving_loop.py`:
```python
self.strategy = HFTMultiTimeframeStrategy(
    informative_timeframe="1h",   # Trend Filter
    primary_timeframe="5m",       # Execution
    symbol="BTC/USDT"
)
```

**Optionen:**
- Informative: `1h`, `4h`, `1d`
- Primary: `1m`, `5m`, `15m`

### Win Rate Threshold

Ändere in `hft_multi_timeframe.py`:
```python
needs_improvement = (
    win_rate < 0.50 or  # Ändere auf 0.55 für strengere Kriterien
    total_pnl < 0
)
```

### DeepSeek Model

Ändere in `hft_self_improving_loop.py`:
```python
self.improver = HFTImproverDeepSeek(
    api_key=deepseek_key,
    model_name="deepseek-reasoner"  # oder "deepseek-chat"
)
```

**Model Vergleich:**
- `deepseek-reasoner`: Beste Analyse, etwas langsamer
- `deepseek-chat`: Schneller, weniger detailliert

---

## 🎯 Production Integration

### 1. Live Data Integration

```python
# Replace simulated data with real exchange data
from ccxt import binance

exchange = binance()

# 1h Data
df_1h = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=100)

# 5m Data
df_5m = exchange.fetch_ohlcv('BTC/USDT', '5m', limit=50)

# Analyze
trend = strategy.analyze_1h_trend(df_1h)
signal = strategy.generate_signal_1m(df_5m)
```

### 2. Real Order Execution

```python
def execute_trade(self, side, entry_price, features):
    """Execute real trade on exchange"""
    
    # Calculate position size
    size = 0.01  # BTC
    
    # Place order
    if side == 'long':
        order = exchange.create_market_buy_order('BTC/USDT', size)
    else:
        order = exchange.create_market_sell_order('BTC/USDT', size)
    
    # Set stop loss and take profit
    stop_price = entry_price * (0.995 if side == 'long' else 1.005)
    target_price = entry_price * (1.01 if side == 'long' else 0.99)
    
    # Place OCO order (stop + target)
    exchange.create_oco_order(
        symbol='BTC/USDT',
        side='sell' if side == 'long' else 'buy',
        amount=size,
        price=target_price,
        stop_price=stop_price
    )
```

### 3. Continuous Loop

```python
def run_continuous_trading():
    """Run HFT continuously"""
    
    hft = HFTSelfImprovingLoop(deepseek_key)
    
    while True:
        # Fetch latest data
        df_1h = fetch_1h_data()
        df_5m = fetch_5m_data()
        
        # Analyze trend
        trend = hft.strategy.analyze_1h_trend(df_1h)
        
        # Generate signal
        signal = hft.strategy.generate_signal_1m(df_5m)
        
        if signal:
            side, features = signal
            
            if hft.strategy.should_take_trade(side, features):
                # Execute
                hft.strategy.execute_trade(side, current_price, features)
        
        # Check hourly
        if hft.should_run_hourly_check():
            hft.run_hourly_improvement_cycle()
        
        # Sleep (adjust for desired frequency)
        time.sleep(5)  # Check every 5 seconds
```

---

## 📈 Expected Performance

### Scenario: Hour 1 (Before Improvement)
```
20 Trades executed
Win Rate: 40% (8 winners, 12 losers)
P&L: -$50

PATTERN: Weak momentum entries (< 0.8) failed
```

### DeepSeek Analysis:
```
IMPROVEMENTS:
1. Require momentum > 1.2
2. Require volume > 1.5x
3. Avoid RSI 45-55 zone
```

### Scenario: Hour 2 (After Improvement)
```
18 Trades executed (fewer but better)
Win Rate: 61% (11 winners, 7 losers)
P&L: +$80

RESULT: Improved win rate by 21%
```

---

## 🛡️ Safety Features

### 1. Hourly Checks Only
- Nicht nach jedem Trade
- Verhindert Over-Optimization
- Stabiler als real-time adjustments

### 2. Specific Thresholds
- DeepSeek gibt konkrete Zahlen
- Nicht vage "improve momentum"
- Testbar und validierbar

### 3. Trade Logging
- Kompletter Audit Trail
- Alle Features gespeichert
- Rollback möglich

### 4. Simpler Filter
- Kein komplexes ML während Trading
- Einfache if/else Rules
- Schnell und deterministisch

---

## 🧪 Testing

### Unit Test
```bash
# Test HFT Strategy
python src/strategy/hft_multi_timeframe.py

# Test DeepSeek Improver
python src/strategy/hft_improver_deepseek.py
```

### Integration Test
```bash
# Full system test (1 hour simulation)
python src/strategy/hft_self_improving_loop.py
```

### Backtest Validation
```python
from src.strategy.hft_backtest import HFTBacktest

bt = HFTBacktest()
results = bt.run(
    start_date="2024-01-01",
    end_date="2025-01-01",
    symbol="BTC/USDT"
)

print(f"Win Rate: {results['win_rate']:.1%}")
print(f"Sharpe: {results['sharpe']:.2f}")
print(f"Max Drawdown: {results['max_dd']:.2%}")
```

---

## 📚 Key Differences vs Daily System

| Feature | Daily System | HFT System |
|---------|-------------|------------|
| **Timeframe** | Daily | 1m/5m |
| **Trades** | 10-20/day | 15-25/hour |
| **Win Rate Target** | > 30% | > 50% |
| **Improvement Cycle** | Daily | Hourly |
| **Model** | DeepSeek + Research | DeepSeek only |
| **Stop Loss** | 2-5% | 0.5% |
| **Take Profit** | 5-10% | 1% |
| **Holding Time** | Days | Minutes |

---

## 🚨 Troubleshooting

### "No trend detected"
- Check if 1h data has enough candles (need ≥50)
- Verify EMA calculation
- May be neutral market (sideways)

### "Win rate still < 50% after improvement"
- Check if improvements are being applied
- May need more aggressive filters
- Consider switching to longer timeframe

### "Too few trades"
- Lower momentum threshold (e.g., 0.8 → 0.6)
- Increase volume threshold acceptance
- Widen RSI range

### "DeepSeek API error"
- Verify DEEPSEEK_KEY in .env
- Check API rate limits
- Try switching to deepseek-chat (faster)

---

## 🔮 Future Enhancements

- [ ] Machine Learning Signal Generation
- [ ] Multi-Symbol Support (correlations)
- [ ] Dynamic Position Sizing (Kelly Criterion)
- [ ] Slippage & Fee Modeling
- [ ] Backtesting Framework
- [ ] Web Dashboard (real-time monitoring)
- [ ] Alert System (Telegram/Discord)
- [ ] Portfolio-Level Risk Management

---

## 📖 Related Documentation

- `SELF_IMPROVING_STRATEGY.md` - Daily improvement system
- `src/models/deepseek_model.py` - DeepSeek integration
- `src/utils/trade_logger.py` - Trade logging utility

---

Built with ❤️ by Moon Dev 🚀

**Kein OpenRouter - Nur DeepSeek!**
