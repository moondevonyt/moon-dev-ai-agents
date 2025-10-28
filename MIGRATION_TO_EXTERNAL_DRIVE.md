# Migration Guide: Move to Evo Plus 2a External Drive

## 📦 What We're Moving

| Item | Size | From | To |
|------|------|------|-----|
| **Project** | ~100 MB | `~/Desktop/APPS/AI AGENTS/` | `/media/squareyes/Evo Plus 2a/AI_Projects/` |
| **Virtual Env** | ~300 MB | Inside project | (moves with project) |
| **Ollama Models** | ~3.3 GB | `~/.ollama/models/` | `/media/squareyes/Evo Plus 2a/ollama_models/` |
| **Total Saved** | **~3.7 GB** | Laptop SSD | External Drive |

---

## ⚠️ IMPORTANT: Safety First!

**Before we start:**
1. Make sure the Evo Plus 2a drive is plugged in and mounted
2. Stop all running agents (Ctrl+C if any are running)
3. This is a COPY operation first - we'll delete originals AFTER testing

---

## 🚀 Step-by-Step Migration

### **Step 1: Verify Drive is Mounted**

```bash
# Check the drive is accessible
df -h | grep "Evo Plus 2a"
ls "/media/squareyes/Evo Plus 2a"
```

**You should see the drive listed.** If not, make sure it's plugged in.

---

### **Step 2: Create Folder Structure on External Drive**

```bash
# Create main folder for AI projects
mkdir -p "/media/squareyes/Evo Plus 2a/AI_Projects"

# Create folder for Ollama models
mkdir -p "/media/squareyes/Evo Plus 2a/ollama_models"

# Verify folders created
ls -la "/media/squareyes/Evo Plus 2a/"
```

