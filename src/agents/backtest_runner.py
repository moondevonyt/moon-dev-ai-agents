"""
🌙 Moon Dev's Backtest Execution Runner
Proof of concept for running backtests in conda environment
"""

import subprocess
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# CONFIGURATION - Change this to test different files
BACKTEST_FILE = "/src/agents/test_backtest_working.py"
CONDA_ENV = "tflow"  # Your conda environment name

def run_backtest_in_conda(file_path: str, conda_env: str = "tflow"):
    """
    Run a backtest file in a conda environment and capture all output
    
    Returns dict with:
    - stdout: Standard output (results, prints)
    - stderr: Standard error (errors, tracebacks)
    - return_code: 0 for success, non-zero for failure
    - execution_time: How long it took
    """
    
    print(f"\n🚀 Moon Dev's Backtest Runner Starting!")
    print(f"📂 File: {file_path}")
    print(f"🐍 Conda env: {conda_env}")
    print("=" * 60)
    
    if not os.path.exists(file_path):
        return {
            "error": f"File not found: {file_path}",
            "success": False
        }
    
    # Build the command to run in conda environment
    cmd = [
        "conda", "run", "-n", conda_env,
        "python", file_path
    ]
    
    print(f"🔧 Command: {' '.join(cmd)}")
    print("=" * 60)
    
    start_time = datetime.now()
    
    try:
        # Run the backtest with timeout of 5 minutes
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        output = {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
        # Print results
        print("\n📊 EXECUTION RESULTS:")
        print(f"✅ Success: {output['success']}")
        print(f"⏱️  Execution time: {output['execution_time']:.2f} seconds")
        print(f"🔢 Return code: {output['return_code']}")
        
        if output['stdout']:
            print("\n📈 STANDARD OUTPUT:")
            print("-" * 60)
            print(output['stdout'])
            print("-" * 60)
        
        if output['stderr']:
            print("\n❌ ERRORS/WARNINGS:")
            print("-" * 60)
            print(output['stderr'])
            print("-" * 60)
            
        return output
        
    except subprocess.TimeoutExpired:
        execution_time = (datetime.now() - start_time).total_seconds()
        print("\n⏰ TIMEOUT: Execution exceeded 5 minutes!")
        return {
            "success": False,
            "error": "Execution timeout (300 seconds)",
            "execution_time": execution_time
        }
        
    except Exception as e:
        print(f"\n💥 EXCEPTION: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "exception_type": type(e).__name__
        }

def parse_backtest_output(output: dict):
    """
    Parse the output to extract key information
    This is where you'd extract stats, errors, etc.
    """
    if not output.get('success'):
        # Parse error information
        error_info = {
            "has_error": True,
            "error_type": None,
            "error_message": output.get('stderr', ''),
            "error_line": None
        }
        
        # Try to extract error details from stderr
        stderr = output.get('stderr', '')
        if 'Traceback' in stderr:
            lines = stderr.split('\n')
            for i, line in enumerate(lines):
                if 'File' in line and '.py' in line:
                    # Extract file and line number
                    if 'line' in line:
                        try:
                            error_info['error_line'] = int(line.split('line ')[1].split(',')[0])
                        except:
                            pass
                            
                if line.strip() and not line.startswith(' ') and i > 0:
                    # This is likely the error type
                    error_info['error_type'] = line.split(':')[0].strip()
                    
        return error_info
    else:
        # Parse successful output for stats
        stats_info = {
            "has_error": False,
            "stats_found": False,
            "stats": {}
        }
        
        stdout = output.get('stdout', '')
        
        # Look for common backtesting.py output patterns
        if 'Start' in stdout and 'End' in stdout:
            stats_info['stats_found'] = True
            # Add more parsing logic here based on backtesting.py output format
            
        return stats_info

def save_results(output: dict, file_path: str):
    """Save results to a JSON file for later analysis"""
    results_dir = Path(__file__).parent.parent / "data" / "execution_results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Create filename based on backtest file
    backtest_name = Path(file_path).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"{backtest_name}_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(output, f, indent=2)
        
    print(f"\n💾 Results saved to: {results_file}")
    return results_file

def main():
    """Run the backtest and demonstrate output capture"""
    
    print("🌙 Moon Dev's Backtest Execution Proof of Concept")
    print("=" * 60)
    print(f"🎯 Target file: {BACKTEST_FILE}")
    print(f"🐍 Using conda env: {CONDA_ENV}")
    print("=" * 60)
    
    # Run the backtest
    result = run_backtest_in_conda(BACKTEST_FILE, CONDA_ENV)
    
    # Parse the results
    parsed = parse_backtest_output(result)
    
    print("\n🔍 PARSED RESULTS:")
    print(json.dumps(parsed, indent=2))
    
    # Save results
    saved_file = save_results(result, BACKTEST_FILE)
    
    print("\n✨ SUMMARY:")
    if result.get('success'):
        print("✅ Backtest executed successfully!")
        print("📊 Check stdout for strategy statistics")
    else:
        print("❌ Backtest failed with errors")
        if parsed.get('error_type'):
            print(f"🐛 Error type: {parsed['error_type']}")
            if parsed.get('error_line'):
                print(f"📍 Error line: {parsed['error_line']}")
    
    print("\n🚀 This proves we can:")
    print("1. ✅ Execute backtest code in conda environment")
    print("2. ✅ Capture all output (stdout/stderr)")
    print("3. ✅ Parse errors and results")
    print("4. ✅ Feed this back to debugging agents")
    print("\n💡 Ready to build the full execution agent!")
    
    return result

if __name__ == "__main__":
    main()