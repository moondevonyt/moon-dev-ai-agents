"""
🌙 Moon Dev's AI Agent Backtests Dashboard 🚀
FastAPI web interface for viewing backtest results from rbi_agent_pp_multi.py
Built with love by Moon Dev

================================================================================
📋 HOW TO USE THIS DASHBOARD:
================================================================================

1. RUN THE RBI AGENT to generate backtest results:
   ```bash
   python src/agents/rbi_agent_pp_multi.py
   ```
   This will create a CSV file with all your backtest stats at:
   src/data/rbi_pp_multi/backtest_stats.csv

2. CONFIGURE THE CSV PATH below (line 60) to point to your stats CSV

3. RUN THIS DASHBOARD:
   ```bash
   python src/scripts/backtestdashboard.py
   ```

4. OPEN YOUR BROWSER to: http://localhost:8001

================================================================================
⚙️ CONFIGURATION:
================================================================================
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from pathlib import Path
import uvicorn
import shutil
import subprocess
import threading
from datetime import datetime

# ============================================================================
# 🔧 CONFIGURATION - CHANGE THESE PATHS TO MATCH YOUR SETUP!
# ============================================================================

# 📊 Path to your backtest stats CSV file
# This CSV is created by rbi_agent_pp_multi.py after running backtests
# Default: src/data/rbi_pp_multi/backtest_stats.csv
project_root = Path(__file__).parent.parent.parent
STATS_CSV = project_root / "src/data/rbi_pp_multi/backtest_stats.csv"

# 📁 Directory for static files (CSS, JS) and templates (HTML)
# Using rbi_pp_multi folder as in README
TEMPLATE_BASE_DIR = project_root / "src/data/rbi_pp_multi"

# 🗂️ Directory to store user-created folders
# Folders allow you to organize and group your backtest results
USER_FOLDERS_DIR = TEMPLATE_BASE_DIR / "user_folders"

# 🎯 Target return percentage (must match rbi_agent_pp_multi.py TARGET_RETURN)
TARGET_RETURN = 50  # % - Optimization goal
SAVE_IF_OVER_RETURN = 1.0  # % - Minimum return to save to CSV

# ============================================================================
# 🚀 FASTAPI APP INITIALIZATION
# ============================================================================

app = FastAPI(title="Moon Dev's AI Agent Backtests")

# Create user_folders directory if it doesn't exist
USER_FOLDERS_DIR.mkdir(exist_ok=True)

# Track running backtests
running_backtests = {}

# Mount static files and templates
app.mount("/static", StaticFiles(directory=str(TEMPLATE_BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(TEMPLATE_BASE_DIR / "templates"))


# 🌙 Moon Dev: Request models for folder operations
class AddToFolderRequest(BaseModel):
    folder_name: str
    backtests: List[Dict[str, Any]]


class DeleteFolderRequest(BaseModel):
    folder_name: str


class BacktestRunRequest(BaseModel):
    ideas: str
    run_name: str


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the main dashboard page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/backtests")
async def get_backtests():
    """API endpoint to fetch all backtest data"""
    try:
        if not STATS_CSV.exists():
            return JSONResponse({
                "data": [],
                "message": "No backtest data found yet. Run rbi_agent_pp_multi.py to generate results!"
            })

        # Read CSV
        df = pd.read_csv(STATS_CSV)

        # Debug: Print columns
        print(f"📊 CSV Columns: {list(df.columns)}")
        print(f"📊 Row count: {len(df)}")

        # Convert numeric columns, replacing 'N/A' with NaN
        numeric_cols = ['Return %', 'Buy & Hold %', 'Max Drawdown %', 'Sharpe Ratio', 'Sortino Ratio', 'EV %', 'Trades']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Replace inf/-inf with None (can't JSON serialize infinity!)
        df = df.replace([np.inf, -np.inf], None)

        # Replace NaN with None for JSON serialization
        df = df.where(pd.notnull(df), None)

        # Convert to records and clean floats
        data = []
        for record in df.to_dict('records'):
            cleaned_record = {}
            for key, value in record.items():
                # Check if value is a problematic float
                if isinstance(value, (float, np.floating)):
                    if np.isnan(value) or np.isinf(value):
                        cleaned_record[key] = None
                    else:
                        cleaned_record[key] = float(value)
                else:
                    cleaned_record[key] = value
            data.append(cleaned_record)

        return JSONResponse({
            "data": data,
            "total": len(data),
            "message": f"Loaded {len(data)} backtest results"
        })

    except Exception as e:
        print(f"❌ Error in /api/backtests: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "data": [],
            "error": str(e),
            "message": "Error loading backtest data"
        }, status_code=500)


@app.get("/api/stats")
async def get_stats():
    """API endpoint for summary statistics"""
    try:
        if not STATS_CSV.exists():
            return JSONResponse({
                "total_backtests": 0,
                "unique_strategies": 0,
                "unique_data_sources": 0,
                "avg_return": 0,
                "max_return": 0,
                "avg_sortino": 0,
                "message": "No data yet"
            })

        df = pd.read_csv(STATS_CSV)

        print(f"📊 Stats CSV Columns: {list(df.columns)}")

        # Convert numeric columns, replacing 'N/A' with NaN
        numeric_cols = ['Return %', 'Buy & Hold %', 'Max Drawdown %', 'Sharpe Ratio', 'Sortino Ratio', 'EV %', 'Trades']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Replace inf/-inf with NaN (can't calculate stats on infinity!)
        df = df.replace([float('inf'), float('-inf')], float('nan'))

        # Helper function to safely get numeric stat
        def safe_stat(series, func, default=0):
            try:
                val = func(series)
                if pd.isna(val) or np.isinf(val) or not isinstance(val, (int, float)):
                    return default
                # Ensure it's JSON-safe
                val = float(val)
                if np.isnan(val) or np.isinf(val):
                    return default
                return round(val, 2)
            except:
                return default

        stats = {
            "total_backtests": len(df),
            "unique_strategies": df['Strategy Name'].nunique() if 'Strategy Name' in df.columns else 0,
            "unique_data_sources": df['Data'].nunique() if 'Data' in df.columns else 0,
            "avg_return": safe_stat(df['Return %'], lambda s: s.mean()) if 'Return %' in df.columns else 0,
            "max_return": safe_stat(df['Return %'], lambda s: s.max()) if 'Return %' in df.columns else 0,
            "avg_sortino": safe_stat(df['Sortino Ratio'], lambda s: s.mean()) if 'Sortino Ratio' in df.columns else 0,
        }

        return JSONResponse(stats)

    except Exception as e:
        print(f"❌ Error in /api/stats: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/folders")
async def get_folders():
    """🌙 Moon Dev: Get list of all folder names"""
    try:
        folders = [f.name for f in USER_FOLDERS_DIR.iterdir() if f.is_dir()]
        return JSONResponse({"folders": sorted(folders)})
    except Exception as e:
        print(f"❌ Error in /api/folders: {str(e)}")
        return JSONResponse({"folders": [], "error": str(e)}, status_code=500)


@app.get("/api/folders/list")
async def list_folders_with_details():
    """🌙 Moon Dev: Get folders with backtest counts"""
    try:
        folders_info = []

        for folder_path in USER_FOLDERS_DIR.iterdir():
            if folder_path.is_dir():
                csv_path = folder_path / "backtest_stats.csv"
                count = 0

                if csv_path.exists():
                    df = pd.read_csv(csv_path)
                    count = len(df)

                folders_info.append({
                    "name": folder_path.name,
                    "count": count
                })

        return JSONResponse({"folders": sorted(folders_info, key=lambda x: x['name'])})

    except Exception as e:
        print(f"❌ Error in /api/folders/list: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"folders": [], "error": str(e)}, status_code=500)


@app.post("/api/folders/add")
async def add_to_folder(request: AddToFolderRequest):
    """🌙 Moon Dev: Add backtests to a folder (duplicates rows, doesn't move)"""
    try:
        folder_name = request.folder_name
        backtests = request.backtests

        # Create folder if it doesn't exist
        folder_path = USER_FOLDERS_DIR / folder_name
        folder_path.mkdir(exist_ok=True)

        folder_csv = folder_path / "backtest_stats.csv"

        # Convert backtests to DataFrame
        new_df = pd.DataFrame(backtests)

        # If folder CSV exists, append to it; otherwise create new
        if folder_csv.exists():
            existing_df = pd.read_csv(folder_csv)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df.to_csv(folder_csv, index=False)
            print(f"📁 Added {len(new_df)} backtests to existing folder '{folder_name}'")
        else:
            new_df.to_csv(folder_csv, index=False)
            print(f"📁 Created new folder '{folder_name}' with {len(new_df)} backtests")

        return JSONResponse({
            "success": True,
            "message": f"Added {len(backtests)} backtest(s) to '{folder_name}'"
        })

    except Exception as e:
        print(f"❌ Error in /api/folders/add: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "error": str(e),
            "message": "Failed to add backtests to folder"
        }, status_code=500)


