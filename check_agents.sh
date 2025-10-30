#!/bin/bash
# 🔍 Check Agent Status Script

echo "════════════════════════════════════════════════════════════════"
echo "🔍 AGENT STATUS CHECK"
echo "════════════════════════════════════════════════════════════════"
echo ""

cd "$(dirname "$0")"

# Function to check if process is running
check_process() {
    local name=$1
    local pattern=$2
    
    if pgrep -f "$pattern" > /dev/null 2>&1; then
        PID=$(pgrep -f "$pattern")
        RUNTIME=$(ps -p $PID -o etime= 2>/dev/null || echo "N/A")
        echo "✅ $name: RUNNING (PID: $PID, Runtime: $RUNTIME)"
    else
        echo "❌ $name: NOT RUNNING"
    fi
}

# Check all agents
check_process "Research Agent " "research_agent.py"
check_process "RBI Agent     " "rbi_agent_pp_multi.py"
check_process "Dashboard     " "app.py"
check_process "Twitter Agent " "twitter_agent.py"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📊 QUICK STATS"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check latest backtests
if [ -f "src/data/rbi_pp_multi/backtest_stats.csv" ]; then
    TOTAL=$(wc -l < src/data/rbi_pp_multi/backtest_stats.csv)
    echo "📈 Total Backtests: $((TOTAL - 1))"
    
    echo ""
    echo "📝 Latest 3 Backtests:"
    tail -3 src/data/rbi_pp_multi/backtest_stats.csv | cut -d',' -f1,14 | \
        awk -F',' '{printf "   - %s (%s)\n", $1, $2}'
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🔗 QUICK LINKS"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Dashboard:       http://localhost:8001"
echo "📝 RBI Log:         tail -f logs/rbi_agent.log"
echo "📝 Research Log:    tail -f logs/research_agent.log"
echo ""
echo "Commands:"
echo "   Start:  ./start_agents.sh"
echo "   Stop:   ./stop_agents.sh"
echo "   Status: ./check_agents.sh"
echo ""
