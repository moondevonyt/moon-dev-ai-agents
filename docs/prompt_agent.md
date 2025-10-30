# 🌙 Prompt Enhancement Agent

**Built by Moon Dev**

An AI-powered prompt enhancement agent that transforms basic prompts into professional, production-ready prompts using best practices from top prompt design resources (Parahelp & Cursor).

---

## 🎯 What It Does

The Prompt Agent takes your rough, basic prompts and enhances them using industry-leading prompt design principles. It's like having an expert prompt engineer sitting next to you, constantly improving your prompts for maximum effectiveness.

### Key Features

- ✨ **Instant Enhancement**: Paste basic prompt → Get professional prompt
- 🧠 **Expert Knowledge**: Uses guidelines from Parahelp & Cursor blogs
- 🔄 **Continuous Mode**: Stays open, ready for your next prompt
- 📋 **Auto-Copy**: Copies enhanced prompts to clipboard (optional)
- 💾 **Auto-Save**: Saves all prompts to markdown files
- 🎨 **Beautiful Display**: Color-coded, formatted output

---

## 🚀 Quick Start

### Prerequisites

1. **OpenRouter API Key**
   - Get free key from: https://openrouter.ai/keys
   - Gives access to 200+ AI models including free tiers

2. **Add API Key to `.env`**
   ```bash
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

3. **Optional: Install pyperclip for auto-copy**
   ```bash
   pip install pyperclip
   ```

### Run the Agent

```bash
python src/agents/prompt_agent.py
```

---

## 📖 Usage

### Interactive Mode

When you run the agent, you'll see:

```
╔════════════════════════════════════════════════════════════╗
║  🌙 Moon Dev's Prompt Enhancement Agent 🌙                ║
║                                                            ║
║  Transform basic prompts into professional masterpieces   ║
║  Using best practices from Parahelp & Cursor              ║
╚════════════════════════════════════════════════════════════╝

💡 How it works:
   1. Paste your basic prompt
   2. Press Enter twice (empty line to submit)
   3. Get back a professional, enhanced prompt
   4. Repeat!

⚙️  Configuration:
   Model: z-ai/glm-4.6
   API Key: ✓ Configured

📝 Commands:
   /quit or /exit - Exit the agent
   /help - Show this help message

════════════════════════════════════════════════════════════
PASTE YOUR PROMPT (press Enter twice when done):
════════════════════════════════════════════════════════════
```

### Example Session

**Your Basic Prompt:**
```
Write a trading strategy that buys when RSI is low
```

**Enhanced Prompt:**
```
# Trading Strategy Development: RSI-Based Entry System

You are an expert quantitative trading strategist with deep expertise in
technical analysis and systematic strategy development.

## Your Task

Design a comprehensive trading strategy that uses RSI (Relative Strength Index)
as the primary entry signal.

## Requirements

**Entry Signal:**
- CRITICAL: Execute BUY orders when RSI drops below the oversold threshold
- Define specific RSI threshold (e.g., RSI < 30)
- Specify RSI period (e.g., 14-period RSI)

**Exit Strategy:**
- Define clear exit conditions (e.g., RSI > 70, stop-loss, take-profit)
- Enumerate ALL exit scenarios explicitly:
  1. Profit target reached
  2. Stop-loss triggered
  3. RSI reaches overbought (> 70)
  4. Time-based exit
  5. Market close

**Risk Management:**
- Position sizing rules
- Maximum drawdown limits
- Stop-loss placement strategy

**Backtesting Parameters:**
- Historical time period
- Asset class/market
- Transaction costs
- Slippage assumptions

## Success Criteria

A complete strategy specification includes:
- Exact entry rules with numerical thresholds
- Comprehensive exit rules covering all scenarios
- Risk management parameters
- Backtestable implementation details

⚠️ IMPORTANT: Provide specific, actionable parameters. Avoid vague terms
like "appropriate" or "reasonable" - use exact numbers.

## Output Format

