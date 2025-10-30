# 🚀 RESEARCH AGENT V2.0 - COMPLETE OVERHAUL DESIGN

## 📋 Executive Summary

Research Agent v2.0 wird ein **Deep-Research-System** mit **Multi-Source Intelligence**, das kontinuierlich die neuesten Krypto-Trends, Strategien und "Hype"-Themen identifiziert und automatisch in `ideas.txt` schreibt.

**Budget:** Minimal (Free-Tiers, Open-Source, Self-Hosted)
**Ziel:** Beste Trading-Ideen in Echtzeit finden
**Output:** 1-3 Top-Ideen pro Stunde in `ideas.txt`

---

## 🎯 Current vs. Future State

### **AKTUELL (v1.0):**
```
✅ MCP deep-research (Tavily API)
✅ Token-optimiert (500 chars max)
✅ Strategy Type Rotation
✅ Duplicate Detection
❌ NUR Web-Search (limitiert)
❌ Keine Social Media
❌ Keine On-Chain Daten
❌ Keine Code Repos
❌ Keine Foren
❌ Kein Twitter Integration
```

### **ZIEL (v2.0):**
```
✅ Multi-Source Intelligence
   ├── 🔍 Meta-Search (SearXNG/Swirl)
   ├── 💬 Social Media (Twitter, Reddit, Discord, Telegram)
   ├── 📊 On-Chain (DexScreener, DefiLlama, Dune)
   ├── 💻 Code Repos (GitHub trending, arXiv papers)
   ├── 🌐 Foren (Bitcointalk, Reddit, Discord)
   └── 📰 News Feeds (RSS, Crypto News APIs)

✅ Intelligent Processing Pipeline
   ├── Relevanz-Filter
   ├── Duplikat-Erkennung (Embeddings)
   ├── KI-Zusammenfassung (GPT-3.5 / Local LLM)
   ├── Sentiment-Analyse
   ├── Trend-Scoring
   └── Priorisierung

✅ Cost Optimization
   ├── Self-Hosted Tools
   ├── Free-Tier Rotation
   ├── Local LLMs für Summaries
   └── Token-Minimierung
```

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RESEARCH AGENT V2.0                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              DATA COLLECTION LAYER (Parallel)                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Web Search   │  │ Social Media │  │  On-Chain    │     │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤     │
│  │ • SearXNG    │  │ • Twitter/X  │  │ • DexScreener│     │
│  │ • Swirl      │  │ • Reddit     │  │ • DefiLlama  │     │
│  │ • Google CSE │  │ • Discord    │  │ • Dune       │     │
│  │ • Bing       │  │ • Telegram   │  │ • Etherscan  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Code Repos   │  │    Forums    │  │  News Feeds  │     │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤     │
│  │ • GitHub     │  │ • Bitcointalk│  │ • RSS Feeds  │     │
│  │ • arXiv      │  │ • Discord    │  │ • Crypto News│     │
│  │ • Google     │  │ • Reddit     │  │ • CoinDesk   │     │
│  │   Scholar    │  │   Crypto     │  │ • CoinTelegraph│   │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              PROCESSING PIPELINE (Sequential)                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. 🔍 COLLECTION → Raw data from all sources                │
│  2. 🧹 CLEANING → Remove ads, spam, duplicates               │
│  3. 📊 FILTERING → Relevance scoring, keyword matching       │
│  4. 🤖 SUMMARIZATION → LLM summaries of each source          │
│  5. 🎯 DEDUPLICATION → Semantic similarity (embeddings)      │
│  6. 📈 SCORING → Trend score, buzz score, novelty score     │
│  7. 🏆 RANKING → Top 3 ideas by combined score               │
│  8. 💾 OUTPUT → Write to ideas.txt + knowledge base          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     OUTPUT LAYER                             │
├─────────────────────────────────────────────────────────────┤
│  • ideas.txt (Top 1-3 ideas für RBI Agent)                  │
│  • strategy_ideas.csv (Alle Ideen + Metadata)               │
│  • knowledge_base.json (Historische Trends)                 │
│  • trending_topics.json (Aktuelle Trends)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔌 Data Sources - Implementation Details

### **1. Web Search (Meta-Search)**

**Primary:** SearXNG (Self-Hosted)
```python
# SearXNG Docker Setup
docker run -d \
  --name searxng \
  -p 8080:8080 \
  searxng/searxng:latest

# Query Example
import requests
results = requests.get('http://localhost:8080/search', params={
    'q': 'crypto HFT strategy 2025',
    'format': 'json',
    'engines': 'google,bing,duckduckgo,reddit,github'
}).json()
```

