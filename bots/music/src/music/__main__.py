"""Entry point for the Music Discord bot."""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

from . import config
from . import logging as shared_logging

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
    shared_logging.initialize_logger(cfg.log_level, cfg.json_logging)
    logger = shared_logging.with_component("main")

    logger.info("Starting Music Bot", version="1.0.0")

    # Create and start bot
    bot = MusicBot(cfg)
    
    # Set up signal handlers for graceful shutdown
    shutdown_event = asyncio.Event()
    
    def signal_handler(signum: int, frame) -> None:
        logger.info("Received shutdown signal", signal=signum)
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start bot in background
        bot_task = asyncio.create_task(bot.start())
        
        # Wait for shutdown signal or bot failure
        done, pending = await asyncio.wait(
            [bot_task, asyncio.create_task(shutdown_event.wait())],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Clean shutdown
        logger.info("Shutting down Music bot...")
        await bot.close()
        
        # Check if bot task failed
        if bot_task in done and not bot_task.cancelled():
            try:
                bot_task.result()
            except Exception as e:
                logger.error("Music bot failed", error=str(e))
                sys.exit(1)
                
    except Exception as e:
        logger.error("Failed to start Music bot", error=str(e))
        await bot.close()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMusic Bot stopped by user")
    except Exception as e:
        print(f"Music Bot crashed: {e}")
        sys.exit(1)
