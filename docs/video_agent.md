# 🎬 Video Agent - Sora 2 Integration

**🌙 Built by Moon Dev**

An AI-powered video generation agent using OpenAI's Sora 2 API for parallel video creation from text prompts.

---

## 🎯 What It Does

The Video Agent leverages OpenAI's Sora 2 model to generate videos directly from text descriptions. It supports parallel video generation, allowing you to queue multiple video ideas that process simultaneously in the background.

### Key Features

- ✨ **Text-to-Video Generation**: Create videos directly from text prompts using Sora 2
- 🚀 **Parallel Processing**: 9 worker threads process multiple videos simultaneously
- ⚙️ **Configurable Settings**: Control resolution, duration, and aspect ratio
- 📱 **Multi-Format Support**: Generate for TikTok (9:16), YouTube (16:9), Instagram (1:1), and more
- 💾 **Auto-Save Organization**: Videos saved in date-organized folders
- 📊 **Live Status Tracking**: Monitor all video jobs in real-time

---

## 🚀 Quick Start

### Prerequisites

1. **OpenAI API Key with Sora Access**
   - Get API key from: https://platform.openai.com/api-keys
   - ⚠️ **Important**: Sora 2 API requires explicit access/invitation from OpenAI
   - Not broadly public yet - join waitlist or contact OpenAI sales

2. **Add API Key to `.env`**
   ```bash
   OPENAI_KEY=your_openai_api_key_here
   ```

3. **Upgrade OpenAI Package**
   ```bash
   pip install openai --upgrade
   pip freeze > requirements.txt
   ```

### Run the Agent

```bash
python src/agents/video_agent.py
```

---

## 📖 Usage

### Interactive Mode

When you run the agent, you'll see an interactive prompt:

```
╔══════════════════════════════════════════════════════════╗
║  🌙 Moon Dev's Sora 2 Video Generation Agent           ║
║  Parallel video generation with OpenAI Sora 2          ║
╚══════════════════════════════════════════════════════════╝

⚙️  Video Settings:
   Model: sora-2 | Resolution: 720p | Duration: 8s
   Aspect Ratio: 9:16
   Format: Vertical (TikTok, Reels, Shorts)

💡 Pro Tips:
   - Type '/status' to see all jobs
   - Type '/quit' to exit
   - Videos process in parallel - queue multiple ideas!

────────────────────────────────────────────────────────────
TYPE YOUR VIDEO IDEA BELOW:
➤
```

### Example Prompts

Here are some example video ideas you can try:

```
A cinematic shot of Bitcoin charts rising dramatically with traders celebrating in the background

A slow-motion explosion of green candles as the market pumps, with confetti falling

Traders screaming and crying "Bitcoin is going to zero!" but then one person says "I'm buying. No gamble, no future."

An aesthetic time-lapse of a trading desk with multiple monitors showing crypto charts

A dramatic scene of a whale entering the ocean while crypto prices spike
```

### Commands

- `/status` - View all video jobs and their current status
- `/quit` or `/exit` - Shutdown the agent gracefully

---

## ⚙️ Configuration

Edit settings at the top of `src/agents/video_agent.py`:

```python
# Sora 2 Configuration
MODEL = "sora-2"  # Options: "sora-2", "sora-2-pro"
DEFAULT_RESOLUTION = "720p"  # Options: "1080p", "720p"
DEFAULT_DURATION = 8  # Seconds: 4, 8, or 12
MAX_WORKERS = 9  # Number of parallel video generation threads

# Aspect Ratio Configuration
DEFAULT_ASPECT_RATIO = "9:16"  # Change this for different video formats!
```

### Aspect Ratio Options

| Aspect Ratio | Description | Best For |
|--------------|-------------|----------|
| `9:16` | Vertical | TikTok, Instagram Reels, YouTube Shorts |
| `16:9` | Widescreen | YouTube videos, landscape content |
| `1:1` | Square | Instagram feed posts |
| `4:3` | Classic TV | Traditional video format |
| `21:9` | Cinematic | Ultra-wide, cinematic content |

### Model Options

- **`sora-2`**: Standard model, 720p resolution, faster output ($0.10/second)
- **`sora-2-pro`**: Premium model, 1080p resolution, higher quality ($0.30-$0.50/second)

---

## 📊 Understanding Video Jobs

### Job Statuses

Videos go through several states during generation:

- **⏳ Queued**: Video job created, waiting for worker
- **🎬 Generating**: Worker actively processing the video
- **✅ Completed**: Video generated and saved successfully
- **❌ Failed**: Error occurred during generation

### Checking Status

Type `/status` at any time to see all your video jobs:

```
================================================================================
📊 VIDEO GENERATION STATUS
================================================================================

📈 Summary:
   ⏳ Queued: 2
   🎬 Generating: 3
   ✅ Completed: 5
   ❌ Failed: 0

📋 All Jobs:

✅ video_69037464de... [COMPLETED] (127s)
   Created: 10:21:15
   Prompt: Traders screaming Bitcoin is going to zero...
   Video: src/data/video_agent/2025-10-30/102317_Traders_screaming_Bitcoin.mp4
```

---

## 📂 Output Structure

Videos are automatically organized by date:

```
src/data/video_agent/
├── 2025-10-30/
│   ├── 102317_Traders_screaming_Bitcoin.mp4
│   ├── 103045_Cinematic_shot_of_Bitcoin.mp4
│   └── 104512_Whale_entering_ocean.mp4
├── 2025-10-31/
│   └── ...
```

**Filename Format**: `HHMMSS_[first_30_chars_of_prompt].mp4`

---

## 💰 Pricing

### Sora 2 API Costs

- **Sora 2**: $0.10 per second of video
- **Sora 2 Pro**: $0.30-$0.50 per second of video