@app.get("/api/folders/{folder_name}/paths")
async def get_folder_paths(folder_name: str):
    """🌙 Moon Dev: Get all file paths from a folder"""
    try:
        folder_path = USER_FOLDERS_DIR / folder_name
        csv_path = folder_path / "backtest_stats.csv"

        if not csv_path.exists():
            return JSONResponse({
                "success": False,
                "message": f"Folder '{folder_name}' has no backtest data"
            }, status_code=404)

        # Read CSV and extract file paths
        df = pd.read_csv(csv_path)

        if 'File Path' not in df.columns:
            return JSONResponse({
                "success": False,
                "message": "No 'File Path' column found in folder data"
            }, status_code=400)

        # Get all file paths, filter out any null/empty values
        paths = df['File Path'].dropna().tolist()

        print(f"📁 Retrieved {len(paths)} paths from folder '{folder_name}'")

        return JSONResponse({
            "success": True,
            "paths": paths,
            "count": len(paths)
        })

    except Exception as e:
        print(f"❌ Error in /api/folders/{folder_name}/paths: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "error": str(e),
            "message": "Failed to get folder paths"
        }, status_code=500)


@app.get("/api/backtest/status/{run_name}")
async def get_backtest_status(run_name: str):
    """🌙 Moon Dev: Check status of a running backtest"""
    try:
        if run_name not in running_backtests:
            return JSONResponse({
                "status": "not_found",
                "message": f"No backtest found with name '{run_name}'"
            })

        status_info = running_backtests[run_name]
        return JSONResponse({
            "status": status_info["status"],
            "new_count": status_info["new_count"],
            "run_name": run_name
        })

    except Exception as e:
        print(f"❌ Error in /api/backtest/status: {str(e)}")
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)


