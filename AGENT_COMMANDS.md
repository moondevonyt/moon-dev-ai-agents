# 🚀 Agent Management Commands

Quick reference for starting, stopping and managing all agents.

---

## 📋 Quick Commands

### Start All Agents
```bash
./start_agents.sh
```

### Stop All Agents
```bash
./stop_agents.sh
```

### Check Status
```bash
./check_agents.sh
```

---

## 🤖 Individual Agent Control

### Research Agent
```bash
# Start
/usr/bin/python3 src/agents/research_agent.py > logs/research_agent.log 2>&1 &

# Stop
pkill -f research_agent.py

# View Log
tail -f logs/research_agent.log
```

### RBI Agent (Backtesting)
```bash
# Start
/usr/bin/python3 src/agents/rbi_agent_pp_multi.py > logs/rbi_agent.log 2>&1 &

# Stop
pkill -f rbi_agent_pp_multi.py

# View Log
tail -f logs/rbi_agent.log
```

### Dashboard
```bash
# Start
/usr/bin/python3 src/data/rbi_pp_multi/app.py > logs/dashboard.log 2>&1 &

# Stop
pkill -f app.py

# View Log
tail -f logs/dashboard.log

# URL
http://localhost:8001
```

### Twitter Agent (optional)
```bash
# Start
/usr/bin/python3 src/agents/twitter_agent.py > logs/twitter_agent.log 2>&1 &

# Stop
pkill -f twitter_agent.py

# View Log
tail -f logs/twitter_agent.log
```

---

## 📊 Monitoring

### View All Logs
```bash
tail -f logs/*.log
```

### Check Running Processes
```bash
ps aux | grep -E '(research_agent|rbi_agent|app.py)' | grep -v grep
```

### Monitor Live Backtests
```bash
/usr/bin/python3 monitor_backtests.py
```

---

## 🔧 Troubleshooting

### Kill All Python Processes
```bash
pkill -9 python3
```
⚠️ **Warning:** This kills ALL Python processes!

### Free Port 8001 (Dashboard Port)
```bash
lsof -ti:8001 | xargs kill -9
```

### Check Which Process Uses Port
```bash
lsof -i:8001
```

### Restart Everything
```bash
./stop_agents.sh
sleep 3
./start_agents.sh
```

---

## 📁 File Locations

| File | Location |
|------|----------|
| **Scripts** | `./start_agents.sh`, `./stop_agents.sh`, `./check_agents.sh` |
| **Logs** | `logs/*.log` |
| **Backtest Results** | `src/data/rbi_pp_multi/backtest_stats.csv` |
| **Ideas File** | `src/data/rbi_pp_multi/ideas.txt` |
| **Dashboard** | http://localhost:8001 |

---

## 🚨 Common Issues

### "Insufficient Balance" Error
```bash
# DeepSeek API balance empty
# Solution: Update API key or switch to different LLM
# Edit: src/agents/rbi_agent_pp_multi.py
```

### Dashboard Shows Old Data
```bash
# Check if RBI Agent is running
./check_agents.sh

# Check for errors in log
tail -50 logs/rbi_agent.log | grep -i error
```

### No New Backtests
```bash
# Check ideas.txt has content
cat src/data/rbi_pp_multi/ideas.txt

# Check RBI Agent is processing
tail -f logs/rbi_agent.log
```

---

## 💡 Tips

- Use `./check_agents.sh` regularly to verify agents are running
- Monitor logs with `tail -f logs/*.log` in a separate terminal
- Dashboard auto-refreshes every 10 seconds
- RBI Agent processes ideas from `ideas.txt` continuously
- Research Agent generates new trading ideas automatically

---

**Last Updated:** 2025-10-30