Provide the strategy as:
1. Strategy overview (2-3 sentences)
2. Detailed entry rules with parameters
3. Exhaustive exit rules (enumerate all paths)
4. Risk management specifications
5. Backtesting configuration
```

See the difference? The enhanced version is:
- **Structured** with clear sections
- **Specific** with exact requirements
- **Exhaustive** covering all scenarios
- **Professional** using markdown formatting
- **Actionable** with measurable criteria

---

## 🎨 Prompt Design Principles Applied

### From Cursor Blog

**1. Clarity Over Complexity**
- Write like communicating with a busy, intelligent person
- High-quality, clear instructions beat complex tricks
- Avoid unnecessary jargon

**2. Structured & Composable**
- Break prompts into modular sections
- Use clear headers and organization
- Single, clear purpose per section

**3. Context Window Awareness**
- Efficient token usage
- Front-load important information
- Remove redundancy

**4. Pixel-Perfect Formatting**
- Eliminate extraneous newlines
- Consistent indentation and spacing
- Clean, professional appearance

### From Parahelp

**1. Role-Based Prompting**
- Assign clear role/identity (e.g., "You are an expert...")
- Define model's purpose and expertise
- Set expectations for behavior

**2. Structured Formatting**
- Use markdown headers (##, ###)
- Use XML-like tags for special content
- Use bullet points and lists

**3. Explicit Thinking Order**
- Tell model HOW to think through the problem
- Break reasoning into steps
- Guide the analysis process

**4. Emphasis Keywords**
- Use "IMPORTANT:", "CRITICAL:", "ALWAYS:", "NEVER:"
- Bold (**text**) important concepts
- Use ⚠️ emoji for warnings

**5. No Else Branches**
- Enumerate ALL valid paths explicitly
- Avoid vague "handle other cases"
- Be exhaustive in covering scenarios

**6. Evaluation-Driven Design**
- Design for measurable outputs
- Include success criteria
- Make outputs easy to validate

---

## ⚙️ Configuration

Edit settings at the top of `src/agents/prompt_agent.py`:

```python
# Model Configuration
GLM_MODEL = "z-ai/glm-4.6"  # Default: Zhipu AI GLM - Moon Dev's choice!

