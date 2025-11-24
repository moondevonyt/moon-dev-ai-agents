# Giveaway Agent

**Built by Moon Dev** 🌙

## What It Does

Monitors live stream chat participation across multiple platforms (YouTube, Twitch, X) via Restream integration.

**Core Functionality:**
- Tracks chat messages and awards points for participation
- Collects and stores Solana wallet addresses from participants
- Maintains a point-based leaderboard saved to CSV
- Real-time terminal display shows participant activity

## Key Features

- **Multi-Platform** - Tracks YouTube, Twitch, X simultaneously
- **Simple Rules** - Messages over 10 characters get points
- **Solana Addresses** - Users drop address once, tracked forever
- **Point System** - Earn points for participation
- **One-Line Display** - Clean bottom-left status (red/green)
- **777 Exception** - Instant point for any message with "777" (15-min cooldown)

## How It Works

### Normal Messages:
1. **User chats** on stream (any platform)
2. **Check length** - Must be ≥10 characters (configurable)
3. **Award point** - User gets +1 point, green flash shows `+1 username`
4. **Data saved** - CSV tracks: username, Solana address, points

### 777 Exception:
- **Any message with "777"** = auto point! 🎰
- **Bypasses** minimum character requirement
- **Cooldown**: Max 1 per 15 minutes per user
- Example: User types "777" → instant +1 point!

## Visual Display

**Terminal output:**

The agent displays on a **single line** that updates in real-time.

**Shows:**
```
Yellow Background (Black Text):  Drop Sol Wallet To Enter  (default state)
```

When someone earns a point:
```
Green Background (White Text):  +1 moondev123  (flashes for 3 seconds)
```

When someone enters their Solana address:
```
Green Background (White Text):  moondev123 addy saved  (flashes for 3 seconds)
```

Then automatically reverts back to yellow "Drop Sol Wallet To Enter"

**Super clean** - no scrolling, just one line that updates!

## Data Storage

Saves to: `src/data/giveaway_agent/participants.csv`

```csv
username,solana_address,points
moondev123,7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU,42
trader456,9zYtF3kL12pQw89sVbNmR4tGhUiOp7aS6dFgHjKl8mNb,28
```

## Requirements

```bash
pip install selenium
brew install chromedriver  # macOS
```

**Restream Token** - Add to `.env`:
```
RESTREAM_EMBED_TOKEN=your_token_here
```

Get your token from Restream.io account settings.

## Usage

```bash
python src/agents/giveaway_agent.py
```

Then just leave it running during your stream!

## Configuration

Edit `src/agents/giveaway_agent.py` top section:

```python
# Minimum characters for a chat to be considered
MIN_CHARS = 10

# Flash duration for status messages (seconds)
FLASH_DURATION = 3  # How long to show "+1 username" or "username addy saved"

# 777 auto-point settings
SEVEN_SEVEN_SEVEN_COOLDOWN = 900  # 15 minutes in seconds
```

The Restream URL is automatically configured using your `RESTREAM_EMBED_TOKEN` from `.env`.

## Flow

### Normal Message Flow:
```
User Types Message
       ↓
Length ≥ 10 chars?
       ↓ YES
+1 Point
       ↓
Flash Green: +1 username
       ↓
Save to CSV
```

### 777 Message Flow:
```
User Types: "777"
       ↓
Contains 777?
       ↓ YES
Check Cooldown (15 min)
       ↓ PASSED
+1 Point (auto!)
       ↓
Flash Green: +1 username
       ↓
Save to CSV
```

## New User Flow

```
User Types First Message
       ↓
Not in CSV
       ↓
Create Entry with "PENDING" address
       ↓
User Drops Solana Address
       ↓
Update CSV with Real Address
       ↓
Flash Green: username addy saved
       ↓
Future Messages = Points!
```

## Solana Address Detection

Automatically detects Solana addresses:
- Length: 32-44 characters
- Alphanumeric only (letters + numbers, no spaces or special chars)
- Examples:
  - `7zSMfdbJNGbk9vX3xY4Z7DmnreTZ1nusuqCzKJN63A7M`
  - `7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU`

## Use Cases

- **Point-based Giveaways** - Random or weighted selection based on participation
- **Engagement Tracking** - Monitor community activity over time
- **Wallet Collection** - Gather Solana addresses for airdrops or rewards
- **Leaderboards** - Rank top participants by points earned

## Example Output

```
Drop Sol Wallet To Enter
```

That's it! Just one line.

When someone chats:
```
+1 moondev123  (green background, white text, flashes for 3 seconds)
```

When someone enters Solana address:
```
moondev123 addy saved  (green background, white text, flashes for 3 seconds)
```

Then back to:
```
Drop Sol Wallet To Enter  (yellow background, black text)
```

Zero clutter, maximum clarity!

## Viewing Participants

```bash
cat src/data/giveaway_agent/participants.csv
```

Or open in Excel/Google Sheets!

## Technical Notes

- **Open Source** - All code is public and transparent
- **Your Data** - CSV data is stored locally on your machine
- **No Token** - This is a participation tracking tool, not a cryptocurrency
- **Configurable** - All settings can be adjusted in the config section

---

**Moon Dev's Giveaway Agent** - Track participation, reward engagement 🚀🌙
