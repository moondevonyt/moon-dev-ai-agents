# 🌍 Multi-Asset Backtest System - Quick Reference

## 📁 File Structure

```
src/
├── scripts/
│   ├── multi_asset_tester.py          ← Tests strategies on 24 assets
│   ├── download_multi_asset_data.py   ← Downloads OHLCV data
│   └── backtestdashboard.py           ← Dashboard server
│
├── data/
│   ├── ohlcv/                         ← 24 CSV files (6 assets × 4 timeframes)
│   │   ├── BTC-USDT-5m.csv
│   │   ├── BTC-USDT-15m.csv
│   │   ├── ETH-USDT-5m.csv
│   │   └── ... (21 more files)
│   │
│   └── rbi_pp_multi/
│       ├── backtest_stats.csv         ← All 142 backtest results
│       ├── visualization/
│       │   ├── generate_viz.py        ← Top 1 strategy visualizer
│       │   ├── generate_multi_viz.py  ← Top 3 multi-asset visualizer
│       │   ├── top_strategy.html      ← 1.0 MB Bokeh chart
│       │   └── multi_asset_results.html ← 2.5 MB Bokeh chart (3 strategies)
│       └── templates/
│           └── index.html             ← Dashboard HTML
```

## 🚀 Quick Commands

### Test Strategies on All Assets
```bash
# Test top 5 strategies on all 24 asset/timeframe combinations
python3 src/scripts/multi_asset_tester.py --top 5

# Test top 10 strategies
python3 src/scripts/multi_asset_tester.py --top 10
```

### Generate Visualizations
```bash
# Generate Top 1 Strategy visualization
python3 src/data/rbi_pp_multi/visualization/generate_viz.py

# Generate Top 3 Multi-Asset visualization
python3 src/data/rbi_pp_multi/visualization/generate_multi_viz.py
```

### Dashboard
```bash
# Start dashboard (if not running)
python3 src/data/rbi_pp_multi/app.py

# Or use the wrapper
cd src/data/rbi_pp_multi && python3 app.py
```

## 🌐 URLs

- **Dashboard**: http://localhost:8001
- **Top Strategy Viz**: http://localhost:8001/visualization/top_strategy.html
- **Multi-Asset Viz**: http://localhost:8001/visualization/multi_asset_results.html

## 📊 Dashboard Features

### Main Page (http://localhost:8001)
- Sortierte Liste aller 142 Backtests
- Auto-refresh alle 5 Sekunden
- Rankings (#1, #2, #3 Badges)
- "🆕 NEU" Badge für neueste Strategie
- "🌍 Multi" Badge für Multi-Asset Tests

### Visualization Buttons
1. **📊 Top Strategy** - Beste einzelne Strategie mit:
   - Candlestick Chart
   - Trade Entry/Exit Markers
   - Volume Bars
   - Equity Curve
   - Stats Box

2. **🌍 Top 3 Multi-Asset** - Top 3 Asset/Timeframe Kombinationen:
   - Side-by-side Vergleich
   - 🥇 #1: ETH-USDT-5m (40.01%)
   - 🥈 #2: SUI-USDT-1h (34.44%)
   - 🥉 #3: ADA-USDT-30m (33.85%)

## 🎯 Best Performing Assets

| Asset | Best Timeframe | Return | Strategy |
|-------|---------------|--------|----------|
| **ETH** | 5m | **40.01%** | AccumulationCrossover |
| **SUI** | 1h | **34.44%** | AccumulationCrossover |
| **ADA** | 30m | **33.85%** | VolatilityDivergence |
| **ADA** | 15m | **28.94%** | VolatilityDivergence |
| **ADA** | 1h | **28.71%** | AccumulationCrossover |

## 📈 Strategy Win Rates

- **AccumulationCrossover**: 50% (12/24 profitable)
- **AdaptiveVolatility**: 33% (8/24 profitable)
- **VolatilityDivergence**: 17% (4/24 profitable)

## 💡 Key Insights

1. **ETH-USDT-5m** is the most profitable combination
2. **SUI** and **ADA** show strong performance across multiple timeframes
3. **5m** and **1h** timeframes outperform 15m/30m
4. Not all strategies work on all assets - asset-specific optimization needed

## 🔄 Workflow

### Full Multi-Asset Testing Workflow
```bash
# 1. Test top 5 strategies on all assets (takes ~5-10 min)
python3 src/scripts/multi_asset_tester.py --top 5

# 2. Generate multi-asset visualization (takes ~30 sec)
python3 src/data/rbi_pp_multi/visualization/generate_multi_viz.py

# 3. Open dashboard to see results
open http://localhost:8001

# 4. Click "🌍 Top 3 Multi-Asset" button
```

## 🛠️ Troubleshooting

### Dashboard not loading?
```bash
# Restart dashboard
pkill -f app.py
python3 src/data/rbi_pp_multi/app.py > logs/dashboard.log 2>&1 &
```

### Visualization not found?
```bash
# Regenerate visualizations
python3 src/data/rbi_pp_multi/visualization/generate_viz.py
python3 src/data/rbi_pp_multi/visualization/generate_multi_viz.py
```

### OHLCV data missing?
```bash
# Download fresh data
python3 src/scripts/download_multi_asset_data.py
```

## 📦 System Requirements

- Python 3.8+
- bokeh==3.4.3
- backtesting
- pandas
- numpy
- ccxt (for data download)

## 🎨 Visualization Details

### Top Strategy Viz (top_strategy.html)
- **Size**: 1.0 MB
- **Strategy**: VolatilityDivergence
- **Asset**: BTC-USD-15m
- **Return**: 151.48%
- **Trades**: 113

### Multi-Asset Viz (multi_asset_results.html)
- **Size**: 2.5 MB
- **Strategies**: Top 3 across all assets
- **Charts**: 3 × (Candlesticks + Volume)
- **Total Trades Shown**: ~50-100 per strategy

## 🔗 Related Files

- `src/agents/rbi_agent_pp_multi.py` - Main agent (auto multi-asset testing)
- `src/data/rbi_pp_multi/backtest_stats.csv` - All results (142 rows)
- `logs/dashboard.log` - Dashboard logs
- `logs/rbi_agent.log` - Agent logs

---

**Last Updated**: Oct 29, 2025
**Version**: 3.0 (Multi-Asset Edition)
**Built by**: BB1151 🌙
