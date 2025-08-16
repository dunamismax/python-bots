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
  <a href="https://www.structlog.org/"><img src="https://img.shields.io/badge/Logging-structlog-3776AB.svg" alt="structlog"></a>
  <a href="https://docs.pydantic.dev/"><img src="https://img.shields.io/badge/Config-Pydantic-E92063.svg" alt="Pydantic"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License"></a>
</p>

---

## About

A modern Discord bot monorepo written in Python, featuring three specialized bots with shared infrastructure. Showcases enterprise-grade architecture, microservice patterns, and 2025 best practices for Discord bot development using modern Python tooling.

**Bot Collection:**

* **MTG Card Bot** – Advanced Magic card lookup with fuzzy search, filtering, and Scryfall API integration
* **Clippy Bot** – Unhinged AI persona with interactive slash commands and button components  
* **Music Bot** – Full-featured audio playback with queue management and YouTube integration

**Architecture Highlights:**

* **Monorepo Design** – Independent bots with isolated dependencies
* **Microservice Pattern** – Each bot is self-contained with clear domain boundaries
* **Independent Configuration** – Each bot has its own configuration system and dependencies
* **Interactive Management** – Smart CLI script for easy bot management and deployment
* **Observability First** – Structured logging and performance monitoring built-in
* **Modern Tooling** – uv package management, typed configuration, and async/await patterns
* **Performance Optimized** – Async operations with intelligent caching

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
# Edit .env with your Discord bot tokens and configuration

# 5. Start the interactive bot manager
uv run python start_bots.py
```

### Configuration

Edit `.env` file with your Discord bot tokens:

```bash
# Required: Add your Discord bot tokens
CLIPPY_DISCORD_TOKEN=your_clippy_bot_token_here
MUSIC_DISCORD_TOKEN=your_music_bot_token_here
MTG_DISCORD_TOKEN=your_mtg_bot_token_here

# Optional: Guild ID for slash command testing
CLIPPY_GUILD_ID=your_guild_id_for_testing
MUSIC_GUILD_ID=your_guild_id_for_testing
MTG_GUILD_ID=your_guild_id_for_testing

# Optional: Customize behavior
LOG_LEVEL=info
DEBUG=false
COMMAND_PREFIX=!
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
# Run specific bots individually (without interactive menu)
uv run --package clippy-bot python -m clippy
uv run --package mtg-card-bot python -m mtg_card_bot
uv run --package music-bot python -m music
```

---

## 🔧 Development Commands

```bash
# Development Setup
./bin/python-bots setup         # Install dependencies and create configs
./bin/python-bots dev           # Run all bots with debug logging
./bin/python-bots run <bot>     # Run specific bot (clippy, mtg-card-bot, music)

# Code Quality
./bin/python-bots format        # Format code with ruff
./bin/python-bots lint          # Lint code with ruff and mypy
./bin/python-bots typecheck     # Type checking with mypy
./bin/python-bots test          # Run test suite
./bin/python-bots quality       # Run all quality checks
./bin/python-bots ci            # Complete CI pipeline

# Project Management
./bin/python-bots clean         # Clean build artifacts and caches
./bin/python-bots reset         # Reset to fresh state
./bin/python-bots build         # Build all applications for deployment
```

---

<p align="center">
  <img src="https://github.com/dunamismax/images/blob/main/python/discord-bots/python-bot.png" alt="python-bots" width="300" />
</p>

## 🤖 Bot Commands & Features

### MTG Card Bot - The Crown Jewel

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

**Features:**
- Fuzzy name matching for typos
- Advanced Scryfall API filtering
- High-resolution card images
- Multi-card grid display
- Intelligent caching system
- Performance metrics

### Clippy Bot - Interactive Chaos

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

**Features:**
- 2% random response rate to any message
- Periodic random messages (configurable timing)
- Real-time performance tracking
- Modern internet culture references
- Interactive button components
- Styled embeds with custom colors

### Music Bot - Full-Featured Audio

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

**Features:**
- YouTube integration with yt-dlp
- Persistent playlist database
- Queue management system
- Volume control and audio effects
- Automatic disconnection on inactivity
- Multi-server support with isolated queues

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
├── shared_lib/                    # Shared library infrastructure
│   ├── src/shared/                # Common modules
│   │   ├── __init__.py            # Package initialization
│   │   ├── config.py              # Unified configuration system
│   │   ├── logging.py             # Structured logging with structlog
│   │   ├── errors.py              # Typed error handling
│   │   ├── discord_utils.py       # Discord utilities and base classes
│   │   ├── security.py            # Security utilities and validation
│   │   └── database.py            # Database operations with aiosqlite
│   └── pyproject.toml             # Shared library dependencies
├── bin/                           # Management and utility scripts
│   └── python-bots                # Main management script
├── .env.example                   # Environment configuration template
├── config.example.json            # Alternative JSON configuration
├── pyproject.toml                 # Workspace configuration
└── uv.lock                        # Dependency lock file
```

