# Python Discord Bots

<p align="center">
  <img src="https://github.com/dunamismax/images/blob/main/python/discord-bots/python.png" alt="Python Discord Bots" width="200" />
</p>

<p align="center">
  <a href="https://python.org/"><img src="https://img.shields.io/badge/Python-3.12+-3776AB.svg?logo=python&logoColor=white" alt="Python Version"></a>
  <a href="https://github.com/Rapptz/discord.py"><img src="https://img.shields.io/badge/Discord-discord.py-5865F2.svg?logo=discord&logoColor=white" alt="discord.py"></a>
  <a href="https://github.com/astral-sh/uv"><img src="https://img.shields.io/badge/Package-uv-purple.svg" alt="uv"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License"></a>
</p>

A modern Discord bot collection featuring three specialized bots: **MTG Card Bot** for Magic card lookups, **Clippy Bot** for interactive AI responses, and **Music Bot** for audio streaming with queue management.

## Documentation

- **[Discord.py Update Guide](DISCORD_PY_UPDATE.md)** - Managing the local discord.py repository
- **[Commands Cheatsheet](DISCORD_BOTS_CHEATSHEET.md)** - Quick command reference

## Quick Start

### Prerequisites

- **[uv](https://docs.astral.sh/uv/)** - Fast Python package manager
- **Discord Bot Token(s)** - From [Discord Developer Portal](https://discord.com/developers/applications)

### Installation

```bash
# 1. Install uv and Python 3.12
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.12

# 2. Clone and setup
git clone https://github.com/dunamismax/python-bots.git
cd python-bots

# 3. Configure environment
cp env.example .env
# Edit .env with your Discord bot tokens

# 4. Start bots
uv run python start_bots.py
```

### Environment Configuration

```bash
# Required Discord tokens
CLIPPY_DISCORD_TOKEN=your_clippy_token_here
MUSIC_DISCORD_TOKEN=your_music_token_here
MTG_DISCORD_TOKEN=your_mtg_token_here

# Optional settings
LOG_LEVEL=info
MUSIC_MAX_QUEUE_SIZE=100
MTG_CACHE_TTL=3600
```

## Bot Features

### MTG Card Bot

Advanced Magic: The Gathering card lookup with fuzzy search and filtering.

```bash
!lightning bolt                    # Basic card lookup
!black lotus; sol ring; time walk  # Multi-card grid
!brainstorm e:ice is:foil          # Advanced filtering
!random                            # Random card discovery
```

### Clippy Bot

Interactive AI assistant with modern Discord slash commands.

```bash
/clippy                   # Get quirky AI responses
/clippy_wisdom           # Questionable life advice
/clippy_help             # Interactive help with buttons
```

### Music Bot

Full-featured audio streaming with YouTube integration and queue management.

```bash
/play <song/url>         # Play music from YouTube
/queue                   # Show current playlist
/skip, /pause, /resume   # Playback controls
/volume <0-100>          # Adjust volume
```

## Architecture

```
python-bots/
├── bots/                    # Independent bot applications
│   ├── clippy/             # Interactive AI assistant
│   ├── mtg-card-bot/       # Magic card lookups
│   └── music/              # Audio streaming
├── discord.py/             # Local discord.py (v8 voice fix)
├── docs/                   # Comprehensive documentation
├── start_bots.py          # Interactive bot launcher
└── troubleshoot_bots.sh   # Process management utility
```

## Development

```bash
# Interactive bot launcher (recommended)
uv run python start_bots.py

# Individual bot execution
uv run --package clippy-bot python -m clippy
uv run --package mtg-card-bot python -m mtg_card_bot
uv run --package music-bot python -m music

# Development tools
uv run ruff format .       # Code formatting
uv run ruff check .        # Linting
uv run mypy bots/         # Type checking
```

## Key Features

- **Graceful Shutdown** - Enhanced Ctrl+C handling and process management
- **Fixed Voice Connections** - Local discord.py with WebSocket 4006 fix
- **Modern Packaging** - uv-based dependency management
- **Interactive Management** - Menu-driven bot launcher with real-time logs
- **Comprehensive Docs** - Detailed guides for maintenance and updates

## Important Notes

This project uses a **local copy of discord.py** with unreleased fixes for voice connection issues. See the [Discord.py Update Guide](DISCORD_PY_UPDATE.md) for maintenance instructions.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>Modern Discord Bot Collection</strong><br>
  <sub>Built with Python 3.12+ • discord.py • uv • 2025 Best Practices</sub>
</p>
