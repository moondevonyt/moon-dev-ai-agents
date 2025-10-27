# HyperLiquid Testnet Setup - Paper Trading Guide

## 🧪 **What is Testnet?**

HyperLiquid testnet is a **test environment** with:
- ✅ **Fake money** (no real funds at risk)
- ✅ **Real trading logic** (same as mainnet)
- ✅ **Perfect for testing** your trading strategies
- ✅ **Free testnet funds** (request from faucet)

---

## ✅ **Configuration Complete!**

Your Trading Agent is now configured for HyperLiquid testnet!

**Changes made:**
1. `src/nice_funcs_hyperliquid.py` - Added `USE_TESTNET = True`
2. `src/agents/trading_agent.py` - Changed to `EXCHANGE = "HYPERLIQUID"`

---

## 🚀 **Quick Setup (5 Steps)**

### **Step 1: Get a HyperLiquid Wallet**

You need an Ethereum-style wallet (NOT Solana).

**Option A: Create New Wallet**
```python
# Run this in Python terminal
import eth_account

account = eth_account.Account.create()
print(f"Address: {account.address}")
print(f"Private Key: {account.key.hex()}")
# SAVE THIS PRIVATE KEY!
```

**Option B: Use Existing Ethereum Wallet**
- Export private key from MetaMask/other wallet
- Should start with `0x...`

---

### **Step 2: Add Private Key to `.env`**

Edit your `.env` file:

```bash
# Add this line (replace with your actual key)
HYPER_LIQUID_KEY=0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
```

⚠️ **This key is ONLY for testnet - safe to use for testing!**

---

### **Step 3: Get Testnet Funds**

**HyperLiquid Testnet Faucet:**
1. Go to: https://app.hyperliquid.xyz/testnet
2. Connect your wallet (use the address from Step 1)
3. Click "Request Testnet Funds" or use their Discord
4. You'll get **fake USDC** to trade with

**Alternative:** Ask in HyperLiquid Discord #testnet channel

---

### **Step 4: Verify Configuration**

Check that everything is set up:

```bash
cd ~/Desktop/APPS/AI\ AGENTS/moon-dev-ai-agents-main
source venv/bin/activate
python -c "
from src.nice_funcs_hyperliquid import USE_TESTNET, get_api_url
print(f'Testnet mode: {USE_TESTNET}')
print(f'API URL: {get_api_url()}')
"
```

Should show:
```
Testnet mode: True
🧪 Using HyperLiquid TESTNET (fake money)
API URL: https://api.hyperliquid-testnet.xyz
```

---

### **Step 5: Run the Trading Agent!**

```bash
cd ~/Desktop/APPS/AI\ AGENTS/moon-dev-ai-agents-main
source venv/bin/activate
python src/agents/trading_agent.py
```

---

## 📊 **What the Agent Will Do**

When you run it:

1. **Connects to HyperLiquid Testnet**
   ```
   🧪 Using HyperLiquid TESTNET (fake money)
   ```

2. **Checks your balance** (testnet USDC)

3. **Analyzes BTC** (currently configured token)

4. **Makes AI decision** using Ollama llama3.2:1b
   - BUY = Opens/maintains long position
   - SELL = Closes position
   - NOTHING = No action

5. **Executes trades** with fake money

6. **Repeats every 15 minutes**

---

## ⚙️ **Current Configuration**

| Setting | Value | What It Means |
|---------|-------|---------------|
| **Exchange** | HYPERLIQUID | HyperLiquid perps exchange |
| **Testnet** | TRUE | Using fake money ✅ |
| **AI Mode** | Single Model | Ollama llama3.2:1b |
| **Tokens** | BTC | Bitcoin only |
| **Position Size** | 90% of balance | Max per position |
| **Leverage** | 9x | Multiplier |
| **Long Only** | TRUE | Can't short |

---

## 🛠️ **Customization**

### **Change Which Tokens to Trade**

Edit `src/agents/trading_agent.py` (lines 174-178):

```python
SYMBOLS = [
    'BTC',      # Bitcoin - ACTIVE
    'ETH',      # Ethereum - Uncomment to enable
    'SOL',      # Solana - Uncomment to enable
]
```

### **Change Position Size**

Edit `src/agents/trading_agent.py` (line 119):

```python
MAX_POSITION_PERCENTAGE = 90  # Use 90% of balance
# Change to 50 for more conservative sizing
```

### **Change Leverage**