### Key Design Principles

* **Domain-Driven Design** – Each bot owns its domain logic completely
* **Microservice Architecture** – Independent deployment and scaling capability
* **Independent Architecture** – Each bot is completely self-contained with isolated dependencies
* **Modern Python** – Full type hints, async/await patterns, and pydantic configuration
* **uv Package Management** – Fast, reliable dependency resolution and virtual environments
* **Observability First** – Structured logging, metrics, and error tracking from day one
* **Performance Optimized** – Async operations with intelligent caching and resource management

### Technology Stack

- **Python 3.12+** - Modern async/await syntax and performance improvements
- **discord.py 2.5+** - Latest Discord API features and slash commands
- **pydantic 2.0+** - Type-safe configuration and data validation
- **structlog** - Structured logging with JSON output support
- **httpx** - Modern async HTTP client for API calls
- **aiosqlite** - Async SQLite database operations
- **uv** - Fast Python package and project management
- **ruff** - Fast Python linting and formatting
- **mypy** - Static type checking

---

## ⚙️ Configuration Options

### Environment Variables

```bash
# Global Settings (applies to all bots unless overridden)
COMMAND_PREFIX=!                 # Default command prefix
LOG_LEVEL=info                   # Logging level (debug, info, warn, error)
JSON_LOGGING=false              # Enable JSON structured logging
DEBUG=false                     # Enable debug mode
GUILD_ID=your_guild_id          # Default guild for slash commands

# Performance & Timeouts
SHUTDOWN_TIMEOUT=30             # Graceful shutdown timeout (seconds)
REQUEST_TIMEOUT=30              # HTTP request timeout (seconds)
MAX_RETRIES=3                   # Maximum retry attempts for failed requests

# Bot-Specific Tokens (required)
CLIPPY_DISCORD_TOKEN=token      # Clippy bot token
MUSIC_DISCORD_TOKEN=token       # Music bot token
MTG_DISCORD_TOKEN=token         # MTG Card bot token

# Bot-Specific Overrides (optional)
CLIPPY_GUILD_ID=guild_id        # Override guild for Clippy
MUSIC_GUILD_ID=guild_id         # Override guild for Music bot
MTG_GUILD_ID=guild_id           # Override guild for MTG bot

# Cache Configuration (MTG bot)
CACHE_TTL=3600                  # Cache time-to-live in seconds
CACHE_SIZE=1000                 # Maximum cached items

# Music Bot Configuration
MUSIC_DATABASE_URL=music.db     # Database file path
MAX_QUEUE_SIZE=100              # Maximum songs in queue
INACTIVITY_TIMEOUT=300          # Auto-disconnect timeout (seconds)
VOLUME_LEVEL=0.5                # Default volume (0.0-1.0)

# Clippy Bot Configuration
RANDOM_RESPONSES=true           # Enable random responses
RANDOM_INTERVAL=2700            # Random message interval (seconds)
RANDOM_MESSAGE_DELAY=3          # Delay before random messages (seconds)
```

### JSON Configuration (Alternative)

You can also use `config.json` for configuration:

```json
{
  "clippy": {
    "bot_name": "Clippy Bot",
    "CLIPPY_DISCORD_TOKEN": "your_token_here",
    "command_prefix": "!",
    "guild_id": "your_guild_id",
    "random_responses": true
  },
  "music": {
    "bot_name": "Music Bot", 
    "MUSIC_DISCORD_TOKEN": "your_token_here",
    "database_url": "music.db",
    "max_queue_size": 100,
    "volume_level": 0.5
  }
}
```

---

## 🚀 Deployment Options

### Local Development
```bash
# Run with auto-restart and debug logging
./bin/python-bots dev
```

### Production Deployment

#### Option 1: Direct uv Execution
```bash
# Run individual bots in production
uv run --package clippy-bot python -m clippy
uv run --package music-bot python -m music  
uv run --package mtg-card-bot python -m mtg_card_bot
```

#### Option 2: Systemd Services (Linux)
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

#### Option 3: Docker Containers
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install uv
RUN uv sync

CMD ["uv", "run", "--package", "clippy", "python", "-m", "clippy"]
```

#### Option 4: Process Manager (PM2/Supervisor)
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

## 🛠️ Development Guide

### Setting Up Development Environment

```bash
# 1. Clone and install dependencies
git clone https://github.com/dunamismax/python-bots.git
cd python-bots
uv sync

# 2. Set up development environment  
./bin/python-bots setup

# 3. Configure environment
cp env.example .env
# Edit .env with your bot tokens

# 4. Install additional tools for music bot
pip install yt-dlp  # YouTube integration
# Install FFmpeg for your platform

# 5. Start development
./bin/python-bots dev
```

### Code Quality Tools

```bash
# Format code
uv run ruff format .

# Lint code  
uv run ruff check .

# Type checking
uv run mypy bots/

# Run tests
uv run pytest

# All quality checks
./bin/python-bots quality
```

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