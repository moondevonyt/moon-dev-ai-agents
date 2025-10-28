# Jupiter Solana Devnet Setup Guide

## 🌟 **What is Jupiter on Solana Devnet?**

Jupiter is Solana's leading DEX aggregator. The **devnet** version lets you:
- ✅ Trade with **fake SOL** (completely free)
- ✅ Test strategies **risk-free**
- ✅ Use real Jupiter interface (devnet version)
- ✅ Get unlimited testnet funds from faucet

**Perfect alternative to HyperLiquid testnet!**

---

## 🚀 **Quick Setup (4 Steps)**

### **Step 1: Create Solana Wallet**

You need a Solana wallet (NOT Ethereum like HyperLiquid).

**Option A: Use Phantom Wallet (Easiest)**
1. Install Phantom browser extension: https://phantom.app
2. Create new wallet
3. Switch to **Devnet** in settings:
   - Click gear icon → Change Network → Devnet
4. Copy your wallet address (starts with letters/numbers, ~44 characters)

**Option B: Generate CLI Wallet**
```bash
# Install Solana CLI (if not already installed)
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"

# Generate new keypair
solana-keygen new --outfile ~/solana-devnet-wallet.json

# Get your address
solana address -k ~/solana-devnet-wallet.json

# Export private key (base58 format)
cat ~/solana-devnet-wallet.json
# Copy the array of numbers - this is your private key
```

---

### **Step 2: Get FREE Devnet SOL**

**Solana Devnet Faucet** (gives you 1-5 SOL instantly):

```bash
# Option 1: CLI (fastest)
solana airdrop 2 YOUR_WALLET_ADDRESS --url devnet

# Option 2: Web Faucet
# Go to: https://faucet.solana.com
# Paste your wallet address
# Request 2 SOL
```