### Example Costs

| Duration | Sora 2 | Sora 2 Pro |
|----------|--------|------------|
| 4 seconds | $0.40 | $1.20-$2.00 |
| 8 seconds | $0.80 | $2.40-$4.00 |
| 12 seconds | $1.20 | $3.60-$6.00 |

**Pro Tip**: Start with 4-8 second videos at 720p to test before scaling up!

---

## 🛠️ Troubleshooting

### AttributeError: 'OpenAI' object has no attribute 'videos'

**Solution**: Upgrade your OpenAI package
```bash
pip install openai --upgrade
```

You need OpenAI SDK version 2.6.1 or higher.

### Access Denied / Authentication Errors

**Reason**: Sora 2 API is not broadly public yet

**Solutions**:
1. Check if you have Sora API access at: https://platform.openai.com/account/api-keys
2. Join the Sora API waitlist
3. Contact OpenAI sales for enterprise access
4. ChatGPT Plus subscribers can use Sora via the web interface (not API)

### Videos Take Too Long (Timeout)

The agent has a 20-minute timeout per video. If videos consistently timeout:

1. Reduce `DEFAULT_DURATION` from 12s to 8s or 4s
2. Simplify your prompts
3. Use `sora-2` instead of `sora-2-pro`
4. Check OpenAI status page for API slowdowns

### Worker Messages Overlapping Prompt

**Fixed in latest version!** The agent now adds proper delays and spacing to prevent worker status messages from interrupting the prompt.

---

## 🎨 Tips for Great Video Prompts

### Structure Your Prompts

Good prompts are:
- **Specific**: Describe exactly what you want to see
- **Visual**: Focus on visual elements, not abstract concepts
- **Detailed**: Include camera angles, lighting, mood
- **Actionable**: Describe what's happening in the scene

### Example Comparisons

❌ **Bad**: "Make a video about Bitcoin"

✅ **Good**: "A cinematic slow-motion shot of a golden Bitcoin coin rotating in space with stars in the background, dramatic lighting from the right side"

❌ **Bad**: "Crypto trading video"

✅ **Good**: "A professional trading desk with 4 monitors showing green candlestick charts, a trader's hands typing on a mechanical keyboard, modern office with city skyline visible through windows, golden hour lighting"

### Trading Video Ideas

- Market crash/pump reactions
- Whale activity visualizations
- Technical analysis chart animations
- Trading desk setups
- Crypto coin showcases
- Market sentiment scenes
- Educational explainer visuals

---

## 🔄 Parallel Processing

The agent runs **9 worker threads** simultaneously, meaning you can:

1. Queue up 10 video ideas in a row
2. Walk away while they all generate in parallel
3. Come back to 10 completed videos

**Example Workflow**:
```
➤ First video idea
➤ Second video idea
➤ Third video idea
...
➤ /status    # Check progress
...
➤ /quit      # When all done
```

All videos will process in the background while you continue adding more!

---

## 🚨 Important Notes

### API Access Requirements

⚠️ **The Sora 2 API is not broadly public yet**

- Requires explicit invitation from OpenAI
- ChatGPT Plus/Pro has Sora access (web only, not API)
- API access is separate and requires waitlist/approval
- Expected to roll out gradually to developers

### Rate Limits

OpenAI may have rate limits on:
- Number of concurrent video generations
- Total seconds of video per hour/day
- API request frequency

The agent handles this by queuing jobs and processing them as workers become available.

### Video Quality

- Sora 2 generates realistic, physically accurate videos
- Quality depends heavily on prompt engineering
- Results may vary - experiment with different descriptions
- Pro version offers higher resolution and quality

---

## 📚 Code Structure

```python
# Main components:
- create_video_job()      # Creates video generation job via API
- poll_video_job()        # Monitors job status and downloads result
- video_worker()          # Background worker that processes jobs
- save_video_bytes()      # Saves downloaded video to disk
- display_status()        # Shows status of all jobs
- main()                  # Interactive CLI loop
```

**Key Design Features**:
- Thread-safe job tracking with locks
- Queue-based worker distribution
- Graceful shutdown handling
- Auto-retry logic for polling
- Date-organized file output

---

## 🌙 Moon Dev's Use Cases

### Content Creation Pipeline

1. **Generate Video Clips**: Use Sora to create short trading reaction clips
2. **Combine with Audio**: Add voiceovers or music in post-production
3. **Post to Social Media**: Share on TikTok, Reels, Shorts
4. **Scale Content**: Generate dozens of videos in parallel

### Trading Content Ideas

- Market analysis visuals
- Strategy explanation scenes
- Reaction videos to market moves
- Educational content backgrounds
- Thumbnail/intro animations
- Social media clips

---

## 🔗 Related Agents

- **Chat Agent**: Monitors live stream chat and responds
- **Twitter Agent**: Creates tweet content using AI
- **Clips Agent**: Helps clip long videos into shorter segments
- **Phone Agent**: AI agent for handling phone calls

---

## 📝 Requirements

**Python Packages**:
- `openai >= 2.6.1` - OpenAI SDK with Sora support
- `python-dotenv` - Environment variable management
- `termcolor` - Colored terminal output
- `requests` - HTTP requests

**External Services**:
- OpenAI API key with Sora 2 access

---

## 🎓 Learn More

- **OpenAI Sora 2 Release**: https://openai.com/sora
- **Sora API Docs**: https://platform.openai.com/docs/guides/video-generation
- **Moon Dev YouTube**: Weekly updates and tutorials
- **Discord Community**: https://discord.gg/8UPuVZ53bh

---

**🌙 Built with love by Moon Dev - Democratizing AI agent development**

*Part of the Moon Dev AI Agents for Trading ecosystem - 48+ specialized agents, all open source.*
