# Backtest Dashboard

Web dashboard for viewing and organizing RBI agent backtest results.

## What It Does
- Displays backtest statistics in a sortable table
- Shows summary stats (total backtests, avg return, max return)
- Organize backtests into folders
- Copy file paths for easy access
- Run new backtests directly from the UI (work in progress, idk if i will build this out as i just run from terminal)

## Quick Start

### 1. Generate Backtest Data
First, run the RBI agent to create backtest results:
```bash
python src/agents/rbi_agent_pp_multi.py
```

This creates: `src/data/rbi_pp_multi/backtest_stats.csv`

### 2. Configure CSV Path
Edit `src/scripts/backtestdashboard.py` line 60:
```python
STATS_CSV = Path("YOUR_PATH_TO/backtest_stats.csv")
```

### 3. Run Dashboard
```bash
python src/scripts/backtestdashboard.py
```

### 4. Open Browser
Navigate to: `http://localhost:8001`

## Features

### Stats Cards
- Total Backtests
- Unique Strategies
- Data Sources Tested
- Average Return
- Max Return
- Average Sortino Ratio

### Table View
- Strategy Name (click to copy file path)
- Return %
- Buy & Hold %
- Max Drawdown %
- Sharpe Ratio
- Sortino Ratio
- Expectancy %
- Number of Trades
- Data Source
- Timestamp

### Folder Management
- Select multiple backtests (Shift-click, Cmd-click)
- Add to folders for organization
- Copy all paths from a folder
- Delete folders

### New Backtests (WIP - Work in Progress)
- Run backtests directly from UI
- Add strategy ideas in text box
- Auto-creates folder with results
- Background processing with status updates

## Configuration

Edit `backtestdashboard.py` to customize:

```python
# Line 60: CSV file location
STATS_CSV = Path("/path/to/backtest_stats.csv")

# Line 64: Templates and static files
TEMPLATE_BASE_DIR = Path("/path/to/rbi_pp_multi")

# Line 69: Folder storage location
USER_FOLDERS_DIR = TEMPLATE_BASE_DIR / "user_folders"

# Line 72-73: Return thresholds
TARGET_RETURN = 50  # Optimization goal
SAVE_IF_OVER_RETURN = 1.0  # Minimum to save
```

## Port Settings
- Default: `8001`
- Change at line 625: `uvicorn.run(app, host="0.0.0.0", port=8001)`

## Requirements
- FastAPI
- Uvicorn
- Pandas
- NumPy

All included in main `requirements.txt`

## File Structure
```
src/data/rbi_pp_multi/
├── backtest_stats.csv        # Main results CSV
├── user_folders/              # Organized folders
├── templates/
│   └── index.html             # Dashboard UI
└── static/
    └── style.css              # Styling
```

## Tips
- **Strategy column**: Hover to see full file path
- **Multi-select**: Shift-click for range, Cmd-click for individual
- **Copy paths**: Select rows → "Copy Paths" button
- **Large returns**: Values ≥1000% display without decimals

## Troubleshooting

**Port already in use:**
- Change port in line 625
- Update browser URL accordingly

**No data showing:**
- Verify CSV path is correct
- Run RBI agent first to generate data
- Check CSV has proper column headers

**Templates not found:**
- Verify TEMPLATE_BASE_DIR points to correct location
- Ensure static/ and templates/ folders exist