@app.post("/api/folders/delete")
async def delete_folder(request: DeleteFolderRequest):
    """🌙 Moon Dev: Delete a folder and all its contents"""
    try:
        folder_name = request.folder_name
        folder_path = USER_FOLDERS_DIR / folder_name

        if not folder_path.exists():
            return JSONResponse({
                "success": False,
                "message": f"Folder '{folder_name}' does not exist"
            }, status_code=404)

        # Delete the entire folder
        shutil.rmtree(folder_path)
        print(f"🗑️ Deleted folder '{folder_name}'")

        return JSONResponse({
            "success": True,
            "message": f"Deleted folder '{folder_name}'"
        })

    except Exception as e:
        print(f"❌ Error in /api/folders/delete: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "error": str(e),
            "message": "Failed to delete folder"
        }, status_code=500)


@app.post("/api/backtest/run")
async def run_backtest(request: BacktestRunRequest):
    """🌙 Moon Dev: Run rbi_agent_pp_multi.py with custom ideas"""
    try:
        ideas = request.ideas
        run_name = request.run_name

        print(f"\n🚀 Starting backtest run: '{run_name}'")
        print(f"📝 Ideas:\n{ideas}\n")

        # Create temp ideas file in the template base dir
        temp_ideas_file = TEMPLATE_BASE_DIR / f"temp_ideas_{run_name}.txt"
        with open(temp_ideas_file, 'w') as f:
            f.write(ideas)

        print(f"📁 Created temp ideas file: {temp_ideas_file}")

        # Path to rbi_agent_pp_multi.py
        script_path = Path(__file__).parent.parent / "agents" / "rbi_agent_pp_multi.py"

        if not script_path.exists():
            return JSONResponse({
                "success": False,
                "message": f"Script not found at {script_path}"
            }, status_code=404)

        # Create snapshot of CSV before running (for auto-add to folder later)
        csv_before_path = TEMPLATE_BASE_DIR / f"temp_csv_before_{run_name}.csv"
        if STATS_CSV.exists():
            shutil.copy(STATS_CSV, csv_before_path)
            print(f"📸 Created CSV snapshot for comparison")

        # Function to run in background
        def run_backtest_background():
            try:
                print(f"\n{'='*60}")
                print(f"🏃 Running backtest script for '{run_name}'...")
                print(f"{'='*60}\n")

                running_backtests[run_name] = {"status": "running", "new_count": 0}

                # Run the script with temp ideas file
                result = subprocess.run(
                    ["python", str(script_path), "--ideas-file", str(temp_ideas_file), "--run-name", run_name],
                    capture_output=True,
                    text=True,
                    timeout=3600  # 1 hour timeout
                )

                print(f"\n{'='*60}")
                print(f"✅ BACKTEST COMPLETED: '{run_name}'")
                print(f"{'='*60}")
                print(f"Return code: {result.returncode}")
                if result.returncode != 0:
                    print(f"⚠️ Script exited with non-zero code")

                # Show last 50 lines of output
                stdout_lines = result.stdout.split('\n')
                print(f"\n📊 Last 50 lines of output:")
                print('\n'.join(stdout_lines[-50:]))

                if result.stderr:
                    print(f"\n⚠️ STDERR:\n{result.stderr}")

                # Clean up temp file
                if temp_ideas_file.exists():
                    temp_ideas_file.unlink()
                    print(f"\n🗑️ Cleaned up temp ideas file")

                # Auto-add results to folder
                print(f"\n{'='*60}")
                new_count = auto_add_to_folder(run_name, str(csv_before_path))
                print(f"{'='*60}\n")

                running_backtests[run_name] = {"status": "complete", "new_count": new_count}

            except subprocess.TimeoutExpired:
                print(f"\n{'='*60}")
                print(f"❌ Backtest '{run_name}' timed out after 1 hour")
                print(f"{'='*60}\n")
                running_backtests[run_name] = {"status": "timeout", "new_count": 0}
            except Exception as e:
                print(f"\n{'='*60}")
                print(f"❌ Error running backtest '{run_name}': {str(e)}")
                print(f"{'='*60}")
                import traceback
                traceback.print_exc()
                running_backtests[run_name] = {"status": "error", "new_count": 0}

        # Start background thread
        thread = threading.Thread(target=run_backtest_background, daemon=True)
        thread.start()

        return JSONResponse({
            "success": True,
            "message": f"Backtest '{run_name}' started in background",
            "run_name": run_name
        })

    except Exception as e:
        print(f"❌ Error in /api/backtest/run: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "error": str(e),
            "message": "Failed to start backtest"
        }, status_code=500)


