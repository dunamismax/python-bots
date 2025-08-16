<p align="center">
  <img src="https://github.com/dunamismax/images/blob/main/python/discord-bots/python.png" alt="Python Discord Bots" width="300" />
</p>

<p align="center">
  <a href="https://github.com/dunamismax/python-bots">
    <img src="https://readme-typing-svg.demolab.com/?font=Fira+Code&size=24&pause=1000&color=3776AB&center=true&vCenter=true&width=900&lines=Python+Discord+Bots+Monorepo;Three+Specialized+Bots+in+One+Repository;MTG+Card+Bot+with+Advanced+Filtering;Clippy+Bot+with+Interactive+Slash+Commands;Music+Bot+with+Queue+Management;Modern+Python+Architecture+2025;Microservice+Pattern+Implementation;Shared+Libraries+and+Common+Infrastructure;uv+Package+Management" alt="Typing SVG" />
  </a>
</p>

<p align="center">
  <a href="https://python.org/"><img src="https://img.shields.io/badge/Python-3.12+-3776AB.svg?logo=python&logoColor=white" alt="Python Version"></a>
  <a href="https://github.com/Rapptz/discord.py"><img src="https://img.shields.io/badge/Discord-discord.py-5865F2.svg?logo=discord&logoColor=white" alt="discord.py"></a>
  <a href="https://scryfall.com/docs/api"><img src="https://img.shields.io/badge/API-Scryfall-FF6B35.svg" alt="Scryfall API"></a>
  <a href="https://github.com/astral-sh/uv"><img src="https://img.shields.io/badge/Package-uv-purple.svg" alt="uv"></a>
  <a href="https://ffmpeg.org/"><img src="https://img.shields.io/badge/FFmpeg-required-007808.svg" alt="FFmpeg"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License"></a>
</p>

---

## About

A modern Discord bot monorepo with three independent bots. Each bot is self-contained with its own code and configuration—no shared package.

**Bot Collection:**

* **MTG Card Bot** – Advanced Magic card lookup with fuzzy search, filtering, and Scryfall API integration
* **Clippy Bot** – Unhinged AI persona with interactive slash commands and button components  
* **Music Bot** – Full-featured audio playback with queue management and YouTube integration

**Highlights:**

- Independent per-bot code and config (no shared module)
- Simple .env configuration per bot
- Interactive launcher (`start_bots.py`) or run bots individually
- Async I/O and lightweight logging

---

## 🚀 Quick Start

### Prerequisites