**You should see: AI_Projects/ and ollama_models/**

---

### **Step 3: Copy Project Files (Keep Original for Now)**

```bash
# Navigate to current location
cd ~/Desktop/APPS/AI\ AGENTS/

# Copy entire project to external drive (this takes 2-3 minutes)
echo "📦 Copying project files..."
cp -rv moon-dev-ai-agents-main "/media/squareyes/Evo Plus 2a/AI_Projects/"

# Verify copy completed
ls -lh "/media/squareyes/Evo Plus 2a/AI_Projects/moon-dev-ai-agents-main"
```

**Important:** The `-v` flag shows progress. Watch for any errors.

---

### **Step 4: Stop Ollama Service**

```bash
# Stop Ollama (so we can move models safely)
sudo systemctl stop ollama

# Verify it stopped
curl http://localhost:11434
# Should say "Connection refused" (that's good!)
```

---

### **Step 5: Copy Ollama Models**

```bash
# Copy models to external drive (this takes 3-5 minutes - 3.3GB)
echo "📦 Copying Ollama models..."
cp -rv ~/.ollama/models/* "/media/squareyes/Evo Plus 2a/ollama_models/"

# Verify models copied
ls -lh "/media/squareyes/Evo Plus 2a/ollama_models/"
# You should see: blobs/ and manifests/ folders
```

---

### **Step 6: Create Symlink for Ollama Models**

```bash
# Backup original models folder name (don't delete yet!)
mv ~/.ollama/models ~/.ollama/models_BACKUP

# Create symlink pointing to external drive
ln -s "/media/squareyes/Evo Plus 2a/ollama_models" ~/.ollama/models

# Verify symlink created
ls -la ~/.ollama/
# You should see: models -> /media/squareyes/Evo Plus 2a/ollama_models
```

---

### **Step 7: Restart Ollama and Test**

```bash
# Start Ollama service
sudo systemctl start ollama

# Wait 5 seconds for it to start
sleep 5

# Test Ollama can see models
ollama list
```

**Expected output:**
```
NAME            ID              SIZE      MODIFIED
llama3.2:1b     ...             1.3 GB    X ago
llama3.2        ...             2.0 GB    X ago
```

**If you see your models listed, SUCCESS!** ✅

---

### **Step 8: Test the Project from New Location**

```bash
# Navigate to NEW location on external drive
cd "/media/squareyes/Evo Plus 2a/AI_Projects/moon-dev-ai-agents-main"

# Activate virtual environment
source venv/bin/activate

# Test Python can find packages
python -c "import pandas, requests; print('✅ Packages work!')"

# Quick test - import Ollama model
python -c "
from src.models.model_factory import ModelFactory
model = ModelFactory.create_model('ollama')
print('✅ Ollama integration works!')
"
```

**If all tests pass, everything is working from the external drive!** ✅

---

### **Step 9: Update Your Workflow**

**NEW commands to use from now on:**

```bash
# Navigate to project (NEW location)
cd "/media/squareyes/Evo Plus 2a/AI_Projects/moon-dev-ai-agents-main"

# Activate virtual environment
source venv/bin/activate

# Run any agent
python src/agents/polymarket_agent.py
python src/agents/trading_agent.py
python src/agents/rbi_agent.py
```

**Optional:** Create a shortcut alias in your `~/.bashrc`:

```bash
# Add this to end of ~/.bashrc
alias moon-agents='cd "/media/squareyes/Evo Plus 2a/AI_Projects/moon-dev-ai-agents-main" && source venv/bin/activate'
```

Then you can just type:
```bash
moon-agents
python src/agents/trading_agent.py
```

---

### **Step 10: Clean Up Old Files (ONLY AFTER TESTING!)**

**⚠️ ONLY DO THIS AFTER YOU'VE TESTED EVERYTHING WORKS!**

```bash
# Remove old project folder from laptop
rm -rf ~/Desktop/APPS/AI\ AGENTS/moon-dev-ai-agents-main

# Remove old Ollama models backup
rm -rf ~/.ollama/models_BACKUP

# Check space saved on laptop
df -h ~
```

**You should have ~3.7GB more free space!** 🎉

---

## 🧪 Testing Checklist

Before cleaning up old files, verify:

- [ ] Ollama lists models correctly (`ollama list`)
- [ ] Can activate virtual environment from new location
- [ ] Python packages import correctly
- [ ] Ollama model loads in Python
- [ ] External drive is stable (doesn't randomly disconnect)
- [ ] Ran at least one agent successfully

**Once ALL checked, safe to clean up old files!**

---

## 🔧 Troubleshooting

### **"Ollama can't find models"**

```bash
# Check symlink is correct
ls -la ~/.ollama/models
# Should point to: /media/squareyes/Evo Plus 2a/ollama_models

# If broken, recreate it:
rm ~/.ollama/models
ln -s "/media/squareyes/Evo Plus 2a/ollama_models" ~/.ollama/models
sudo systemctl restart ollama
```

### **"Permission denied" when copying**

```bash
# Add sudo to copy commands
sudo cp -rv ~/.ollama/models/* "/media/squareyes/Evo Plus 2a/ollama_models/"
```

### **"Drive not found"**

```bash
# Check exact mount point
mount | grep "Evo Plus"
# Use the exact path shown
```

### **"Virtual environment doesn't work"**

```bash
# Recreate venv in new location
cd "/media/squareyes/Evo Plus 2a/AI_Projects/moon-dev-ai-agents-main"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📊 Space Saved

**Before:**
```
Laptop SSD: ~3.7 GB used by project + Ollama
External Drive: Empty
```

**After:**
```
Laptop SSD: ~200 MB (symlink + Ollama binary)
External Drive: ~3.7 GB (project + models)
Net Saved: ~3.5 GB on laptop! ✅
```

---

## ⚡ Performance Notes

**Evo Plus 2a (Samsung) specs:**
- Read: ~100-200 MB/s
- Write: ~100-200 MB/s
- **Fast enough for everything!** ✅

**What this means:**
- ✅ Ollama model loading: ~1-2 seconds (same as SSD)
- ✅ Python imports: Instant
- ✅ Agent execution: No noticeable difference
- ✅ Git operations: Normal speed

**You won't notice any slowdown!**

---

## 🔄 Auto-Mounting (Optional)

If you want the drive to always mount to the same location:

1. Find UUID:
```bash
blkid | grep "Evo Plus"
```

2. Add to `/etc/fstab`:
```bash
sudo nano /etc/fstab
# Add line (replace UUID with yours):
UUID=your-uuid-here /media/squareyes/Evo\ Plus\ 2a exfat defaults 0 0
```

**Or just leave it as-is** - Linux usually handles this automatically.

---

## 📋 Quick Reference

**New Project Location:**
```bash
cd "/media/squareyes/Evo Plus 2a/AI_Projects/moon-dev-ai-agents-main"
```

**Activate Virtual Environment:**
```bash
source venv/bin/activate
```

**Run Agents:**
```bash
python src/agents/polymarket_agent.py
python src/agents/trading_agent.py
python src/agents/rbi_agent.py
```

**Check Ollama Models:**
```bash
ollama list
```

---

## ✅ Summary

**What You Gain:**
- 💾 **3.5+ GB free space** on laptop
- 📦 **Everything in one place** on external drive
- 🔄 **Easy to backup** (just copy the drive)
- 🚀 **Same performance** (fast external SSD)

**What Stays the Same:**
- ✅ All commands work exactly the same
- ✅ Git still works
- ✅ All agents run normally
- ✅ Ollama works transparently

---

**Ready to start the migration?** Just follow the steps in order! 🚀

Let me know when you finish each step, or if you hit any issues!