def auto_add_to_folder(run_name: str, csv_before_path: str) -> int:
    """🌙 Moon Dev: Automatically add new winning backtests to a folder"""
    try:
        print(f"📁 Auto-adding results to folder '{run_name}'...")

        # Read main CSV
        if not STATS_CSV.exists():
            print(f"❌ Main CSV not found")
            return 0

        df_after = pd.read_csv(STATS_CSV)

        # Read CSV snapshot from before run
        if not Path(csv_before_path).exists():
            print(f"❌ Before-run CSV snapshot not found")
            return 0

        df_before = pd.read_csv(csv_before_path)

        # Find new rows (rows in df_after that aren't in df_before)
        # Simple approach: compare row counts and take the difference
        before_count = len(df_before)
        after_count = len(df_after)
        new_count = after_count - before_count

        if new_count <= 0:
            print(f"ℹ️ Zero backtests passed the {SAVE_IF_OVER_RETURN}% return threshold")
            return 0

        print(f"✅ Found {new_count} new backtest(s)")

        # Get the new rows (last N rows)
        new_rows = df_after.tail(new_count)

        # Create folder
        folder_path = USER_FOLDERS_DIR / run_name
        folder_path.mkdir(exist_ok=True)

        folder_csv = folder_path / "backtest_stats.csv"

        # Save new rows to folder CSV
        new_rows.to_csv(folder_csv, index=False)

        print(f"✅ Successfully added {new_count} backtest(s) to folder '{run_name}'")
        print(f"📂 Folder location: {folder_path}")

        # Clean up snapshot
        Path(csv_before_path).unlink()
        print(f"🗑️ Cleaned up CSV snapshot")

        return new_count

    except Exception as e:
        print(f"❌ Error in auto_add_to_folder: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🌙 Moon Dev's AI Agent Backtests Dashboard 🚀")
    print("="*80)
    print(f"\n📊 CSV Path: {STATS_CSV}")
    print(f"📁 Templates: {TEMPLATE_BASE_DIR}")
    print(f"🌐 Starting server at: http://localhost:8001")
    print(f"\n💡 NOTE: Make sure you've run rbi_agent_pp_multi.py first to generate backtest data!")
    print(f"💡 Port 8001 is used to avoid conflict with main API on port 8000")
    print("\nPress CTRL+C to stop\n")

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

