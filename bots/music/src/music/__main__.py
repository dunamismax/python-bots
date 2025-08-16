"""Entry point for the Music Discord bot."""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

# Add shared_lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared_lib" / "src"))

from shared import config, logging as shared_logging

from .bot import MusicBot


def load_env_file() -> None:
    """Load environment variables from .env file if it exists."""
    env_file = Path(".env")
    if not env_file.exists():
        return

    try:
        with env_file.open() as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or (
                        value.startswith("'") and value.endswith("'")
                    ):
                        value = value[1:-1]
                    
                    # Only set if not already set by system environment
                    if key not in os.environ:
                        os.environ[key] = value
    except Exception as e:
        print(f"Warning: failed to load .env file: {e}")


async def main() -> None:
    """Main entry point for the Music bot."""
    # Load environment variables from .env file
    load_env_file()

    # Load configuration
    try:
        cfg = config.load_config(config.BotType.MUSIC)
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Validate configuration
    try:
        cfg.validate_config()
    except Exception as e:
        print(f"Invalid configuration: {e}")
        sys.exit(1)

    # Initialize logging
    shared_logging.initialize_logger(cfg.log_level, cfg.json_logging)
    logger = shared_logging.with_component("main")

    logger.info("Starting Music Bot", version="1.0.0")

    # Create and start bot
    bot = MusicBot(cfg)
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum: int, frame) -> None:
        logger.info("Received shutdown signal", signal=signum)
        asyncio.create_task(bot.close())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await bot.start()
    except Exception as e:
        logger.error("Failed to start Music bot", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMusic Bot stopped by user")
    except Exception as e:
        print(f"Music Bot crashed: {e}")
        sys.exit(1)