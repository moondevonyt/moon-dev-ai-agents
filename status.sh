#!/bin/bash
# 🌙 BB1151's System Status Checker

echo "================================================================"
echo "🌙 BB1151's AI Trading Research System - Status Check"
echo "================================================================"
echo ""

# Check processes
echo "📊 RUNNING PROCESSES:"
echo "────────────────────────────────────────────────────────────────"

research_pid=$(ps aux | grep "research_agent.py" | grep -v grep | awk '{print $2}')
rbi_pid=$(ps aux | grep "rbi_agent_pp_multi.py" | grep -v grep | awk '{print $2}')
dash_pid=$(ps aux | grep "app.py" | grep -v grep | awk '{print $2}')

if [ ! -z "$research_pid" ]; then
  echo "✅ Research Agent (PID: $research_pid)"
else
  echo "❌ Research Agent - NOT RUNNING"
fi

if [ ! -z "$rbi_pid" ]; then
  echo "✅ RBI Agent (PID: $rbi_pid)"
else
  echo "❌ RBI Agent - NOT RUNNING"
fi

if [ ! -z "$dash_pid" ]; then
  echo "✅ Dashboard (PID: $dash_pid)"
else
  echo "❌ Dashboard - NOT RUNNING"
fi

echo ""
echo "================================================================"
echo "📊 DASHBOARD STATS:"
echo "────────────────────────────────────────────────────────────────"

if [ ! -z "$dash_pid" ]; then
  curl -s http://localhost:8001/api/stats 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"   Total Backtests: {data['total_backtests']}\")
    print(f\"   Unique Strategies: {data['unique_strategies']}\")
    print(f\"   Max Return: {data['max_return']:.2f}%\")
    print(f\"   Avg Return: {data['avg_return']:.2f}%\")
except:
    print('   Dashboard initializing...')
" || echo "   Dashboard not responding"
else
  echo "   Dashboard not running"
fi

echo ""
echo "================================================================"
echo "📁 LOG FILES:"
echo "────────────────────────────────────────────────────────────────"

for log in logs/research_agent.log logs/rbi_agent.log logs/dashboard.log; do
  if [ -f "$log" ]; then
    size=$(du -h "$log" | cut -f1)
    lines=$(wc -l < "$log")
    echo "   $log ($size, $lines lines)"
  fi
done

echo ""
echo "================================================================"
echo "🔧 USEFUL COMMANDS:"
echo "────────────────────────────────────────────────────────────────"
echo "   View logs: tail -f logs/research_agent.log"
echo "   Dashboard: open http://localhost:8001"
echo "   Stop all:  pkill -f 'research_agent|rbi_agent|app.py'"
echo "================================================================"