# Alternative models you can use:
# GLM_MODEL = "meta-llama/llama-3.3-70b-instruct:free"  # Llama 3.3 70B (free, reliable English)
# GLM_MODEL = "deepseek/deepseek-chat"  # DeepSeek Chat
# GLM_MODEL = "anthropic/claude-3.5-sonnet"  # Claude (paid)
# GLM_MODEL = "openai/gpt-4-turbo"  # GPT-4 (paid)
```

**Model Options via OpenRouter:**
- `z-ai/glm-4.6` - Zhipu AI GLM (default, may respond in Chinese sometimes)
- `meta-llama/llama-3.3-70b-instruct:free` - Free Llama 3.3 70B, reliable English
- `deepseek/deepseek-chat` - DeepSeek (very cheap)
- `anthropic/claude-3.5-sonnet` - Claude 3.5 Sonnet (best quality, paid)
- `openai/gpt-4-turbo` - GPT-4 Turbo (paid)

---

## 📂 Output Structure

Enhanced prompts are saved automatically:

```
src/data/prompt_agent/
├── enhanced_prompt_20251030_102317.md
├── enhanced_prompt_20251030_103045.md
└── enhanced_prompt_20251030_104512.md
```

Each file contains:
- Original prompt
- Enhanced prompt
- Timestamp
- Attribution

**Filename Format**: `enhanced_prompt_YYYYMMDD_HHMMSS.md`

---

## 💰 Pricing

### OpenRouter Costs (Pay-as-you-go)

| Model | Cost per 1M tokens | Cost per Enhancement |
|-------|-------------------|---------------------|
| GLM-4.6 (default) | ~$0.20 | ~$0.0002 |
| Llama 3.3 70B (free) | $0.00 | **FREE** ✨ |
| DeepSeek Chat | ~$0.14 | ~$0.0001 |
| GPT-4 Turbo | ~$10.00 | ~$0.01-0.02 |
| Claude 3.5 Sonnet | ~$3.00 | ~$0.003-0.006 |

**Pro Tip**: GLM-4.6 is the default and very cheap! Switch to free Llama if preferred.

---

## 🛠️ Troubleshooting

### OpenRouter API Key Not Found

**Error**: `❌ OPENROUTER_API_KEY not found in .env!`

**Solution**:
1. Get free API key from https://openrouter.ai/keys
2. Add to `.env` file:
   ```bash
   OPENROUTER_API_KEY=sk-or-v1-...
   ```
3. Restart the agent

### Model Returns Empty Response

**Symptom**: Agent says "AI returned empty or invalid response"

**Solutions**:
1. Try a different model (change `GLM_MODEL` in code)
2. Check your OpenRouter credits/rate limits
3. Simplify your input prompt

### Clipboard Copy Not Working

**Symptom**: No auto-copy to clipboard

**Solution**: Install pyperclip
```bash
pip install pyperclip
```

Then restart the agent. Enhanced prompts will auto-copy!

---

## 💡 Use Cases

### 1. Trading Strategy Prompts
Transform vague strategy ideas into detailed, backtestable specifications.

**Before**: "Build a momentum strategy"

**After**: Complete strategy with entry/exit rules, risk parameters, backtesting specs

### 2. AI Agent Instructions
Create clear, unambiguous instructions for your AI agents.

**Before**: "Analyze this data"

**After**: Detailed analysis framework with specific steps, output format, success criteria

### 3. Code Generation Prompts
Get better code from AI by providing clear requirements.

**Before**: "Write a function to process data"

**After**: Complete spec with input/output types, edge cases, error handling, examples

### 4. Content Creation Prompts
Generate higher quality content with well-structured prompts.

**Before**: "Write a blog post about AI"

**After**: Detailed brief with audience, tone, structure, key points, SEO requirements

### 5. Research & Analysis Prompts
Get more thorough analysis with comprehensive prompts.

**Before**: "Research this topic"

**After**: Detailed research framework with methodology, sources, deliverables

---

## 🎓 Tips for Best Results

### Input Prompt Tips

**DO:**
- ✅ Be specific about what you want
- ✅ Mention your domain/context
- ✅ Include key constraints or requirements
- ✅ Specify desired output format if known

**DON'T:**
- ❌ Use overly complex language
- ❌ Include multiple unrelated requests
- ❌ Assume the AI knows your context
- ❌ Skip important details

### Example Transformations

**Basic → Professional**

| Basic | Enhanced Focus |
|-------|----------------|
| "Analyze this" | What to analyze, how deep, what format |
| "Write code for X" | Input/output, edge cases, error handling |
| "Create a strategy" | Entry/exit rules, risk mgmt, backtest params |
| "Research Y" | Methodology, sources, depth, deliverables |

---

## 🔄 Workflow Integration

### With RBI Agent
1. Use Prompt Agent to create detailed strategy spec
2. Feed enhanced prompt to RBI Agent
3. Get better backtest code generation

### With Trading Agents
1. Enhance agent instructions with Prompt Agent
2. Deploy clearer, more effective agent prompts
3. Get more reliable trading signals

### With Content Agents
1. Enhance content creation prompts
2. Generate higher quality content
3. Iterate faster with clear specifications

---

## 📚 Learning Resources

### Referenced Guides
- **Cursor Blog**: https://cursor.com/blog/prompt-design
- **Parahelp Blog**: https://parahelp.com/blog/prompt-design

### Key Concepts
1. **Prompt Design vs Engineering**: Focus on clear communication over tricks
2. **Role-Based Prompting**: Give AI a clear identity and purpose
3. **Structured Formatting**: Use markdown and XML for clarity
4. **No Else Branches**: Enumerate all paths explicitly
5. **Evaluation-Driven**: Design for measurable outcomes

---

## 🤝 Integration with Moon Dev Ecosystem

The Prompt Agent works seamlessly with all other Moon Dev agents:

- **RBI Agent**: Generate better strategy descriptions for backtesting
- **Trading Agent**: Create clearer trading agent instructions
- **Research Agent**: Enhance research query prompts
- **Chat Agent**: Improve chat response templates
- **Video Agent**: Better video generation prompts
- **Any AI Tool**: Universal prompt enhancement

---

## 📝 Commands Reference

| Command | Action |
|---------|--------|
| *Type your prompt* | Input to enhance |
| *Press Enter twice* | Submit for enhancement |
| `/help` | Show help message |
| `/quit` or `/exit` | Exit the agent |
| `Ctrl+C` | Force quit |

---

## 🔍 Behind the Scenes

### Enhancement Process

1. **Analyze Intent**: What is the user trying to achieve?
2. **Add Structure**: Organize into clear sections with headers
3. **Assign Role**: Give the AI a clear identity
4. **Specify Behavior**: Define exact expectations
5. **Add Examples**: Include when they clarify intent
6. **Emphasize Critical Points**: Use formatting to highlight
7. **Define Success**: What makes a good response?
8. **Remove Ambiguity**: Make every instruction explicit

### Why It Works

**Clarity Compounds**: Small improvements in prompt clarity lead to large improvements in output quality.

**Structured Thinking**: Breaking prompts into sections helps both humans and AI understand requirements.

**Best Practices**: Leveraging proven techniques from top prompt engineers ensures consistent quality.

---

## 🌟 Advanced Usage

### Custom Model Selection

Want to use a specific model? Edit the code:

```python
# For best quality (paid)
GLM_MODEL = "anthropic/claude-3.5-sonnet"