**Fallback:** Swirl (Open-Source Meta-Search)
```bash
git clone https://github.com/swirlai/swirl-search
cd swirl-search && docker-compose up -d
```

**Free APIs:**
- Google Custom Search API (100 queries/day free)
- Bing Search API (1000 queries/month free)

### **2. Social Media Intelligence**

#### **Twitter/X:**
```python
# Option 1: snscrape (Free, no API key)
import snscrape.modules.twitter as sntwitter

for tweet in sntwitter.TwitterSearchScraper('#crypto HFT').get_items():
    if tweet.date > datetime.now() - timedelta(hours=24):
        yield tweet.content

# Option 2: Twitter API v2 (Free tier: 500k tweets/month)
# Option 3: Nitter (RSS feed from Twitter)
```

#### **Reddit:**
```python
# PRAW (Python Reddit API Wrapper)
import praw

reddit = praw.Reddit(
    client_id='YOUR_CLIENT_ID',
    client_secret='YOUR_CLIENT_SECRET',
    user_agent='ResearchAgent/1.0'
)

# Search crypto subreddits
for submission in reddit.subreddit('CryptoCurrency+Bitcoin+ethtrader').hot(limit=50):
    if 'strategy' in submission.title.lower():
        yield submission
```

#### **Discord:**
```python
# Discord.py bot for monitoring
import discord

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_message(message):
    # Monitor specific channels
    if 'trading' in message.channel.name:
        if any(kw in message.content.lower() for kw in ['strategy', 'alpha', 'signal']):
            yield message.content
```

#### **Telegram:**
```python
# Telethon for monitoring channels
from telethon import TelegramClient

client = TelegramClient('session', api_id, api_hash)

async def monitor_channels():
    channels = ['CryptoTradingSignals', 'AlphaSeekers']
    for channel in channels:
        async for message in client.iter_messages(channel, limit=50):
            yield message.text
```

### **3. On-Chain & DEX Data**

#### **DexScreener (Trending):**
```python
import requests

# Get trending pairs
def get_trending_tokens():
    r = requests.get('https://api.dexscreener.com/latest/dex/tokens/trending')
    tokens = r.json()
    
    # Filter high buzz tokens
    return [t for t in tokens if t.get('buzz_score', 0) > 80]
```

#### **DefiLlama (TVL, Volume):**
```python
# Get protocols with rising TVL
def get_rising_protocols():
    r = requests.get('https://api.llama.fi/protocols')
    protocols = r.json()
    
    # Find protocols with +20% TVL in 24h
    return [p for p in protocols if p.get('change_1d', 0) > 20]
```

#### **Dune Analytics (Custom Queries):**
```python
# Use Dune's free community queries
# Example: Top DEX by volume (last 24h)
query_id = 12345  # Public query ID
r = requests.get(f'https://api.dune.com/api/v1/query/{query_id}/results')
```

### **4. Code Repositories**

#### **GitHub Trending:**
```python
from github import Github

g = Github()  # Anonymous (60 req/hour)
# Or with token: g = Github("access_token")  # 5000 req/hour

# Trending repos in crypto
repos = g.search_repositories(
    query='crypto trading language:python',
    sort='stars',
    order='desc'
)

for repo in repos[:10]:
    if repo.pushed_at > datetime.now() - timedelta(days=7):
        yield {'name': repo.name, 'desc': repo.description, 'url': repo.html_url}
```

#### **arXiv Papers:**
```python
import arxiv

# Search recent papers
search = arxiv.Search(
    query='cryptocurrency trading strategy',
    max_results=10,
    sort_by=arxiv.SortCriterion.SubmittedDate
)

for paper in search.results():
    if paper.published > datetime.now() - timedelta(days=30):
        yield paper.summary
```

### **5. Forums**

#### **Bitcointalk:**
```python
# Web scraping (no official API)
import requests
from bs4 import BeautifulSoup

def scrape_bitcointalk():
    url = 'https://bitcointalk.org/index.php?board=159.0'  # Trading Discussion
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    
    # Parse threads
    for thread in soup.find_all('div', class_='subject'):
        yield thread.text
```

#### **Reddit Crypto Subs:**
```python
# Already covered in Social Media section
subreddits = [
    'CryptoCurrency',
    'Bitcoin',
    'ethtrader',
    'CryptoMarkets',
    'CryptoTechnology'
]
```

### **6. News Feeds (RSS)**