- **uv** - Fast Python package manager and runtime
- **Discord Bot Token(s)** - Create applications at [Discord Developer Portal](https://discord.com/developers/applications)
- **FFmpeg** - For music bot audio processing: [Download here](https://ffmpeg.org/download.html)

### Installation

```bash
# 1. Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install Python 3.12 and set as global default
uv python install 3.12
uv python pin 3.12

# 3. Clone the repository
git clone https://github.com/dunamismax/python-bots.git
cd python-bots

# 4. Copy environment template and add your tokens
cp env.example .env
# Edit .env with your bot tokens

# 5. Start the interactive bot manager
uv run python start_bots.py
```

### Configuration

Edit `.env` with your tokens (minimal example):

```bash
CLIPPY_DISCORD_TOKEN=...
MUSIC_DISCORD_TOKEN=...
MTG_DISCORD_TOKEN=...

# Optional
LOG_LEVEL=info
DEBUG=false

# Music bot (optional overrides)
MUSIC_MAX_QUEUE_SIZE=100
MUSIC_INACTIVITY_TIMEOUT=300
MUSIC_VOLUME_LEVEL=0.5

# MTG bot (optional overrides)
MTG_CACHE_TTL=3600
MTG_CACHE_SIZE=1000
```

### Running Bots

#### Interactive Bot Manager (Recommended)
```bash
# Start the interactive CLI bot manager
uv run python start_bots.py

# This interactive script will:
# - Scan and detect all available bots automatically
# - Present a menu with arrow key navigation
# - Allow you to start all bots or individual bots
# - Validate environment variables are set
# - Sync all dependencies automatically
# - Display logs with bot-specific prefixes
# - Handle graceful shutdown with Ctrl+C
```

#### Manual Bot Execution
```bash
# Run bots individually (without the menu)
uv run --package clippy-bot python -m clippy
uv run --package mtg-card-bot python -m mtg_card_bot
uv run --package music-bot python -m music
```

---

## 🔧 Development

- Format: `uv run ruff format .`
- Lint: `uv run ruff check .`
- Types: `uv run mypy bots/`

---

<p align="center">
  <img src="https://github.com/dunamismax/images/blob/main/python/discord-bots/python-bot.png" alt="python-bots" width="300" />
</p>

## 🤖 Bot Commands & Features

### MTG Card Bot

Advanced Magic: The Gathering card lookup with fuzzy search and filtering.

```bash
# Card lookup with fuzzy matching
!lightning bolt        # Finds "Lightning Bolt"
!the one ring         # Finds "The One Ring"
!jac bele             # Finds "Jace Beleren" (fuzzy search)

# Multi-card grids (semicolon-separated)
!black lotus; lightning bolt; the one ring; sol ring

# Advanced filtering with Scryfall syntax
!lightning bolt frame:1993         # Original 1993 frame
!the one ring border:borderless   # Borderless version
!brainstorm is:foil e:ice         # Foil from Ice Age
!sol ring set:lea                 # From Limited Edition Alpha

# Random card discovery & stats
!random               # Get a random Magic card
!help                 # Show available commands
!cache                # Cache utilization stats
```

Features: fuzzy search, Scryfall filters, images, multi-card grids, caching.

### Clippy Bot

Unhinged AI persona with modern Discord interactions.

```bash
# Modern Slash Commands with Interactive Components
/clippy                      # Unhinged Clippy response
/clippy_wisdom              # Questionable life advice with styled embeds
/clippy_help                # Interactive help with clickable buttons

# Interactive Button Features (triggered from /clippy_help)
"More Chaos" button         # Activates chaos mode
"I Regret This" button      # Regret acknowledgment
"Classic Clippy" button     # Random classic response
```

Features: slash commands, interactive buttons, optional random replies.

### Music Bot

Complete audio streaming solution with playlist management.

```bash
# Basic Playback
/play <query>               # YouTube URL or search
/pause                      # Pause current song
/resume                     # Resume playback
/skip                       # Skip to next song
/stop                       # Stop and disconnect
/queue                      # Show current queue
/volume <0-100>            # Adjust volume

# Playlist System (Database Required)
/playlist_create <name>     # Create new playlist
/playlist_list             # List your playlists
/playlist_show <id>        # Show playlist contents
/playlist_add <id> <song>  # Add song to playlist
/playlist_play <id>        # Play entire playlist
```

Features: YouTube/yt-dlp integration, queue, volume control, auto-disconnect.

---

## 🏗️ Architecture & Project Structure

### Modern Monorepo Structure

```
python-bots/
├── bots/                          # Independent bot applications
│   ├── clippy/                    # Clippy bot with slash commands
│   │   ├── src/clippy/            # Bot source code
│   │   │   ├── __main__.py        # Entry point
│   │   │   ├── bot.py             # Main bot implementation
│   │   │   └── quotes.py          # Clippy quotes and responses
│   │   └── pyproject.toml         # Bot-specific dependencies
│   ├── mtg-card-bot/              # MTG card lookup bot
│   │   ├── src/mtg_card_bot/      # Bot source code
│   │   │   ├── __main__.py        # Entry point
│   │   │   ├── bot.py             # Main bot implementation
│   │   │   ├── cache.py           # Card caching system
│   │   │   └── scryfall.py        # Scryfall API client
│   │   └── pyproject.toml         # Bot-specific dependencies
│   └── music/                     # Music streaming bot
│       ├── src/music/             # Bot source code
│       │   ├── __main__.py        # Entry point
│       │   ├── bot.py             # Main bot implementation
│       │   ├── audio.py           # Audio processing
│       │   ├── extractor.py       # YouTube extraction
│       │   ├── queue.py           # Queue management
│       │   └── models.py          # Data models
│       └── pyproject.toml         # Bot-specific dependencies
├── start_bots.py                  # Interactive launcher for all bots
├── bin/                           # Management and utility scripts
│   └── python-bots                # Main management script
├── .env.example                   # Environment configuration template
├── config.example.json            # Alternative JSON configuration
├── pyproject.toml                 # Workspace configuration
└── uv.lock                        # Dependency lock file
```

### Technology

- Python 3.12+
- discord.py 2.5+
- httpx (MTG only)
- yt-dlp + FFmpeg (Music only)
- uv, ruff, mypy

---

## ⚙️ Environment Variables (summary)

See Configuration above or `env.example` for a quick template.

---

## 🚀 Deployment

### Local Development
```bash
# Run with auto-restart and debug logging
./bin/python-bots dev
```

### Production Deployment

### Direct uv Execution
```bash
# Run individual bots in production
uv run --package clippy-bot python -m clippy
uv run --package music-bot python -m music  
uv run --package mtg-card-bot python -m mtg_card_bot
```

### Systemd (Linux)
```ini
# /etc/systemd/system/clippy-bot.service
[Unit]
Description=Clippy Discord Bot
After=network.target

[Service]
Type=simple
User=discord
WorkingDirectory=/path/to/python-bots
ExecStart=/path/to/uv run --package clippy python -m clippy
Restart=always
RestartSec=5
Environment=LOG_LEVEL=info

[Install]
WantedBy=multi-user.target
```

### Docker (example)
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install uv
RUN uv sync

CMD ["uv", "run", "--package", "clippy", "python", "-m", "clippy"]
```

### Compose (example)
```yaml
# docker-compose.yml
services:
  clippy:
    build: .
    command: uv run --package clippy python -m clippy
    environment:
      - CLIPPY_DISCORD_TOKEN=${CLIPPY_DISCORD_TOKEN}
    restart: unless-stopped
    
  music:
    build: .
    command: uv run --package music python -m music
    environment:
      - MUSIC_DISCORD_TOKEN=${MUSIC_DISCORD_TOKEN}
    volumes:
      - ./music.db:/app/music.db
    restart: unless-stopped
```

Each bot can be deployed independently or together based on your infrastructure needs.

---

## 🛠️ Development Notes

- Ensure FFmpeg is installed and on PATH for the music bot.
- Install `yt-dlp` is handled via `bots/music/pyproject.toml` when using uv.

### Adding a New Bot

1. Create bot directory: `bots/your-bot/`
2. Add `pyproject.toml` with dependencies
3. Create `src/your_bot/` package structure
4. Implement bot logic in `src/your_bot/bot.py`
5. Add entry point in `src/your_bot/__main__.py`
6. Update `./bin/python-bots` script to include new bot
7. Add configuration options to shared config system

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run quality checks: `./bin/python-bots quality`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

---

## 📊 Performance & Monitoring

### Built-in Observability

- **Structured Logging** - JSON logs with correlation IDs
- **Performance Metrics** - Response times and error rates
- **Health Checks** - Built-in status endpoints
- **Resource Monitoring** - Memory and CPU usage tracking

### Monitoring Integration

The bots include Prometheus metrics integration for production monitoring:

```python
# Example metrics available
discord_commands_total              # Total commands executed
discord_command_duration_seconds    # Command execution time
discord_errors_total               # Error count by type
cache_hits_total                   # Cache performance
api_requests_total                 # External API calls
```

---

<p align="center">
  <img src="https://github.com/dunamismax/images/blob/main/python/python-logo.png" alt="Python Discord Bots Logo" width="300" />
</p>

## 🤝 Support & Community

<p align="center">
  <a href="https://twitter.com/dunamismax" target="_blank"><img src="https://img.shields.io/badge/Twitter-%231DA1F2.svg?&style=for-the-badge&logo=twitter&logoColor=white" alt="Twitter"></a>
  <a href="https://bsky.app/profile/dunamismax.bsky.social" target="_blank"><img src="https://img.shields.io/badge/Bluesky-blue?style=for-the-badge&logo=bluesky&logoColor=white" alt="Bluesky"></a>
  <a href="https://reddit.com/user/dunamismax" target="_blank"><img src="https://img.shields.io/badge/Reddit-%23FF4500.svg?&style=for-the-badge&logo=reddit&logoColor=white" alt="Reddit"></a>
  <a href="https://discord.com/users/dunamismax" target="_blank"><img src="https://img.shields.io/badge/Discord-dunamismax-7289DA.svg?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="https://signal.me/#p/+dunamismax.66" target="_blank"><img src="https://img.shields.io/badge/Signal-dunamismax.66-3A76F0.svg?style=for-the-badge&logo=signal&logoColor=white" alt="Signal"></a>
</p>

### Getting Help

- **Documentation**: Check this README and code comments
- **Issues**: Report bugs or request features on GitHub Issues
- **Discussions**: Join GitHub Discussions for community support
- **Discord**: Find me on Discord for real-time help

### Support the Project

<p align="center">
  <a href="https://buymeacoffee.com/dunamismax" target="_blank">
    <img src="https://github.com/dunamismax/images/blob/main/python/buy-coffee-python.gif" alt="Buy Me A Coffee" style="height: 150px !important;" />
  </a>
</p>

---

## 📄 License

MIT License – see [LICENSE](LICENSE) for details.

This project is open source and free to use, modify, and distribute under the MIT license.

---

<p align="center">
  <strong>Python Discord Bots Monorepo</strong><br>
  <sub>Modern Architecture • Domain-Driven Design • Microservices • Observability • Performance Optimized • 2025 Best Practices</sub>
</p>

---