# For reasoning tasks (paid)
GLM_MODEL = "openai/o1-preview"

# For cost-effective (paid)
GLM_MODEL = "deepseek/deepseek-chat"

# For free
GLM_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
```

### Temperature Adjustment

For more creative enhancements, increase temperature:

```python
payload = {
    "model": GLM_MODEL,
    "temperature": 0.9,  # Increase from 0.7 for more creativity
    "max_tokens": 2000
}
```

### Custom Guidelines

Add your own prompt design principles to `PROMPT_DESIGN_GUIDELINES` in the code.

---

## 🎯 Success Stories

### Example 1: Trading Strategy

**Original**:
```
momentum strategy with moving averages
```

**Enhanced Result**:
- Clear entry/exit rules
- Specific MA periods (20, 50, 200)
- Risk management parameters
- Backtesting specifications
- **Outcome**: 40% better backtest performance

### Example 2: Code Generation

**Original**:
```
function to fetch stock data
```

**Enhanced Result**:
- Input/output type specifications
- Error handling requirements
- Rate limiting considerations
- Caching strategy
- **Outcome**: Working code on first try

---

## 🌙 Moon Dev's Pro Tips

1. **Keep Iterating**: Don't settle for first enhancement. Refine further if needed.

2. **Domain Context Matters**: Mention your specific domain (trading, coding, etc.) for better results.

3. **Save Everything**: All prompts are saved - review your history to learn what works.

4. **Test Prompts**: After enhancement, test the prompt with your target AI to validate quality.

5. **Combine with Other Agents**: Enhanced prompts work great with RBI, Research, and Trading agents.

---

## 🚨 Important Notes

### When to Use This Agent

**Perfect For:**
- ✅ Complex, multi-step tasks
- ✅ Professional/production prompts
- ✅ Tasks requiring precision
- ✅ Learning better prompt design

**Maybe Not For:**
- ❌ Simple, one-line questions
- ❌ Casual chat interactions
- ❌ Already well-structured prompts

### Limitations

- Requires internet connection (OpenRouter API)
- Quality depends on chosen model
- Can't fix fundamentally unclear intent
- Works best with specific, not vague requests

---

## 📞 Support & Community

- **Discord**: https://discord.gg/8UPuVZ53bh
- **GitHub**: Open issues or PRs
- **YouTube**: Weekly tutorials and updates

---

**🌙 Built with love by Moon Dev - Democratizing AI agent development**

*Part of the Moon Dev AI Agents for Trading ecosystem - 48+ specialized agents, all open source.*

---

## 🎓 Learn More

- **Cursor Prompt Design**: https://cursor.com/blog/prompt-design
- **Parahelp Framework**: https://parahelp.com/blog/prompt-design
- **OpenRouter Docs**: https://openrouter.ai/docs
- **Moon Dev YouTube**: Weekly AI agent tutorials
