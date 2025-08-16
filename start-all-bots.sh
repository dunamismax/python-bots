#!/bin/bash

# Discord Bots Startup Script
# Syncs dependencies and starts all three bots concurrently

set -e

echo "🤖 Starting Python Discord Bots..."
echo "================================="

# Load environment variables from .env file if it exists
if [[ -f .env ]]; then
    echo "📋 Loading environment variables from .env file..."
    set -a  # automatically export all variables
    source .env
    set +a  # turn off automatic export
else
    echo "⚠️  No .env file found. Using environment variables only."
fi

# Check for required environment variables
missing_vars=()
if [[ -z "${CLIPPY_DISCORD_TOKEN}" ]]; then
    missing_vars+=("CLIPPY_DISCORD_TOKEN")
fi
if [[ -z "${MTG_DISCORD_TOKEN}" ]]; then
    missing_vars+=("MTG_DISCORD_TOKEN")
fi
if [[ -z "${MUSIC_DISCORD_TOKEN}" ]]; then
    missing_vars+=("MUSIC_DISCORD_TOKEN")
fi

if [[ ${#missing_vars[@]} -gt 0 ]]; then
    echo "❌ Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please set these variables or create a .env file with:"
    echo "CLIPPY_DISCORD_TOKEN=your_token_here"
    echo "MTG_DISCORD_TOKEN=your_token_here"
    echo "MUSIC_DISCORD_TOKEN=your_token_here"
    exit 1
fi

echo "📦 Syncing dependencies..."
uv sync --all-extras

echo ""
echo "🚀 Starting all bots..."
echo "Press Ctrl+C to stop all bots"
echo ""

# Start all three bots in parallel
(
    echo "🔗 Starting Clippy Bot..."
    uv run --package clippy-bot python -m clippy 2>&1 | sed 's/^/[CLIPPY] /'
) &
CLIPPY_PID=$!

(
    echo "🃏 Starting MTG Card Bot..."
    uv run --package mtg-card-bot python -m mtg_card_bot 2>&1 | sed 's/^/[MTG] /'
) &
MTG_PID=$!

(
    echo "🎵 Starting Music Bot..."
    uv run --package music-bot python -m music 2>&1 | sed 's/^/[MUSIC] /'
) &
MUSIC_PID=$!

# Store PIDs for cleanup
echo $CLIPPY_PID > .clippy.pid
echo $MTG_PID > .mtg.pid
echo $MUSIC_PID > .music.pid

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all bots..."
    
    # Try to kill processes using stored PIDs first
    if [[ -f .clippy.pid ]]; then
        CLIPPY_PID=$(cat .clippy.pid)
        if kill -0 $CLIPPY_PID 2>/dev/null; then
            echo "   Stopping Clippy Bot (PID: $CLIPPY_PID)..."
            kill -TERM $CLIPPY_PID 2>/dev/null || true
            sleep 1
            kill -0 $CLIPPY_PID 2>/dev/null && kill -KILL $CLIPPY_PID 2>/dev/null || true
        fi
    fi
    
    if [[ -f .mtg.pid ]]; then
        MTG_PID=$(cat .mtg.pid)
        if kill -0 $MTG_PID 2>/dev/null; then
            echo "   Stopping MTG Card Bot (PID: $MTG_PID)..."
            kill -TERM $MTG_PID 2>/dev/null || true
            sleep 1
            kill -0 $MTG_PID 2>/dev/null && kill -KILL $MTG_PID 2>/dev/null || true
        fi
    fi
    
    if [[ -f .music.pid ]]; then
        MUSIC_PID=$(cat .music.pid)
        if kill -0 $MUSIC_PID 2>/dev/null; then
            echo "   Stopping Music Bot (PID: $MUSIC_PID)..."
            kill -TERM $MUSIC_PID 2>/dev/null || true
            sleep 1
            kill -0 $MUSIC_PID 2>/dev/null && kill -KILL $MUSIC_PID 2>/dev/null || true
        fi
    fi
    
    # Clean up PID files
    rm -f .clippy.pid .mtg.pid .music.pid
    
    echo "✅ All bots stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "✅ All bots started successfully!"
echo "   - Clippy Bot (PID: $CLIPPY_PID)"
echo "   - MTG Card Bot (PID: $MTG_PID)"
echo "   - Music Bot (PID: $MUSIC_PID)"
echo ""
echo "Logs are prefixed with [BOT_NAME]"
echo "Press Ctrl+C to stop all bots"

# Wait for all background processes
wait