```python
import feedparser

RSS_FEEDS = [
    'https://cointelegraph.com/rss',
    'https://www.coindesk.com/arc/outboundfeeds/rss/',
    'https://decrypt.co/feed',
    'https://cryptopotato.com/feed/'
]

def fetch_rss():
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:10]:  # Latest 10
            if 'trading' in entry.title.lower() or 'strategy' in entry.title.lower():
                yield {'title': entry.title, 'link': entry.link, 'summary': entry.summary}
```

---

## 🤖 Processing Pipeline - Implementation

### **Step 1: Collection (Parallel)**

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def collect_all_sources():
    """Run all data collectors in parallel"""
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(collect_web_search),
            executor.submit(collect_twitter),
            executor.submit(collect_reddit),
            executor.submit(collect_discord),
            executor.submit(collect_dex_data),
            executor.submit(collect_github),
            executor.submit(collect_arxiv),
            executor.submit(collect_rss)
        ]
        
        results = []
        for future in futures:
            try:
                data = future.result(timeout=30)
                results.extend(data)
            except Exception as e:
                print(f"Error in collector: {e}")
        
        return results
```

### **Step 2: Cleaning & Filtering**

```python
def clean_and_filter(raw_data):
    """Remove spam, ads, duplicates"""
    
    cleaned = []
    
    for item in raw_data:
        # Remove spam
        if is_spam(item):
            continue
        
        # Remove ads
        if is_advertisement(item):
            continue
        
        # Keyword filtering
        if not contains_relevant_keywords(item):
            continue
        
        # Add relevance score
        item['relevance_score'] = calculate_relevance(item)
        
        cleaned.append(item)
    
    return cleaned

def is_spam(item):
    """Detect spam using heuristics"""
    spam_indicators = [
        'guaranteed profit', 'risk-free', '1000x',
        'pump and dump', 'join telegram', 'click here'
    ]
    text = item.get('text', '').lower()
    return any(indicator in text for indicator in spam_indicators)

def contains_relevant_keywords(item):
    """Check for trading strategy keywords"""
    keywords = [
        'strategy', 'trading', 'backtest', 'indicator',
        'signal', 'pattern', 'arbitrage', 'HFT',
        'momentum', 'mean reversion', 'breakout'
    ]
    text = item.get('text', '').lower()
    return any(kw in text for kw in keywords)
```

### **Step 3: Summarization (LLM)**

```python
from openai import OpenAI

# Use GPT-3.5 for cost-efficiency
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def summarize_content(items, max_items=50):
    """Summarize content using GPT-3.5"""
    
    summaries = []
    
    # Batch process to save tokens
    for batch in chunk_list(items, 10):
        combined_text = "\n\n---\n\n".join([item['text'][:500] for item in batch])
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Cheaper than GPT-4
            messages=[{
                "role": "system",
                "content": "Summarize trading strategy ideas from these sources. Extract only novel trading approaches."
            }, {
                "role": "user",
                "content": combined_text
            }],
            max_tokens=200  # Keep it short
        )
        
        summary = response.choices[0].message.content
        summaries.append(summary)
    
    return summaries

# Alternative: Local LLM (FREE!)
def summarize_with_local_llm(text):
    """Use local Llama model for free summaries"""
    import ollama
    
    response = ollama.chat(model='llama3.2:latest', messages=[{
        'role': 'user',
        'content': f'Summarize this trading idea in 1-2 sentences:\n\n{text[:1000]}'
    }])
    
    return response['message']['content']
```

### **Step 4: Deduplication (Embeddings)**

```python
from sentence_transformers import SentenceTransformer
import numpy as np

# Use lightweight model
model = SentenceTransformer('all-MiniLM-L6-v2')  # Only 80MB!

def deduplicate_ideas(ideas, threshold=0.85):
    """Remove duplicate ideas using semantic similarity"""
    
    # Generate embeddings
    embeddings = model.encode([idea['text'] for idea in ideas])
    
    # Compute similarity matrix
    similarities = np.inner(embeddings, embeddings)
    
    # Keep only unique ideas
    unique_ideas = []
    seen_indices = set()
    
    for i, idea in enumerate(ideas):
        if i in seen_indices:
            continue
        
        # Check similarity with remaining ideas
        similar_indices = np.where(similarities[i] > threshold)[0]
        seen_indices.update(similar_indices)
        
        unique_ideas.append(idea)
    
    return unique_ideas
