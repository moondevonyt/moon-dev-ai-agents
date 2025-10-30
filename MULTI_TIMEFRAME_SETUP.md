# 🌍 Multi-Timeframe Backtest System - Setup Guide

## 📊 System Configuration

### Assets (6)
- BTC-USDT
- ETH-USDT
- SOL-USDT
- ADA-USDT
- XRP-USDT
- SUI-USDT

### Primary Timeframes (4) - Main Chart
- 1m (1 minute)
- 5m (5 minutes)
- 15m (15 minutes)
- 30m (30 minutes)

### Informative Timeframes (5) - Higher TF Context
- 1h (1 hour)
- 2h (2 hours)
- 4h (4 hours)
- 1d (Daily)
- 1w (Weekly)

### Total Combinations Per Strategy
**120 backtests** = 6 assets × 4 primary TF × 5 informative TF

### Required OHLCV Files
**54 files** = 6 assets × 9 timeframes

---

## 🚀 Setup Workflow (DO NOT START YET!)

### Step 1: Check Configuration
```bash
# View the configuration
python3 src/config/multi_timeframe_config.py
```

Expected output:
- 120 combinations per strategy
- 54 unique OHLCV files required

### Step 2: Download OHLCV Data
```bash
# Download all 54 OHLCV files from Binance
python3 src/scripts/download_multi_timeframe_data.py
```

This will download:
- 6 assets × 9 timeframes = 54 CSV files
- Data saved to: `src/data/ohlcv/`
- Takes ~5-10 minutes

Example files:
- `BTC-USDT-1m.csv` (7 days of 1-min data)
- `BTC-USDT-5m.csv` (30 days)
- `BTC-USDT-1h.csv` (180 days)
- `BTC-USDT-1d.csv` (2 years)
- ... (50 more files)

### Step 3: Test Multi-Timeframe Backtesting
```bash
# Validate that multi-timeframe backtesting works
python3 src/scripts/test_multi_timeframe.py
```

This will:
1. Test 10 sample combinations
2. Run backtests with simple multi-TF strategy
3. Show results (return %, trades, etc.)
4. Validate that system is ready

Expected output:
- ✅ At least 8/10 successful backtests
- Returns ranging from -X% to +Y%
- Top 3 combinations shown

---

## 🎯 After Validation

### IF TEST PASSES (✅):
1. ✅ System is ready
2. ⚠️ **DO NOT START YET**
3. 💰 Load DeepSeek account first
4. 🚀 Then start Research + RBI agents

### IF TEST FAILS (❌):
1. ❌ Check OHLCV data exists
2. 🔍 Review error messages
3. 🛠️ Fix issues before proceeding

---

## 📁 File Structure

```
src/
├── config/
│   └── multi_timeframe_config.py      ← Configuration (120 combos)
│
├── scripts/
│   ├── download_multi_timeframe_data.py  ← Data downloader (54 files)
│   └── test_multi_timeframe.py           ← Validation tester
│
└── data/
    └── ohlcv/                          ← 54 OHLCV files
        ├── BTC-USDT-1m.csv
        ├── BTC-USDT-5m.csv
        ├── BTC-USDT-1h.csv
        ├── BTC-USDT-1d.csv
        └── ... (50 more)
```

---

## 🧪 Test Command Summary

```bash
# 1. Check config
python3 src/config/multi_timeframe_config.py

# 2. Download data (takes ~5-10 min)
python3 src/scripts/download_multi_timeframe_data.py

# 3. Validate system (takes ~1-2 min)
python3 src/scripts/test_multi_timeframe.py
```

---

## ⚠️ IMPORTANT NOTES

### DO NOT START AGENTS YET!

This is SETUP ONLY. After validation:
1. Load DeepSeek account
2. Update RBI agent to use 120 combinations
3. Then start research + RBI agents

### Data Download Notes

- 1m data: 7 days (fast moving, short history)
- 5m data: 30 days
- 15m/30m: 60-90 days
- 1h: 180 days
- 2h/4h: 1 year
- Daily: 2 years
- Weekly: 3 years

### Expected Behavior

Each strategy will be backtested on:
- BTC-USDT-1m-1h
- BTC-USDT-1m-2h
- BTC-USDT-1m-4h
- BTC-USDT-1m-1d
- BTC-USDT-1m-1w
- BTC-USDT-5m-1h
- ... (114 more combinations)

Total: 120 backtests per strategy

---

## 🎯 Next Steps After Validation

1. ✅ Validation passes
2. 💰 Load DeepSeek account ($10-20 recommended)
3. 🔧 Update RBI agent to use 120 combos
4. 🚀 Start agents in DRY RUN mode
5. 📊 Monitor first few strategies
6. 🎉 Full production if all good

---

**Built by BB1151 🌙**
**Version: 4.0 (Multi-Timeframe Edition)**
**Date: Oct 30, 2025**