**You can request multiple times!** Each airdrop gives 1-5 SOL (worth $0 - it's fake)

**Verify you received funds:**
```bash
solana balance YOUR_WALLET_ADDRESS --url devnet
```

---

### **Step 3: Add Private Key to `.env`**

Your `.env` file needs the Solana private key in **base58 format**.

**If using Phantom:**
1. Phantom → Settings → Show Private Key
2. Copy the private key (base58 string)

**If using CLI wallet:**
```bash
# Your keypair file contains an array of numbers
# Example: [123, 45, 67, ...]
# You need to convert this to base58

# Option 1: Use Phantom to import and export
# - Import your JSON keypair into Phantom
# - Export as base58 private key

# Option 2: Use Python (already in your environment)
python3 << 'EOF'
import json
import base58

# Read your keypair file
with open('/path/to/your/solana-devnet-wallet.json', 'r') as f:
    keypair = json.load(f)

# Convert to base58
private_key = base58.b58encode(bytes(keypair)).decode('utf-8')
print(f"Base58 Private Key:\n{private_key}")
EOF
```

**Add to `.env`:**
```bash
SOLANA_PRIVATE_KEY=your_base58_private_key_here
```

---

### **Step 4: Configure Trading Agent for Solana Devnet**

Edit `src/agents/trading_agent.py`:

```python
# Line 84: Change exchange to SOLANA
EXCHANGE = "SOLANA"  # Was "HYPERLIQUID"

# Line 93: Keep paper trading OFF to use real devnet
PAPER_TRADING_MODE = False  # Set to False for real devnet trading

# Line 109: Keep swarm mode enabled
USE_SWARM_MODE = True  # 4-model consensus
```

**Also need to configure Solana RPC endpoint** in `.env`:
```bash
# Use public devnet RPC (free)
RPC_ENDPOINT=https://api.devnet.solana.com

# OR use Helius devnet (faster, also free)
RPC_ENDPOINT=https://devnet.helius-rpc.com/?api-key=YOUR_HELIUS_KEY
```

---

## 🎯 **What Tokens to Trade?**

On Solana devnet, you need to use **devnet token addresses** (different from mainnet).

Common devnet tokens:
```python
# In trading_agent.py, line ~169
MONITORED_TOKENS = [
    'So11111111111111111111111111111111111111112',  # Wrapped SOL (devnet)
    # Add other devnet token addresses here
]
```

**Finding devnet tokens:**
- Solana Explorer (devnet): https://explorer.solana.com/?cluster=devnet
- Look for "Token Program" accounts
- Most popular tokens have devnet versions

---

## ▶️ **Run the Trading Agent**

```bash
# Make sure Ollama is running
ollama serve &

# Run the trading agent
python src/agents/trading_agent.py
```

**What you'll see:**
```
🌙 Moon Dev AI Trading System Starting Up! 🚀
🌊 Initializing Trading Agent in SWARM MODE (4 FREE local AI consensus)...
✅ Swarm mode initialized with 4 FREE Ollama models!
🏦 Using SOLANA - Trading tokens: [...]
📊 Collecting market data...
🌊 Analyzing token... with SWARM (4 FREE local AI models voting)
💡 AI #1 (deepseek-r1:7b): BUY
💡 AI #2 (qwen2.5:7b): BUY
💡 AI #3 (llama3.2:latest): BUY
💡 AI #4 (llama3.2:1b): NOTHING
📊 Consensus: BUY (75% confidence)
✅ Executing trade on Solana devnet...
```

---

## 🔄 **Switching Between Devnet and Mainnet**

### **Devnet (Fake Money - Safe)**
```python
# trading_agent.py
EXCHANGE = "SOLANA"
PAPER_TRADING_MODE = False

# .env
RPC_ENDPOINT=https://api.devnet.solana.com
SOLANA_PRIVATE_KEY=your_devnet_wallet_key
```

### **Mainnet (REAL Money - Dangerous!)**
```python
# trading_agent.py
EXCHANGE = "SOLANA"
PAPER_TRADING_MODE = False  # ⚠️ REAL MONEY!

# .env
RPC_ENDPOINT=https://api.mainnet-beta.solana.com  # or Helius mainnet
SOLANA_PRIVATE_KEY=your_mainnet_wallet_key  # ⚠️ Use different wallet!
```

**⚠️ NEVER use your devnet wallet on mainnet - create a separate wallet!**

---

## 📊 **Paper Trading vs Devnet vs Mainnet**

| Mode | Money | AI Analysis | Trades | Best For |
|------|-------|-------------|--------|----------|
| **Paper Trading** | Fake ($10k) | ✅ Real | ❌ Simulated | Testing AI logic |
| **Solana Devnet** | Fake (free SOL) | ✅ Real | ✅ Real (on devnet) | Testing full system |
| **Solana Mainnet** | Real ($$) | ✅ Real | ✅ Real | Live trading |

**Recommendation:**
1. Start with **Paper Trading** (current setup) → Test AI decisions
2. Move to **Solana Devnet** (tomorrow) → Test full trading flow
3. Only go **Mainnet** after weeks of testing with tiny amounts

---

## 🐛 **Troubleshooting**

**"Insufficient SOL balance"**
```bash
# Get more devnet SOL
solana airdrop 5 YOUR_ADDRESS --url devnet
```

**"Transaction failed"**
- Devnet can be unstable - retry a few times
- Switch RPC endpoints if one is slow
- Check Solana status: https://status.solana.com

**"Invalid private key format"**
- Solana needs base58 format, NOT hex or array
- Use Phantom export or Python conversion script above

**"No market data"**
- Devnet tokens have less liquidity
- Some tokens may not exist on devnet
- Try wrapped SOL first (most reliable)

---

## 💰 **Cost Comparison**

| Component | Paper Mode | Devnet | Mainnet |
|-----------|------------|--------|---------|
| AI (Ollama) | $0.00 | $0.00 | $0.00 |
| Trading Funds | Fake | Free (faucet) | Real $ |
| Transaction Fees | $0.00 | $0.00 | ~$0.0001-0.01 per trade |
| Total | **$0.00** | **$0.00** | **$$** |

---

## 🎯 **Tomorrow's Setup Plan**

1. ✅ **Paper Trading** (done today!)
   - Test 4-model consensus
   - See AI decisions
   - Verify swarm works

2. 📅 **Tomorrow: Solana Devnet**
   - Create/import Solana wallet
   - Get devnet SOL from faucet
   - Configure trading agent for devnet
   - Test real trades with fake money

3. 🔮 **Future: Mainnet** (only after extensive testing)
   - Start with $10-50 ONLY
   - Monitor closely for weeks
   - Scale up gradually

---

## 📚 **Resources**

- **Solana Devnet Faucet**: https://faucet.solana.com
- **Solana Devnet Explorer**: https://explorer.solana.com/?cluster=devnet
- **Jupiter Docs**: https://docs.jup.ag
- **Phantom Wallet**: https://phantom.app
- **Solana CLI Docs**: https://docs.solana.com/cli

---

## ✅ **Ready for Tomorrow!**

**Tonight you can:**
1. ✅ Test paper trading mode
2. ✅ See 4-model consensus in action
3. ✅ Verify Ollama models working

**Tomorrow we'll:**
1. Set up Solana devnet wallet
2. Get free testnet SOL
3. Run real trades on devnet with fake money
4. Watch the full system work end-to-end!

Sleep well! 🌙

---

**Built with ❤️ using 100% free tools!**

No API costs, safe testing, complete control.