```

### **Step 5: Scoring & Ranking**

```python
def calculate_combined_score(idea):
    """Calculate combined score from multiple factors"""
    
    # Buzz score (social media engagement)
    buzz_score = calculate_buzz(idea)
    
    # Novelty score (how unique is this idea?)
    novelty_score = calculate_novelty(idea)
    
    # Recency score (how fresh is this?)
    recency_score = calculate_recency(idea)
    
    # Source credibility score
    credibility_score = get_source_credibility(idea['source'])
    
    # Combined score (weighted)
    combined = (
        buzz_score * 0.3 +
        novelty_score * 0.4 +
        recency_score * 0.2 +
        credibility_score * 0.1
    )
    
    return combined

def calculate_buzz(idea):
    """Calculate buzz from social signals"""
    metrics = idea.get('metrics', {})
    
    upvotes = metrics.get('upvotes', 0)
    comments = metrics.get('comments', 0)
    shares = metrics.get('shares', 0)
    
    buzz = (upvotes * 1 + comments * 2 + shares * 3)
    
    # Normalize to 0-100
    return min(buzz / 100, 100)

def calculate_novelty(idea):
    """Check if idea is novel compared to knowledge base"""
    # Load historical ideas
    historical = load_knowledge_base()
    
    # Calculate similarity with existing ideas
    similarities = [
        semantic_similarity(idea['text'], hist['text'])
        for hist in historical
    ]
    
    # Novel = low similarity with existing
    avg_similarity = np.mean(similarities) if similarities else 0
    novelty = 100 * (1 - avg_similarity)
    
    return novelty

def rank_ideas(ideas):
    """Rank ideas by combined score"""
    for idea in ideas:
        idea['score'] = calculate_combined_score(idea)
    
    # Sort by score (descending)
    ranked = sorted(ideas, key=lambda x: x['score'], reverse=True)
    
    return ranked
```

---

## 💰 Cost Optimization Strategy

### **1. Use Free Tiers Aggressively**

```python
# Rotate between multiple API keys
class APIKeyRotator:
    def __init__(self, keys):
        self.keys = keys
        self.current_index = 0
    
    def get_key(self):
        key = self.keys[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.keys)
        return key

# Example: Multiple Google Custom Search API keys
google_keys = [
    'KEY_1',  # 100 queries/day
    'KEY_2',  # 100 queries/day
    'KEY_3',  # 100 queries/day
]
key_rotator = APIKeyRotator(google_keys)

def search_google(query):
    key = key_rotator.get_key()
    # Use key...
```

### **2. Self-Hosted Tools**

```bash
# SearXNG (Free meta-search)
docker run -d --name searxng -p 8080:8080 searxng/searxng:latest

# Ollama (Free local LLMs)
ollama pull llama3.2:latest
ollama pull gemma:2b

# Sentence Transformers (Free embeddings)
pip install sentence-transformers
```

### **3. Token Minimization**

```python
def minimize_tokens(text, max_chars=500):
    """Aggressively minimize text before sending to LLM"""
    
    # Remove URLs
    import re
    text = re.sub(r'http\S+', '', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Extract key sentences only
    sentences = text.split('.')
    key_sentences = [s for s in sentences if any(kw in s.lower() for kw in [
        'strategy', 'trading', 'indicator', 'signal'
    ])]
    
    # Truncate
    result = '. '.join(key_sentences[:3])
    return result[:max_chars]
```

### **4. Local LLMs for Bulk Operations**

```python
# Use Ollama for summaries (FREE!)
import ollama

def bulk_summarize(texts):
    """Summarize many texts using local LLM"""
    summaries = []
    
    for text in texts:
        response = ollama.chat(
            model='gemma:2b',  # Fast, lightweight
            messages=[{'role': 'user', 'content': f'Summarize: {text[:500]}'}]
        )
        summaries.append(response['message']['content'])
    
    return summaries

# Only use GPT-3.5 for final ranking/selection
def final_selection(summaries):
    """Use GPT-3.5 only for final selection"""
    # This costs tokens, but much less than processing everything
    combined = "\n\n".join(summaries[:10])  # Top 10 only
    
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "user",
            "content": f"Select the best 3 trading ideas:\n\n{combined}"
        }]
    )
    
    return response.choices[0].message.content
```

---

## 🔧 Twitter Agent Integration

### **Option 1: Integrate Existing Twitter Agent**

```python
# src/agents/twitter_agent.py exists
from src.agents.twitter_agent import TwitterAgent

class ResearchAgentV2:
    def __init__(self):
        self.twitter_agent = TwitterAgent()
    
    def collect_twitter_data(self):
        """Use existing Twitter agent"""
        return self.twitter_agent.search_tweets(
            keywords=['crypto', 'trading', 'strategy'],
            hours=24
        )
```

### **Option 2: Create Integrated Twitter Module**

```python
# src/agents/research_agent_v2/sources/twitter.py

