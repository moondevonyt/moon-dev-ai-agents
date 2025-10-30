#!/bin/bash
# 🛑 Stop All Agents Script

echo "════════════════════════════════════════════════════════════════"
echo "🛑 STOPPING ALL AGENTS"
echo "════════════════════════════════════════════════════════════════"
echo ""

cd "$(dirname "$0")"

# Stop Research Agent
echo "🧠 Stopping Research Agent..."
pkill -f "research_agent.py" && echo "   ✅ Research Agent stopped" || echo "   ⚠️  Research Agent not running"

# Stop RBI Agent
echo "🤖 Stopping RBI Agent..."
pkill -f "rbi_agent_pp_multi.py" && echo "   ✅ RBI Agent stopped" || echo "   ⚠️  RBI Agent not running"

# Stop Dashboard
echo "📊 Stopping Dashboard..."
pkill -f "app.py" && echo "   ✅ Dashboard stopped" || echo "   ⚠️  Dashboard not running"

# Stop Twitter Agent (if running)
echo "🐦 Stopping Twitter Agent (if running)..."
pkill -f "twitter_agent.py" && echo "   ✅ Twitter Agent stopped" || echo "   ⚠️  Twitter Agent not running"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ ALL AGENTS STOPPED!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "💡 To start agents again, run: ./start_agents.sh"
echo ""
