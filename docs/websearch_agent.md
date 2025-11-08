# Web Search Research Agent

**Created by Moon Dev**

The Web Search Research Agent is an autonomous AI system that searches the web for trading strategies, scrapes content, and extracts individual strategies into clean, backtest-ready markdown files.

## Overview

This agent creates a fully automated pipeline for strategy discovery:

```
AI Query Generation → Web Search → Content Scraping → Strategy Extraction → Clean Files
```

Each cycle produces multiple clean strategy files that can be directly fed into the RBI Agent for backtesting.

## Key Features

- **Automated Search Query Generation**: Uses GLM AI to create diverse, creative search queries
- **Web Search Integration**: OpenAI's web search API finds relevant trading content
- **Smart Content Scraping**: Converts HTML to markdown, handles various formats
- **Duplicate Detection**: Never processes the same URL twice
- **Strategy Extraction**: AI separates multi-strategy content into individual files
- **Clean Output**: Files contain only strategy name + description (no metadata)
- **Continuous Operation**: Runs 24/7, searching at configurable intervals
- **Heavy Logging**: All queries, results, and extractions logged to CSV

## Installation

### Prerequisites

```bash
# Required API keys in .env
OPENROUTER_API_KEY=your_key_here    # For GLM model
OPENAI_API_KEY=your_key_here        # For web search
```

### Dependencies

All required packages are in `requirements.txt`. The agent uses:
- `openai` - Web search API
- `requests` - API calls and web scraping
- `beautifulsoup4` - HTML parsing
- `termcolor` - Colored terminal output
- `pandas` - CSV logging

## Usage

### Basic Usage

Run continuous search loop (searches every 60 seconds):
```bash
python src/agents/websearch_agent.py
```

Run single search and exit:
```bash
python src/agents/websearch_agent.py --once
```

### Output Location

All outputs saved to: `src/data/web_search_research/`

Key folders:
- `final_strategies/` - **Clean strategy files ready for backtesting**
- `strategies/` - Raw scraped content (archived)
- `*.csv` - Logs of all queries, results, and extractions

## Configuration

**Location**: `src/agents/websearch_agent.py` (lines 52-86)

### Key Settings

```python
# Search Interval
SLEEP_BETWEEN_SEARCHES = 60  # Seconds between search cycles

# AI Models
GLM_MODEL = "z-ai/glm-4.6"                           # Query generation & extraction
OPENAI_WEB_SEARCH_MODEL = "gpt-4o-mini-search-preview"  # Web search
```

### Available GLM Models

```python
# Recommended (default)
GLM_MODEL = "z-ai/glm-4.6"
# Zhipu AI GLM-4.6 - Reasoning model, may need fallback handling

# Alternative (more reliable English)
GLM_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
# Meta Llama 3.3 70B - Solid English responses

# Alternative (fast and cheap)
GLM_MODEL = "deepseek/deepseek-chat"
# DeepSeek Chat - Fast inference
```

### Available Web Search Models

```python
# Recommended (default)
OPENAI_WEB_SEARCH_MODEL = "gpt-4o-mini-search-preview"
# Fast, cheap, good quality

# More powerful
OPENAI_WEB_SEARCH_MODEL = "gpt-4o-search-preview"
# Better results, higher cost

# Most powerful
OPENAI_WEB_SEARCH_MODEL = "gpt-5-search-api"
# GPT-5 search capabilities
```

## How It Works

### Pipeline Stages

#### 1. Query Generation
GLM AI generates creative search queries focusing on:
- Different strategy types (momentum, mean reversion, arbitrage, etc.)
- Various approaches (site filters, file types, academic sources)
- Diverse indicators and timeframes
- Backtest results and performance metrics

**Example queries**:
- "swing trading momentum strategy rules backtest results"
- "intraday volume profile trading system specific parameters"
- "statistical arbitrage pairs trading cryptocurrency backtest"

#### 2. Web Search
OpenAI's web search API:
- Searches with the generated query
- Returns 5-10 relevant URLs
- Includes title, snippet, and URL for each result

#### 3. Duplicate Detection
Before scraping, checks:
- `search_results.csv` for previously processed URLs
- Skips if URL already scraped
- Logs duplicate detection

#### 4. Content Scraping
For each new URL:
- Fetches HTML content
- Uses Beautiful Soup to extract text
- Converts to clean markdown
- Saves to `strategies/` folder
- Handles errors gracefully (timeouts, 404s, etc.)

#### 5. Strategy Extraction
GLM AI analyzes markdown content:
- Identifies distinct trading strategies
- Extracts each as a separate concept
- Creates individual markdown files
- Saves to `final_strategies/` folder