# 🎨 Visualization route
@app.get("/visualization/top_strategy.html", response_class=HTMLResponse)
async def serve_visualization():
    """Serve the Bokeh visualization HTML"""
    viz_file = TEMPLATE_BASE_DIR / "visualization" / "top_strategy.html"
    
    if not viz_file.exists():
        return HTMLResponse(
            content="""
            <html>
            <body style="font-family: system-ui; padding: 40px; text-align: center;">
                <h1>📊 Visualization Not Generated Yet</h1>
                <p>Run the visualization generator first:</p>
                <pre style="background: #f0f0f0; padding: 20px; border-radius: 8px; display: inline-block;">
cd /Users/bb1151/Desktop/git_projects/bb1151-dev-ai-agents
python3 src/data/rbi_pp_multi/visualization/generate_viz.py
                </pre>
                <p><a href="/" style="color: blue;">← Back to Dashboard</a></p>
            </body>
            </html>
            """,
            status_code=404
        )
    
    with open(viz_file, 'r') as f:
        content = f.read()
    
    return HTMLResponse(content=content)


# 🌍 Multi-Asset Visualization route
@app.get("/visualization/multi_asset_results.html", response_class=HTMLResponse)
async def serve_multi_asset_visualization():
    """Serve the Multi-Asset Bokeh visualization HTML"""
    viz_file = TEMPLATE_BASE_DIR / "visualization" / "multi_asset_results.html"
    
    if not viz_file.exists():
        return HTMLResponse(
            content="""
            <html>
            <body style="font-family: system-ui; padding: 40px; text-align: center;">
                <h1>🌍 Multi-Asset Visualization Not Generated Yet</h1>
                <p>Run the multi-asset visualization generator first:</p>
                <pre style="background: #f0f0f0; padding: 20px; border-radius: 8px; display: inline-block;">
cd /Users/bb1151/Desktop/git_projects/bb1151-dev-ai-agents
python3 src/data/rbi_pp_multi/visualization/generate_multi_viz.py
                </pre>
                <p><a href="/" style="color: blue;">← Back to Dashboard</a></p>
            </body>
            </html>
            """,
            status_code=404
        )
    
    with open(viz_file, 'r') as f:
        content = f.read()
    
    return HTMLResponse(content=content)
