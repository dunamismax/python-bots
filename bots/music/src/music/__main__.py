"""Entry point for the Music Discord bot."""

import asyncio
import signal
import sys
from pathlib import Path

from . import config, logging
from .bot import MusicBot




async def main() -> None:
    """Main entry point for the Music bot."""
    # Load environment variables from .env file
    env_file = Path(".env")
    if env_file.exists():
        config.load_env_file(env_file)

    # Load configuration
    try:
        cfg = config.load_config()
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
    logging.initialize_logger(cfg.log_level, cfg.json_logging)
    logger = logging.with_component("main")

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
        await bot.start(cfg.discord_token)
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