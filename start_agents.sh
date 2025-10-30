#!/bin/bash
# 🚀 Start All Agents Script

echo "════════════════════════════════════════════════════════════════"
echo "🚀 STARTING ALL AGENTS"
echo "════════════════════════════════════════════════════════════════"
echo ""

cd "$(dirname "$0")"

# Create logs directory if it doesn't exist
mkdir -p logs

# 1. Start Research Agent
echo "🧠 Starting Research Agent..."
/usr/bin/python3 src/agents/research_agent.py > logs/research_agent.log 2>&1 &
RESEARCH_PID=$!
echo "   ✅ Research Agent started (PID: $RESEARCH_PID)"

# 2. Start RBI Agent
echo "🤖 Starting RBI Agent..."
/usr/bin/python3 src/agents/rbi_agent_pp_multi.py > logs/rbi_agent.log 2>&1 &
RBI_PID=$!
echo "   ✅ RBI Agent started (PID: $RBI_PID)"

# 3. Start Dashboard
echo "📊 Starting Dashboard..."
/usr/bin/python3 src/data/rbi_pp_multi/app.py > logs/dashboard.log 2>&1 &
DASH_PID=$!
echo "   ✅ Dashboard started (PID: $DASH_PID)"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ ALL AGENTS STARTED!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Dashboard:       http://localhost:8001"
echo "📝 RBI Log:         tail -f logs/rbi_agent.log"
echo "📝 Research Log:    tail -f logs/research_agent.log"
echo "📝 Dashboard Log:   tail -f logs/dashboard.log"
echo ""
echo "PIDs:"
echo "   Research Agent: $RESEARCH_PID"
echo "   RBI Agent:      $RBI_PID"
echo "   Dashboard:      $DASH_PID"
echo ""
echo "════════════════════════════════════════════════════════════════"
