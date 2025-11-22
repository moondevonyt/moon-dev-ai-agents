# Scraper Agent

**Built by Moon Dev** 🌙

## What It Does

Scrapes websites and analyzes them using AI swarms. Handles JavaScript-rendered sites (Next.js, React, Vue, etc.) using Selenium headless browser.

## Key Features

- **Batch Processing** - Enter multiple URLs at once (space-separated)
- **Prompt Override** - Add custom prompt after URLs for specific analysis
- **Parallel Execution** - All URLs scrape simultaneously
- **JavaScript Support** - Selenium headless browser renders JS before scraping
- **SwarmAgent Integration** - Multiple AI models analyze in parallel
- **Human-Readable Output** - TXT files with metadata + AI responses
- **Debug Mode** - Raw scraped content saved separately

## Requirements

```bash
pip install selenium
brew install chromedriver  # macOS
```

For Windows/Linux: Download ChromeDriver from https://chromedriver.chromium.org/

## Usage

```bash
python src/agents/scraper_agent.py
```

### Default Prompt
Enter URLs only - uses default prompt:
```
🌙 Enter URLs > https://site1.com https://site2.com https://site3.com
```

### Custom Prompt Override
Add your question after the URLs:
```
🌙 Enter URLs > https://site1.com https://site2.com what are their pricing models

🔴 CUSTOM PROMPT: what are their pricing models
```

Everything after the last URL becomes the custom prompt!

## How It Works

The agent parses your input intelligently:
- **URLs** have `.` in them (like `.com`, `.ai`)
- **Everything after the last URL** = custom prompt
- If no text after URLs = uses default prompt

**Examples:**
```bash
# Default prompt
anthropic.com openai.com

# Custom prompt
anthropic.com openai.com tell me about their API pricing

# Another custom prompt
site1.com site2.com site3.com compare their features
```

## Output Files

Each URL generates 3 files in `src/data/scraper_agent/`:

```
src/data/scraper_agent/
├── raw_scrapes/
│   └── site1_com_20250119_143022.txt    # Raw scraped content (debug)
├── site1_com_20250119_143022.txt         # Human readable (metadata + AI)
└── site1_com_20250119_143022.json        # Full data (structured)
```

### Human-Readable TXT Format:
```
URL: https://site1.com
Timestamp: 2025-01-19T14:30:22

METADATA:
Title: [Site Title]
Description: [Site Description]
Keywords: [Site Keywords]

AI ANALYSIS:
🧠 AI CONSENSUS: [3-sentence summary from swarm]
📋 INDIVIDUAL RESPONSES: [Full responses from each AI model]
```

## Configuration

Edit `src/agents/scraper_agent.py` top section:

```python
# Use SwarmAgent (True) or XAI model only (False)
USE_SWARM = True

# XAI model to use when swarm is disabled
XAI_MODEL = "grok-4-fast-reasoning"

# Default analysis prompt
DEFAULT_PROMPT = """Give me two sentences and ten bullet points about what this website is about."""

# Request timeout (seconds)
REQUEST_TIMEOUT = 30
```

## Why Selenium?

BeautifulSoup can't handle JavaScript-rendered sites. Modern sites (Next.js, React) render content client-side, so you get "Loading..." with basic HTTP requests.

Selenium launches a real headless browser, executes JavaScript, waits for content to render, then extracts the full page.

## Examples

**Single URL with default prompt:**
```
🌙 Enter URLs > anthropic.com
📝 Using default prompt
```

**Multiple URLs with default prompt:**
```
🌙 Enter URLs > anthropic.com openai.com deepseek.com
📝 Using default prompt
```

**Custom prompt:**
```
🌙 Enter URLs > anthropic.com openai.com what are their API rate limits
🔴 CUSTOM PROMPT: what are their API rate limits
```

**Another custom prompt:**
```
🌙 Enter URLs > site1.com site2.com compare their security features
🔴 CUSTOM PROMPT: compare their security features
```

**Exit:**
```
🌙 Enter URLs > quit
```

---

**Moon Dev's Scraper Agent** - Scrape any site, ask anything! 🚀