**Output format** (clean and simple):
```markdown
# Strategy Name

Full strategy description here...
```

### Reasoning Model Fallback

GLM-4.6 is a reasoning model that sometimes puts content in the `reasoning` field instead of `content` field. The agent handles this automatically:

```python
# Checks content field first
search_query = response['choices'][0]['message']['content']

# Falls back to reasoning field if content is empty
if not search_query:
    reasoning = response['choices'][0]['message']['reasoning']
    # Extract query from reasoning
```

**User sees**: "🔄 Content field empty, extracting from reasoning field..."

## Output Files

### search_queries.csv
All generated queries:
```csv
timestamp,model,search_query
2025-10-28 09:49:38,llama-3.3-70b,swing trading momentum strategy backtest results
```

### search_results.csv
All search results and processing status:
```csv
timestamp,search_query,url,title,content_preview,scraped,strategies_extracted
```

### strategies/ folder
Raw scraped content:
- `raw_YYYYMMDD_HHMMSS_[source].md`
- Original HTML converted to markdown
- May contain multiple strategies per file
- Archived for reference

### final_strategies/ folder
**THE IMPORTANT OUTPUT**

Clean individual strategy files:
- `extracted_YYYYMMDD_HHMMSS_NNN_[name].md`
- Format: Strategy name (header) + description
- No metadata, no timestamps, no author attribution
- **Ready to feed directly into RBI Agent**

### final_strategies_index.csv
Index of all extracted strategies:
```csv
timestamp,source_file,strategy_number,title,filename,source_url
```

## Integration with RBI Agent

The websearch agent is designed to work seamlessly with `rbi_agent_pp_multi.py`:

### Setup Instructions

1. **Run websearch agent** (generates strategy files):
```bash
python src/agents/websearch_agent.py
```

2. **Configure RBI agent** to read from `final_strategies/`:

Edit `src/agents/rbi_agent_pp_multi.py` (lines 102-103):
```python
STRATEGIES_FROM_FILES = True
STRATEGIES_FOLDER = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/web_search_research/final_strategies"
```

3. **Run RBI agent**:
```bash
python src/agents/rbi_agent_pp_multi.py
```

### The Complete Pipeline

```
Web Search Agent (continuous)
    ↓
Generates search queries every 60 seconds
    ↓
Finds trading strategies on the web
    ↓
Extracts clean strategy files
    ↓
Saves to final_strategies/ folder
    ↓
RBI Agent (continuous)
    ↓
Reads each .md file from folder
    ↓
Generates backtest code
    ↓
Tests on multiple timeframes/assets
    ↓
Logs results to backtest_stats.csv
```

**Result**: Fully automated strategy discovery, extraction, and backtesting!

## Prompts

The agent uses two carefully crafted prompts:

### Query Generation Prompt
Instructs GLM to:
- Generate ONE creative search query
- Focus on backtestable trading strategies
- Explore different strategy types
- Mix up approaches (site filters, file types, etc.)
- **Respond in English only** (emphatic warnings)

### Strategy Extraction Prompt
Instructs GLM to:
- Read trading content
- Extract EVERY distinct strategy
- Be aggressive in splitting strategies
- Return valid JSON format
- **All text in English** (emphatic warnings)

Both prompts have prominent warnings to prevent non-English responses from GLM.

## Performance & Costs

### Typical Cycle
- Query generation: 1-2 seconds, ~$0.001
- Web search: 2-5 seconds, ~$0.01-0.03
- Scraping: 1-2 seconds per page (free)
- Strategy extraction: 3-5 seconds per page, ~$0.005
- **Total per cycle**: 1-2 minutes, ~$0.02-0.05

### Output Rate
- Typical: 1-5 strategies per search cycle
- Good content: 5-10 strategies per cycle
- Running 24/7: 50-200 strategies per day
- Depends on search result quality

### Daily Costs
- 24 hours * 60 searches/hour = ~1,440 searches/day
- ~$0.03 per search = ~$43/day
- Can reduce by increasing `SLEEP_BETWEEN_SEARCHES`

## Troubleshooting

### "Empty or invalid response" Error

**Cause**: GLM puts content in `reasoning` field instead of `content` field

**Solution**: Automatic fallback is now implemented
- Agent checks reasoning field if content is empty
- Extracts query from reasoning
- Shows yellow warning message
- Continues processing normally

**If still occurring**: Switch to Llama model:
```python
GLM_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
```

### Chinese Text in Responses

**Cause**: GLM-4.6 is a Chinese-developed model

**Current solution**: Prompts have emphatic English-only warnings
- Multiple ⚠️ warnings in prompts
- "CRITICAL INSTRUCTION: YOU MUST RESPOND IN ENGLISH ONLY"
- Response requirement sections

