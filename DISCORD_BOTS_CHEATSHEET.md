# 🤖 Discord Bots Command Reference

This repository contains three independent Discord bots built with modern Python architecture. Each bot is its own application in the Discord Developer Portal, has its own bot token, and must be invited to your server separately.

---

## 🎯 Quick Bot Overview

| Bot | Type | Purpose | Commands |
|-----|------|---------|----------|
| **MTG Card Bot** | Prefix (`!`) | Magic card lookup | `!card name`, `!random`, `!help` |
| **Clippy Bot** | Slash (`/`) | Interactive chaos & humor | `/clippy`, `/clippy_wisdom`, `/clippy_help` |
| **Music Bot** | Slash (`/`) | Audio streaming & queue | `/play`, `/pause`, `/resume`, `/skip`, `/stop`, `/queue`, `/volume` |

---

## 🃏 MTG Card Bot - Advanced Card Lookup

**Command Prefix:** `!` (configurable)

### Core Commands

```bash
# Basic card lookup with fuzzy matching
!lightning bolt         # Finds "Lightning Bolt"
!the one ring          # Finds "The One Ring" 
!jac bele              # Finds "Jace Beleren" (fuzzy search)
!sol ring              # Finds "Sol Ring"

# Utility commands
!random                # Get a random Magic card
!help                  # Show available commands and examples
!cache                 # Display cache performance statistics
```

### Multi-Card Grid Display

Use semicolons to display multiple cards in a single message:

```bash
# Fetch multiple cards at once
!black lotus; lightning bolt; the one ring; sol ring

# Theme collections
!city of brass e:arn; library of alexandria e:arn; juzam djinn e:arn; serendib efreet e:arn

# Power comparison
!lightning bolt; bolt; lightning strike; shock
```

### Advanced Filtering (Scryfall Syntax)

```bash
# Set-specific searches
!sol ring set:lea              # From Limited Edition Alpha
!lightning bolt set:leb        # From Limited Edition Beta
!brainstorm e:ice              # From Ice Age

# Frame and border filtering
!lightning bolt frame:1993     # Original 1993 frame
!the one ring border:borderless # Borderless version
!black lotus frame:old         # Old card frame

# Foiling and special versions  
!brainstorm is:foil           # Foil versions only
!sol ring is:nonfoil          # Non-foil versions only
!lightning bolt is:fullart    # Full art versions
!shock is:textless            # Textless versions

# Rarity filtering
!lightning bolt rarity:common  # Common printings only
!sol ring rarity:uncommon     # Uncommon printings only
!black lotus rarity:rare      # Rare printings only

# Complex filtering combinations
!lightning bolt frame:1993 is:foil e:4ed    # 1993 frame foil from 4th Edition
!sol ring border:black rarity:uncommon      # Black border uncommon Sol Ring
```

### Features

- **Fuzzy Name Matching** - Handles typos and partial names
- **High-Resolution Images** - Crystal clear card images
- **Advanced Filtering** - Full Scryfall API syntax support
- **Multi-Card Grids** - Display up to 4 cards in grid format
- **Intelligent Caching** - Fast responses with cache performance tracking
- **Performance Metrics** - Built-in monitoring and statistics

### Required Permissions

- ✅ Send Messages
- ✅ Embed Links  
- ✅ Attach Files
- ✅ Read Message History
- ⚠️ **Message Content Intent** (Must enable in Developer Portal)

---

## 📎 Clippy Bot - Interactive Chaos & Humor

**Command Type:** Slash Commands (`/`)

### Slash Commands

```bash
# Core interactions
/clippy                      # Unhinged Clippy response with random personality
/clippy_wisdom              # Questionable life advice with styled embeds
/clippy_help                # Interactive help with clickable buttons

# Interactive button responses (triggered from /clippy_help)
"More Chaos" button         # Activates chaos mode with escalating responses
"I Regret This" button      # Acknowledgment of poor life choices
"Classic Clippy" button     # Random classic Clippy-style response
```

### Passive Features

- **Random Responses** - 2% chance to reply to any message
- **Periodic Messages** - Random posts every 30-90 minutes (configurable)
- **Modern References** - Current internet culture and memes
- **Interactive Buttons** - Clickable components for enhanced interaction
- **Styled Embeds** - Custom colors and formatting

### Behavior Configuration

```bash
# Environment variables to customize behavior
RANDOM_RESPONSES=true           # Enable/disable random replies
RANDOM_INTERVAL=2700           # Random message interval (45 minutes)
RANDOM_MESSAGE_DELAY=3         # Delay before random messages (seconds)
```

### Required Permissions

- ✅ Send Messages
- ✅ Use Application Commands
- ✅ Add Reactions
- ✅ Read Message History
- ✅ Embed Links

---

## 🎵 Music Bot - Full-Featured Audio Streaming

**Command Type:** Slash Commands (`/`)

### Basic Playback Commands

```bash
# Essential playback controls
/play <url or search>       # Join voice channel and queue track (YouTube)
/pause                      # Pause current song
/resume                     # Resume playback
/skip                       # Skip to next song in queue
/stop                       # Stop playback, clear queue, disconnect
/queue                      # Show now playing and upcoming tracks
/volume <0-100>            # Adjust playback volume (0-100%)
```

### Implemented Commands