Edit `src/agents/trading_agent.py` (line 127):

```python
LEVERAGE = 9  # 9x leverage
# Change to 3 for less risk
```

### **Change AI Model**

Already using Ollama! But you can switch models:

```python
AI_MODEL_NAME = 'llama3.2:1b'  # Current (fast)
# OR
# AI_MODEL_NAME = 'llama3.2'   # More powerful
# AI_MODEL_NAME = 'deepseek-r1:7b'  # Best reasoning
```

---

## 🔄 **Switching Between Testnet and Mainnet**

### **To Use Mainnet (REAL MONEY):**

Edit `src/nice_funcs_hyperliquid.py` (line 44):

```python
USE_TESTNET = False  # ⚠️ REAL MONEY MODE!
```

**You'll need:**
- Real USDC on HyperLiquid mainnet
- Funded via Arbitrum bridge
- ⚠️ **Start with small amounts!**

---

## 📈 **What to Watch For**

When the agent runs, you'll see:

```
🧪 Using HyperLiquid TESTNET (fake money)
💰 Account Balance: $10,000 (testnet USDC)
📊 Analyzing BTC...
🤖 AI Decision: BUY
✅ Opening long position: $9,000 notional ($1,000 margin @ 9x)
⏰ Next run in 15 minutes...
```

---

## 🐛 **Troubleshooting**

**"Could not connect to Ollama"**
```bash
# Check Ollama is running
curl http://localhost:11434

# If not running
ollama serve
```

**"Could not connect to HyperLiquid"**
- Check your `.env` has `HYPER_LIQUID_KEY` set
- Verify key format starts with `0x...`
- Check internet connection

**"Insufficient balance"**
- Request testnet funds from faucet
- Go to https://app.hyperliquid.xyz/testnet
- Or ask in Discord #testnet channel

**"Module not found" errors**
```bash
# Install missing dependencies
cd ~/Desktop/APPS/AI\ AGENTS/moon-dev-ai-agents-main
source venv/bin/activate
pip install hyperliquid-python-sdk eth-account
```

---

## 💰 **Cost Breakdown**

| Component | Testnet | Mainnet |
|-----------|---------|---------|
| **AI (Ollama)** | $0.00 | $0.00 |
| **Trading Funds** | Fake (free) | Real money |
| **Gas Fees** | $0.00 | ~$0.10 per trade |
| **Exchange Fees** | $0.00 | 0.02% (taker) |

**Testnet Total: $0.00** ✅

---

## 🎯 **Testing Strategy**

### **Phase 1: Watch Mode** (First 1-2 hours)
- Let it run and observe decisions
- Check if AI reasoning makes sense
- See how it handles different market conditions

### **Phase 2: Single Token** (Current setup)
- Trading BTC only
- Monitor P&L
- Understand leverage impact

### **Phase 3: Multiple Tokens** (When confident)
- Add ETH, SOL to SYMBOLS list
- See how it manages multiple positions

### **Phase 4: Fine-Tuning**
- Adjust position sizes
- Change leverage
- Try different AI models

### **Phase 5: Live Trading** (When ready)
- Switch `USE_TESTNET = False`
- Start with very small amounts
- Scale up gradually

---

## ⚠️ **Important Safety Notes**

1. **Testnet is NOT mainnet** - Performance won't be exactly the same
2. **Test thoroughly** - Run for days/weeks before live trading
3. **Start small** - When going live, use tiny positions first
4. **Watch closely** - Monitor all trades, don't run blind
5. **Use stop losses** - Already configured at 5% loss
6. **Don't over-leverage** - 9x is aggressive, consider 3-5x

---

## 📚 **Resources**

- **HyperLiquid Testnet:** https://app.hyperliquid.xyz/testnet
- **HyperLiquid Docs:** https://hyperliquid.gitbook.io
- **HyperLiquid Discord:** Ask for testnet funds in #testnet
- **Trading Agent Config:** `src/agents/trading_agent.py` lines 83-178

---

## 🎉 **You're Ready!**

Your setup:
✅ Ollama running (free local AI)
✅ Trading Agent configured for HyperLiquid
✅ Testnet mode enabled (fake money)
✅ BTC trading configured
✅ All documentation ready

**Next step:**
```bash
python src/agents/trading_agent.py
```

Watch it trade with fake money and learn how it works! 🚀

---

**Built with ❤️ using 100% free tools!** 🌙

No API costs, safe testing environment, complete control.
