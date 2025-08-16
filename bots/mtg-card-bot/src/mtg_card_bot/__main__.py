"""Main entry point for the MTG Card Bot."""

import asyncio
import signal
import sys
from pathlib import Path

from . import config, logging

from .bot import MTGCardBot


async def main() -> None:
    """Main function to run the MTG Card Bot."""
    # Load environment from .env file if it exists
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

    logger.info("Starting MTG Card Bot", version="2.0.0")

    # Create and start the bot
    bot = MTGCardBot(cfg)

    # Set up signal handlers for graceful shutdown
    def signal_handler(signum: int, frame) -> None:
        logger.info("Received shutdown signal", signal=signum)
        asyncio.create_task(bot.close())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await bot.start()
    except Exception as e:
        logger.error("Failed to start bot", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