**If persisting**: Switch to Llama model (see above)

### No Strategies Extracted

**Check**:
1. `search_results.csv` - Were pages scraped?
2. `strategies/` folder - Is content meaningful?
3. Error messages in terminal

**Common causes**:
- Content too short or generic
- Pages behind paywalls
- JavaScript-heavy sites (scraper can't execute JS)

**Fix**: Queries will naturally adjust over time as GLM learns

### Rate Limits

**OpenRouter**: Generous free tier for GLM models
- If hitting limits: Increase `SLEEP_BETWEEN_SEARCHES`

**OpenAI**: Standard rate limits apply
- Web search API has reasonable limits
- If hitting limits: Use slower model or increase interval

### Scraping Failures

**Common issues**:
- 403 Forbidden: Site blocking scrapers
- 404 Not Found: Dead links
- Timeout: Slow sites
- JavaScript required: Can't execute JS

**Handling**: Agent logs errors and continues to next URL

## Tips for Best Results

### Let It Run 24/7
- Diversity improves over time
- Different queries find different content
- More volume = better strategies

### Monitor Quality
Check `final_strategies/` periodically:
- Are strategies specific enough?
- Do they have clear rules?
- Are they backtestable?

### Adjust Configuration
- Try different GLM models
- Adjust search interval
- Change web search model for quality/cost trade-off

### Feed to RBI Agent
- Set up automated pipeline
- Let both agents run continuously
- Review `backtest_stats.csv` for results
- Find winning strategies automatically

### Clean Up Periodically
```bash
# Remove low-quality strategies manually
cd src/data/web_search_research/final_strategies/
# Review and delete vague or duplicate files

# RBI agent will skip processed strategies (tracked by hash)
```

## Advanced Features

### Custom Search Sources

Edit the query generation prompt to focus on specific sources:
```python
# Add to prompt:
"Focus on these sources: reddit.com/r/algotrading, tradingview.com, forexfactory.com"
```

### File Type Targeting

Modify queries to prefer certain formats:
```python
# Add to prompt:
"Prefer PDF documents with detailed strategy rules: filetype:pdf"
```

### Performance Tracking

Monitor extraction success rate:
```bash
# Count raw files
ls -1 src/data/web_search_research/strategies/ | wc -l

# Count extracted strategies
ls -1 src/data/web_search_research/final_strategies/ | wc -l

# Calculate extraction rate
```

## Data Management

### Storage Requirements
- Raw markdown: ~5-50 KB per file
- Final strategies: ~1-5 KB per file
- Running 24/7: ~500 MB per week
- CSV logs: ~10 MB per month

### Backup Recommendations
Backup these critical files:
- `final_strategies/` folder (the valuable output)
- `final_strategies_index.csv` (tracking)
- `search_queries.csv` (to see what's working)

### Reset/Cleanup
To start fresh:
```bash
cd src/data/web_search_research/
rm *.csv                    # Remove logs
rm -rf strategies/          # Remove raw content
rm -rf final_strategies/    # Remove extracted strategies
# Agent recreates everything on next run
```

## Architecture Notes

### Why GLM for Query Generation?
- Creative and diverse queries
- Understands trading concepts
- Free tier on OpenRouter
- Reasoning capabilities helpful

### Why OpenAI for Web Search?
- Best-in-class web search API
- Returns clean, structured results
- Fast and reliable
- No need to manage search engine APIs

### Why Two-Stage Extraction?
1. **Raw scraping**: Archives original content
2. **AI extraction**: Separates and cleans strategies

Benefits:
- Can reprocess raw files later
- Improves extraction without re-scraping
- Audit trail of sources

### Thread Safety
Currently single-threaded, but designed for parallelization:
- Each search cycle is independent
- No shared state between cycles
- Could add threading for concurrent processing

## Future Enhancements

Possible improvements:
- **Parallel scraping**: Process multiple URLs concurrently
- **Quality scoring**: Rate strategy quality before saving
- **Deduplication**: Detect similar strategies across different sources
- **Category tagging**: Auto-tag strategies by type
- **Performance tracking**: Track which sources produce best strategies

## Notes

- **No fake data**: Only real content from web
- **Heavy logging**: Everything tracked in CSV files
- **Fault tolerant**: Continues on errors
- **Duplicate prevention**: Never reprocesses URLs
- **Clean output**: Files ready for immediate use
- **Integration ready**: Designed to feed RBI Agent

---

**Made with ❤️ by Moon Dev**

*Part of the Moon Dev AI Agents for Trading project*

**Related Documentation**:
- [RBI Agent](rbi_agent.md) - Backtest the extracted strategies
- [OpenRouter](openrouter.md) - GLM model configuration