```bash
/play <url or search>       # Join voice and play/queue
/pause                      # Pause current song
/resume                     # Resume playback
/skip                       # Skip current song
/stop                       # Stop and disconnect
/queue                      # Show queue
/volume <0-100>            # Set or show volume
```

### Features

- **YouTube Integration** - yt-dlp powered search and streaming
- **Queue Management** - Play, skip, and list queue
- **Multi-Server Support** - Isolated queues per server
- **Auto-Disconnect** - Leaves voice channel after inactivity
- **FFmpeg Audio** - Reliable Opus streaming

### System Requirements

- **yt-dlp** (installed via uv for the music bot)
- **FFmpeg** - [Download FFmpeg](https://ffmpeg.org/download.html)
- **Opus Library** (macOS: `brew install opus`)

### Configuration

```bash
# Music bot environment variables (optional overrides)
MUSIC_MAX_QUEUE_SIZE=100
MUSIC_INACTIVITY_TIMEOUT=300
MUSIC_VOLUME_LEVEL=0.5
```

### Required Permissions

- ✅ Send Messages
- ✅ Use Application Commands
- ✅ Connect (to voice channels)
- ✅ Speak (in voice channels)
- ✅ Read Message History
- ✅ Embed Links

---

## 🚀 Setup & Inviting Bots

### 1. Creating Discord Applications

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create **3 separate applications** (one per bot)
3. For each application:
   - Go to "Bot" section
   - Copy the bot token
   - Enable required intents (see below)

### 2. Required Bot Intents

| Bot | Server Members Intent | Message Content Intent | Presence Intent |
|-----|----------------------|------------------------|-----------------|
| **MTG Card Bot** | ❌ | ✅ **Required** | ❌ |
| **Clippy Bot** | ❌ | ✅ Recommended | ❌ |
| **Music Bot** | ❌ | ❌ | ❌ |

### 3. Generating Invite URLs

#### For MTG Card Bot (Prefix Commands)

- **Scopes:** `bot`
- **Permissions:** Send Messages, Embed Links, Attach Files, Read Message History

#### For Clippy & Music Bots (Slash Commands)

- **Scopes:** `bot` + `applications.commands`
- **Permissions:**
  - **Clippy:** Send Messages, Use Application Commands, Add Reactions, Read Message History, Embed Links
  - **Music:** Send Messages, Use Application Commands, Connect, Speak, Read Message History, Embed Links

### 4. Configuration

```bash
# Copy environment template
cp env.example .env

# Edit .env with your bot tokens
CLIPPY_DISCORD_TOKEN=your_clippy_token_here
MUSIC_DISCORD_TOKEN=your_music_token_here  
MTG_DISCORD_TOKEN=your_mtg_token_here

# Optional: Guild IDs for instant slash command registration
CLIPPY_GUILD_ID=your_guild_id_for_testing
MUSIC_GUILD_ID=your_guild_id_for_testing
MTG_GUILD_ID=your_guild_id_for_testing
```

---

## 🔧 Troubleshooting

### Slash Commands Not Appearing?

**Quick Fix Checklist:**

1. **Verify OAuth Scopes**
   - Re-invite slash command bots with scopes: `bot` + `applications.commands`

2. **Use Guild-Scoped Registration**
   - Set `CLIPPY_GUILD_ID` and/or `MUSIC_GUILD_ID` in `.env`
   - Guild commands appear instantly vs. 1 hour for global commands

3. **Check Startup Logs**
   - Look for "Registered command" messages
   - Enable debug: `DEBUG=true` in `.env`

4. **Confirm Token/App Match**
   - Each bot must use its own application's bot token
   - Mismatched tokens register commands under wrong app

5. **Verify Discord Permissions**
   - Ensure bot role has "Use Application Commands" permission
   - Check channel-specific permission overrides

6. **Last Resort: Re-register**
   - Restart bot to remove and re-register commands
   - Global commands may take up to 1 hour to propagate

### Common Issues

| Issue | Solution |
|-------|----------|
| MTG bot not responding to `!` commands | Enable "Message Content Intent" in Developer Portal |
| Music bot can't join voice channel | Check "Connect" and "Speak" permissions |
| Slash commands missing | Verify OAuth scopes include `applications.commands` |
| Random responses not working | Set `RANDOM_RESPONSES=true` in environment |
| Music playback failing | Install yt-dlp and FFmpeg system dependencies |

### Performance Tips

- **Use Guild IDs** for faster slash command registration during development
- **Enable Caching** for MTG bot to reduce API calls
- **Configure Timeouts** appropriately for your server size
- **Monitor Logs** with `LOG_LEVEL=debug` for troubleshooting

---

## 📊 Bot Comparison

| Feature | MTG Card Bot | Clippy Bot | Music Bot |
|---------|--------------|------------|-----------|
| **Command Style** | Prefix (`!`) | Slash (`/`) | Slash (`/`) |
| **Primary Use** | Card lookup | Entertainment | Audio streaming |
| **Database Required** | No | No | No |
| **External APIs** | Scryfall | None | YouTube |
| **Voice Channel** | No | No | Yes |
| **Message Content Intent** | Required | Recommended | Optional |
| **System Dependencies** | None | None | yt-dlp, FFmpeg |
| **Interactive Elements** | Embeds | Buttons | Embeds |
| **Passive Behavior** | No | Random messages | Auto-disconnect |

---

That's your complete command reference for all three Python Discord bots! 🚀

For more detailed setup instructions, see the [README.md](README.md) file.