class TwitterSource:
    """Twitter data source for Research Agent"""
    
    def __init__(self):
        # Could reuse existing Twitter agent or create new
        pass
    
    def collect(self, keywords, hours=24):
        """Collect tweets"""
        pass
    
    def analyze_sentiment(self, tweets):
        """Analyze sentiment"""
        pass
    
    def find_trending(self):
        """Find trending topics"""
        pass
```

**EMPFEHLUNG:** **Option 2** (Integrated Module)
- Cleaner architecture
- Research Agent owns its data sources
- Easier to extend and maintain

---

## 📦 File Structure

```
src/agents/research_agent_v2/
├── __init__.py
├── main.py                    # Main orchestrator
├── config.py                  # Configuration
│
├── sources/                   # Data collectors
│   ├── __init__.py
│   ├── web_search.py         # SearXNG, Swirl
│   ├── twitter.py            # Twitter/X
│   ├── reddit.py             # Reddit
│   ├── discord.py            # Discord
│   ├── telegram.py           # Telegram
│   ├── dex_data.py           # DexScreener, DefiLlama
│   ├── github.py             # GitHub trending
│   ├── arxiv.py              # arXiv papers
│   ├── forums.py             # Bitcointalk, etc.
│   └── rss_feeds.py          # RSS news feeds
│
├── processing/               # Data processing
│   ├── __init__.py
│   ├── cleaner.py           # Spam removal, filtering
│   ├── summarizer.py        # LLM summaries
│   ├── deduplicator.py      # Semantic deduplication
│   ├── scorer.py            # Buzz, novelty, recency scores
│   └── ranker.py            # Final ranking
│
├── models/                   # ML models
│   ├── __init__.py
│   ├── embeddings.py        # Sentence transformers
│   ├── sentiment.py         # Sentiment analysis
│   └── llm_client.py        # LLM interface (GPT-3.5, Ollama)
│
├── storage/                  # Data persistence
│   ├── __init__.py
│   ├── knowledge_base.py    # Historical ideas
│   ├── trending_cache.py    # Current trends
│   └── dedup_index.py       # Deduplication index
│
└── utils/                    # Utilities
    ├── __init__.py
    ├── api_rotator.py       # API key rotation
    ├── rate_limiter.py      # Rate limiting
    └── logger.py            # Logging
```

---

## 🚀 Implementation Roadmap

### **Phase 1: Core Infrastructure (Week 1)**
1. ✅ Set up new file structure
2. ✅ Implement config system
3. ✅ Create base collector interface
4. ✅ Set up logging & monitoring

### **Phase 2: Data Sources (Week 2)**
1. ✅ Web search (SearXNG/Swirl)
2. ✅ Twitter integration
3. ✅ Reddit integration
4. ✅ DEX data (DexScreener)
5. ✅ RSS feeds

### **Phase 3: Processing Pipeline (Week 3)**
1. ✅ Cleaner & Filter
2. ✅ Summarizer (Local LLM + GPT-3.5)
3. ✅ Deduplicator (Embeddings)
4. ✅ Scorer & Ranker

### **Phase 4: Cost Optimization (Week 4)**
1. ✅ API key rotation
2. ✅ Token minimization
3. ✅ Local LLM integration
4. ✅ Caching & rate limiting

### **Phase 5: Testing & Tuning (Week 5)**
1. ✅ End-to-end testing
2. ✅ Performance optimization
3. ✅ Cost analysis
4. ✅ Quality metrics

---

## 🎯 Success Metrics

| Metric | Target |
|--------|--------|
| **Idea Quality** | Top 3 ideas per day are actionable |
| **Novelty Rate** | >80% of ideas are truly novel |
| **Cost per Idea** | <$0.10 (including all API costs) |
| **Latency** | Full cycle <10 minutes |
| **Source Coverage** | All 8 sources active |
| **Uptime** | >99% (24/7 operation) |

---

## 💡 Next Steps

1. **Review & Approve Design**
2. **Set up Development Environment**
3. **Implement Phase 1 (Core Infrastructure)**
4. **Test with Single Source (Twitter)**
5. **Expand to All Sources**
6. **Optimize & Deploy**

---

## 🤔 Questions for Discussion

1. **Twitter Agent:** Integrate existing or create new module?
2. **LLM Choice:** Local (Ollama) vs Cloud (GPT-3.5)?
3. **Deployment:** Docker Compose vs Separate Services?
4. **Monitoring:** What metrics to track in real-time?
5. **Priority:** Which data source to implement first?

---

**Ready to start implementation?** 🚀
