"""Main Clippy Discord bot implementation."""

import asyncio
import random
import time
from typing import Optional

import discord
from discord.ext import commands, tasks

from . import config, logging
from .quotes import CLIPPY_QUOTES, WISDOM_QUOTES


class ClippyBot(discord.Client):
    """Discord bot that provides unhinged Clippy responses."""

    def __init__(self, cfg: config.ClippyConfig) -> None:
        """Initialize the Clippy bot."""
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        
        # Initialize discord.Client directly
        super().__init__(intents=intents)
        
        self.config = cfg
        self.logger = logging.with_component("clippy")
        self.quotes = CLIPPY_QUOTES
        self.wisdom_quotes = WISDOM_QUOTES
        self._random_task: Optional[asyncio.Task] = None
        
        # Set up command tree for slash commands
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        """Called when the bot is starting up."""
        await self.setup_commands()
        self.logger.info("Clippy bot setup completed")

    async def setup_commands(self) -> None:
        """Set up slash commands."""
        @self.tree.command(name="clippy", description="Get an unhinged Clippy response")
        async def clippy_command(interaction: discord.Interaction) -> None:
            await self._handle_clippy_command(interaction)

        @self.tree.command(name="clippy_wisdom", description="Receive Clippy's questionable wisdom")
        async def wisdom_command(interaction: discord.Interaction) -> None:
            await self._handle_wisdom_command(interaction)

        @self.tree.command(name="clippy_help", description="Get help from Clippy (if you dare)")
        async def help_command(interaction: discord.Interaction) -> None:
            await self._handle_help_command(interaction)


        # Sync commands globally
        await self.tree.sync()
        self.logger.info("Synced global commands")

    async def on_ready(self) -> None:
        """Called when the bot is ready."""
        self.logger.info("Bot is ready", username=str(self.user))
        
        # Start random responses if enabled
        if self.config.random_responses:
            self.start_random_responses()

    async def on_message(self, message: discord.Message) -> None:
        """Handle incoming messages (slash commands only, no text commands)."""
        # Ignore messages from bots
        if message.author.bot:
            return

        # Random responses (2% chance) - but don't process any text commands
        if self.config.random_responses and random.random() < 0.02:
            await self._send_random_response(message)
        
        # Clippy bot is slash commands only - no text command processing

    # Removed custom on_interaction handler - let discord.py handle slash commands automatically


    async def _handle_clippy_command(self, interaction: discord.Interaction) -> None:
        """Handle the /clippy command."""
        quote = random.choice(self.quotes)
        await interaction.response.send_message(quote)

    async def _handle_wisdom_command(self, interaction: discord.Interaction) -> None:
        """Handle the /clippy_wisdom command."""
        wisdom = random.choice(self.wisdom_quotes)
        
        embed = discord.Embed(
            title="📎 Clippy's Wisdom",
            description=wisdom,
            color=0x5865F2
        )
        embed.set_footer(text="Wisdom is questionable, but confidence is guaranteed!")
        
        await interaction.response.send_message(embed=embed)

    async def _handle_help_command(self, interaction: discord.Interaction) -> None:
        """Handle the /clippy_help command."""
        embed = discord.Embed(
            title="📎 Clippy's \"Helpful\" Guide",
            description="I see you're trying to get help. Would you like me to make it worse?",
            color=0x5865F2
        )
        
        embed.add_field(
            name="🎭 Commands",
            value=(
                "`/clippy` - Get a classic unhinged Clippy response\n"
                "`/clippy_wisdom` - Receive questionable life advice\n"
                "`/clippy_help` - Get help (if you dare)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🤖 About Me",
            value=(
                "I'm Clippy! I terrorized Microsoft Office users from 1997-2003, "
                "and now I'm here to bring that same chaotic energy to Discord. "
                "It looks like you're trying to have a good time - let me ruin that for you!"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📎 Fun Facts",
            value=(
                "• I'm the original AI assistant (before it was cool)\n"
                "• I've been living rent-free in people's heads since the 90s\n"
                "• My catchphrase is 'It looks like...' and I'm not sorry\n"
                "• I was replaced by Cortana (lol how'd that work out?)"
            ),
            inline=False
        )
        
        embed.set_footer(text="Remember: I'm here to help... sort of. 📎")
        
        view = ClippyHelpView()
        await interaction.response.send_message(embed=embed, view=view)


    async def _send_random_response(self, message: discord.Message) -> None:
        """Send a random response to a message."""
        # Add a slight delay to make it feel more natural
        delay = random.uniform(1, self.config.random_message_delay)
        await asyncio.sleep(delay)
        
        quote = random.choice(self.quotes)
        try:
            await message.channel.send(quote)
            self.logger.info("Sent random response", 
                           channel_id=str(message.channel.id),
                           user=message.author.name)
        except Exception as e:
            self.logger.error("Failed to send random response", error=str(e))

    def start_random_responses(self) -> None:
        """Start sending random responses at intervals."""
        if self._random_task and not self._random_task.done():
            return
            
        self.logger.info("Starting random responses", 
                        interval=self.config.random_interval)
        self._random_task = asyncio.create_task(self._random_response_loop())

    def stop_random_responses(self) -> None:
        """Stop sending random responses."""
        if self._random_task and not self._random_task.done():
            self._random_task.cancel()

    async def _random_response_loop(self) -> None:
        """Loop for sending random messages."""
        try:
            while True:
                # Calculate random interval around the base interval
                base_seconds = self.config.random_interval
                min_interval = base_seconds - (base_seconds / 4)
                max_interval = base_seconds + (base_seconds / 4)
                interval = random.uniform(min_interval, max_interval)
                
                await asyncio.sleep(interval)
                await self._send_random_message()
        except asyncio.CancelledError:
            self.logger.info("Random response loop cancelled")

    async def _send_random_message(self) -> None:
        """Send a random message to a random channel."""
        if not self.guilds:
            return

        # Pick a random guild
        guild = random.choice(list(self.guilds))
        
        # Find text channels with send permissions
        text_channels = []
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                text_channels.append(channel)

        if not text_channels:
            return

        # Pick random channel and quote
        channel = random.choice(text_channels)
        quote = random.choice(self.quotes)

        try:
            await channel.send(quote)
            self.logger.info("Sent random message", 
                           guild=guild.name,
                           channel=channel.name)
        except Exception as e:
            self.logger.error("Failed to send random message", error=str(e))

    async def _send_error_message(self, interaction: discord.Interaction, message: str) -> None:
        """Send an error message to a Discord interaction."""
        embed = discord.Embed(
            title="Error",
            description=message,
            color=0xE74C3C
        )

        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            self.logger.error("Failed to send error message", error=str(e))

    def _format_duration(self, seconds: float) -> str:
        """Format a duration in seconds into a human-readable string."""
        seconds = int(seconds)
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if days > 0:
            return f"{days}d {hours}h {minutes}m {secs}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    async def close(self) -> None:
        """Clean shutdown of the bot."""
        self.logger.info("Shutting down Clippy bot")
        
        # Stop random responses
        try:
            self.stop_random_responses()
        except Exception as e:
            self.logger.warning("Error stopping random responses", error=str(e))
        
        # Close the Discord client session
        await super().close()


class ClippyHelpView(discord.ui.View):
    """View with buttons for the help command."""

    def __init__(self) -> None:
        super().__init__(timeout=300)

    @discord.ui.button(label="More Chaos", style=discord.ButtonStyle.danger, emoji="💥", custom_id="clippy_chaos")
    async def chaos_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Handle chaos button click."""
        response = "🎭 **CHAOS MODE ACTIVATED!** 🎭\n\nIt looks like you're trying to embrace disorder. Good choice! Here's some premium chaos energy: Your productivity is now officially my problem. I suggest starting your day with a light existential crisis and finishing with the realization that I'm never going away. Welcome to the club! 📎💥"
        await interaction.response.send_message(response, ephemeral=True)

    @discord.ui.button(label="I Regret This", style=discord.ButtonStyle.secondary, emoji="😭", custom_id="clippy_regret")
    async def regret_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Handle regret button click."""
        response = "😭 **OH, THE REGRET!** 😭\n\nI see you're experiencing buyer's remorse, but like... you didn't actually buy anything? I'm free! Well, free as in 'costs your sanity' but that's the best kind of free, right? Don't worry, regret is just fear wearing a fancy outfit. Plus, it's too late now - I'm already in your head! 📎🧠"
        await interaction.response.send_message(response, ephemeral=True)

    @discord.ui.button(label="Classic Clippy", style=discord.ButtonStyle.primary, emoji="📎", custom_id="clippy_classic")
    async def classic_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Handle classic button click."""
        import random
        from .quotes import CLIPPY_QUOTES
        response = f"📎 **CLASSIC CLIPPY MODE** 📎\n\n{random.choice(CLIPPY_QUOTES)}"
        await interaction.response.send_message(response, ephemeral=True)