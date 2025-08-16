"""Main Music Discord bot implementation."""

import asyncio
import sys
import time
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands

from . import config, logging

from .audio import AudioPlayer
from .extractor import AudioExtractor
from .queue import QueueManager


class MusicBot(discord.Client):
    """Discord bot for music streaming with yt-dlp integration."""

    def __init__(self, cfg: config.MusicConfig) -> None:
        """Initialize the Music bot."""
        # Enable voice intents
        intents = discord.Intents.default()
        intents.voice_states = True
        intents.guilds = True
        intents.message_content = True
        
        # Initialize discord.Client directly
        super().__init__(intents=intents)
        
        self.config = cfg
        self.logger = logging.with_component("music")
        
        # Set up command tree for slash commands
        self.tree = discord.app_commands.CommandTree(self)
        
        # Initialize music components
        self.queue_manager = QueueManager()
        self.audio_player = AudioPlayer()
        self.audio_extractor = AudioExtractor()
        
        # Store database connection if configured
        self.database: Optional[object] = None  # TODO: Implement database
        
        # Track voice connections
        self.voice_connections: dict[str, discord.VoiceClient] = {}

    async def setup_hook(self) -> None:
        """Called when the bot is starting up."""
        await self.setup_commands()
        self.logger.info("Music bot setup completed")

    async def setup_commands(self) -> None:
        """Set up slash commands."""
        
        # Basic playback commands
        @self.tree.command(name="play", description="Play music from YouTube (auto-joins your voice channel)")
        async def play_command(interaction: discord.Interaction, query: str) -> None:
            await self._handle_play_command(interaction, query)

        @self.tree.command(name="pause", description="Pause the current song")
        async def pause_command(interaction: discord.Interaction) -> None:
            await self._handle_pause_command(interaction)

        @self.tree.command(name="resume", description="Resume playback")
        async def resume_command(interaction: discord.Interaction) -> None:
            await self._handle_resume_command(interaction)

        @self.tree.command(name="skip", description="Skip the current song")
        async def skip_command(interaction: discord.Interaction) -> None:
            await self._handle_skip_command(interaction)

        @self.tree.command(name="stop", description="Stop music and disconnect")
        async def stop_command(interaction: discord.Interaction) -> None:
            await self._handle_stop_command(interaction)

        @self.tree.command(name="queue", description="Show the music queue")
        async def queue_command(interaction: discord.Interaction) -> None:
            await self._handle_queue_command(interaction)

        @self.tree.command(name="volume", description="Set or show volume level")
        async def volume_command(interaction: discord.Interaction, level: Optional[int] = None) -> None:
            await self._handle_volume_command(interaction, level)

        # Sync commands globally
        await self.tree.sync()
        self.logger.info("Synced global commands")

    async def on_ready(self) -> None:
        """Called when the bot is ready."""
        self.logger.info("Bot is ready", username=str(self.user))

    async def on_message(self, message: discord.Message) -> None:
        """Handle incoming messages (music bot only uses slash commands)."""
        if message.author.bot:
            return
        
        # Music bot explicitly ignores text commands
        if message.content.startswith("!"):
            self.logger.debug("Ignoring text command", content=message.content[:20])

    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ) -> None:
        """Handle voice state changes for auto-leave functionality."""
        # Disable auto-leave functionality for now due to connection issues
        # The bot will stay in voice channels until manually disconnected
        return
            
    async def _check_auto_leave(self, guild_id: str, bot_channel: discord.VoiceChannel) -> None:
        """Check if the bot should automatically leave the voice channel."""
        # Add a small delay to avoid immediate reactions to voice state changes
        await asyncio.sleep(2.0)
        
        # Count non-bot members in the voice channel
        human_members = [member for member in bot_channel.members if not member.bot]
        
        self.logger.info("Checking auto-leave", 
                       guild_id=guild_id, 
                       channel=bot_channel.name,
                       human_members=len(human_members))
        
        if len(human_members) == 0:
            self.logger.info("Starting auto-leave timer - no human members", 
                           guild_id=guild_id, 
                           channel=bot_channel.name,
                           timeout_minutes=self.config.inactivity_timeout/60)
            
            # Create a background task for the auto-leave timer
            asyncio.create_task(self._auto_leave_timer(guild_id, bot_channel))
            
    async def _auto_leave_timer(self, guild_id: str, bot_channel: discord.VoiceChannel) -> None:
        """Timer task for auto-leaving voice channel."""
        try:
            # Wait for the inactivity timeout
            await asyncio.sleep(self.config.inactivity_timeout)
            
            # Double-check that no one has joined during the timeout and bot is still connected
            if guild_id not in self.voice_connections:
                return
                
            voice_client = self.voice_connections[guild_id]
            current_channel = voice_client.channel
            human_members = [member for member in current_channel.members if not member.bot]
            
            if len(human_members) == 0:
                self.logger.info("Auto-leaving voice channel after timeout", 
                               guild_id=guild_id, 
                               channel=current_channel.name)
                
                if voice_client.is_playing():
                    voice_client.stop()
                await voice_client.disconnect()
                del self.voice_connections[guild_id]
                self.queue_manager.clear_queue(guild_id)
                
            else:
                self.logger.info("Auto-leave cancelled - users rejoined", 
                               guild_id=guild_id,
                               human_members=len(human_members))
                
        except Exception as e:
            self.logger.error("Error during auto-leave timer", 
                            guild_id=guild_id, 
                            error=str(e))

    async def _handle_play_command(self, interaction: discord.Interaction, query: str) -> None:
        """Handle the /play slash command."""
        start_time = time.time()
        user_id = str(interaction.user.id)
        username = interaction.user.display_name
        guild_id = str(interaction.guild_id) if interaction.guild_id else ""

        # Validate input
        if not query or len(query) > 500:
            await interaction.response.send_message(
                "❌ Please provide a valid song name or URL (max 500 characters)",
                ephemeral=True
            )
            return

        # Check if user is in a voice channel
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message(
                "❌ You must be in a voice channel to play music! Please join a voice channel and try again.",
                ephemeral=True
            )
            return

        user_voice_channel = interaction.user.voice.channel

        # Check if bot is already in a different voice channel
        if guild_id in self.voice_connections:
            voice_client = self.voice_connections[guild_id]
            if voice_client.channel != user_voice_channel:
                await interaction.response.send_message(
                    "❌ I'm already playing music in another voice channel! Please join that channel or wait for the current session to end.",
                    ephemeral=True
                )
                return

        # Send immediate response to avoid timeout
        await interaction.response.send_message("🎵 Searching and loading your song...")

        try:
            # Extract song information
            song = await self.audio_extractor.extract_song_info(query)
            song.requester_id = user_id
            song.requester_name = username

            # Join voice channel if not already connected
            voice_client = await self._get_or_create_voice_connection(guild_id, user_voice_channel)

            # Add to queue
            queue = self.queue_manager.get_queue(guild_id)
            position = queue.add(song)

            if position == 0 and not queue.is_playing():
                response = f"🔊 Joined your voice channel and now playing: **{song.title}**"
                # Start playing immediately
                asyncio.create_task(
                    self.audio_player.play_next(self, guild_id, voice_client, queue)
                )
            else:
                response = f"🎵 Added to queue: **{song.title}**\nPosition in queue: {position + 1}"

            await interaction.edit_original_response(content=response)

        except Exception as e:
            self.logger.error("Play command failed", 
                            user_id=user_id, 
                            error=str(e))
            await interaction.edit_original_response(
                content=f"❌ Could not find or load the requested song: {str(e)}"
            )

    async def _handle_pause_command(self, interaction: discord.Interaction) -> None:
        """Handle the /pause slash command."""
        guild_id = str(interaction.guild_id) if interaction.guild_id else ""
        
        if not await self._validate_user_in_bot_voice_channel(interaction):
            return

        queue = self.queue_manager.get_queue(guild_id)
        if not queue.is_playing():
            await interaction.response.send_message(
                "❌ Nothing is currently playing",
                ephemeral=True
            )
            return

        queue.set_paused(True)
        if guild_id in self.voice_connections:
            voice_client = self.voice_connections[guild_id]
            if voice_client.is_playing():
                voice_client.pause()

        await interaction.response.send_message("⏸️ Paused the current song")

    async def _handle_resume_command(self, interaction: discord.Interaction) -> None:
        """Handle the /resume slash command."""
        guild_id = str(interaction.guild_id) if interaction.guild_id else ""
        
        if not await self._validate_user_in_bot_voice_channel(interaction):
            return

        queue = self.queue_manager.get_queue(guild_id)
        if not queue.is_paused():
            await interaction.response.send_message(
                "❌ Nothing is currently paused",
                ephemeral=True
            )
            return

        queue.set_paused(False)
        if guild_id in self.voice_connections:
            voice_client = self.voice_connections[guild_id]
            if voice_client.is_paused():
                voice_client.resume()

        await interaction.response.send_message("▶️ Resumed the current song")

    async def _handle_skip_command(self, interaction: discord.Interaction) -> None:
        """Handle the /skip slash command."""
        guild_id = str(interaction.guild_id) if interaction.guild_id else ""
        
        if not await self._validate_user_in_bot_voice_channel(interaction):
            return

        queue = self.queue_manager.get_queue(guild_id)
        if not queue.is_playing():
            await interaction.response.send_message(
                "❌ Nothing is currently playing",
                ephemeral=True
            )
            return

        current = queue.current()
        queue.skip()

        # Stop current audio to trigger next song
        if guild_id in self.voice_connections:
            voice_client = self.voice_connections[guild_id]
            if voice_client.is_playing():
                voice_client.stop()

        response = "⏭️ Skipped the current song"
        if current:
            response = f"⏭️ Skipped **{current.title}**"

        await interaction.response.send_message(response)

    async def _handle_stop_command(self, interaction: discord.Interaction) -> None:
        """Handle the /stop slash command."""
        guild_id = str(interaction.guild_id) if interaction.guild_id else ""
        
        if not await self._validate_user_in_bot_voice_channel(interaction):
            return

        # Stop audio and disconnect
        if guild_id in self.voice_connections:
            voice_client = self.voice_connections[guild_id]
            if voice_client.is_playing():
                voice_client.stop()
            await voice_client.disconnect()
            del self.voice_connections[guild_id]

        # Clear queue
        self.queue_manager.clear_queue(guild_id)

        await interaction.response.send_message("⏹️ Stopped music and disconnected from voice channel")

    async def _handle_queue_command(self, interaction: discord.Interaction) -> None:
        """Handle the /queue slash command."""
        guild_id = str(interaction.guild_id) if interaction.guild_id else ""
        queue = self.queue_manager.get_queue(guild_id)

        if queue.current() is None and queue.is_empty():
            await interaction.response.send_message(
                "📭 The queue is empty",
                ephemeral=True
            )
            return

        embed = self._build_queue_embed(queue)
        await interaction.response.send_message(embed=embed)

    async def _handle_volume_command(self, interaction: discord.Interaction, level: Optional[int]) -> None:
        """Handle the /volume slash command."""
        guild_id = str(interaction.guild_id) if interaction.guild_id else ""
        
        if not await self._validate_user_in_bot_voice_channel(interaction):
            return

        if level is None:
            # Show current volume
            volume = self.audio_player.get_volume(guild_id)
            await interaction.response.send_message(
                f"🔊 Current volume: {int(volume * 100)}%",
                ephemeral=True
            )
            return

        if level < 0 or level > 100:
            await interaction.response.send_message(
                "❌ Volume must be between 0 and 100",
                ephemeral=True
            )
            return

        volume_float = level / 100.0
        self.audio_player.set_volume(guild_id, volume_float)

        # Update volume for active voice client
        if guild_id in self.voice_connections:
            voice_client = self.voice_connections[guild_id]
            if hasattr(voice_client.source, 'volume'):
                voice_client.source.volume = volume_float

        await interaction.response.send_message(f"🔊 Volume set to {level}%")

    async def _get_or_create_voice_connection(
        self, guild_id: str, channel: discord.VoiceChannel
    ) -> discord.VoiceClient:
        """Get existing voice connection or create a new one."""
        if guild_id in self.voice_connections:
            voice_client = self.voice_connections[guild_id]
            # Check if voice client is still connected and valid
            if voice_client.is_connected() and voice_client.channel == channel:
                return voice_client
            # Different channel or disconnected, clean up and reconnect
            try:
                await voice_client.disconnect()
            except:
                pass  # Ignore errors when disconnecting
            finally:
                del self.voice_connections[guild_id]

        # Create new voice connection with extended retries and backoff
        max_retries = 5
        base_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Attempting to connect to voice channel (attempt {attempt + 1})", 
                               guild_id=guild_id, channel=channel.name)
                
                # Use longer timeout and retry with exponential backoff
                timeout = min(30.0, 10.0 + (attempt * 5.0))
                voice_client = await channel.connect(timeout=timeout, reconnect=True)
                self.voice_connections[guild_id] = voice_client
                
                self.logger.info("Successfully connected to voice channel", 
                               guild_id=guild_id, channel=channel.name)
                return voice_client
                
            except discord.errors.ConnectionClosed as e:
                if "4006" in str(e):
                    self.logger.warning(f"WebSocket 4006 error (attempt {attempt + 1}), known Discord API issue", 
                                      error=str(e))
                else:
                    self.logger.warning(f"Voice connection attempt {attempt + 1} failed", 
                                      error=str(e))
                                      
                if attempt == max_retries - 1:
                    # On final failure, provide user-friendly error
                    raise Exception("Voice connection failed due to Discord API issues (Error 4006). This is a known Discord issue affecting many bots. Please try again later.")
                    
                # Exponential backoff with jitter
                delay = base_delay * (2 ** attempt) + (attempt * 0.5)
                await asyncio.sleep(min(delay, 15.0))
                
            except Exception as e:
                self.logger.warning(f"Voice connection attempt {attempt + 1} failed", 
                                  error=str(e))
                if attempt == max_retries - 1:
                    raise
                    
                delay = base_delay * (attempt + 1)
                await asyncio.sleep(min(delay, 10.0))

    async def _validate_user_in_bot_voice_channel(self, interaction: discord.Interaction) -> bool:
        """Validate that the user is in the same voice channel as the bot."""
        guild_id = str(interaction.guild_id) if interaction.guild_id else ""
        
        # Check if user is in a voice channel
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message(
                "❌ You must be in a voice channel to use this command",
                ephemeral=True
            )
            return False

        # Check if bot is in a voice channel
        if guild_id not in self.voice_connections:
            await interaction.response.send_message(
                "❌ I'm not currently in a voice channel. Use `/play` to start playing music first",
                ephemeral=True
            )
            return False

        # Check if user and bot are in the same voice channel
        bot_voice_channel = self.voice_connections[guild_id].channel
        if interaction.user.voice.channel != bot_voice_channel:
            await interaction.response.send_message(
                "❌ You must be in the same voice channel as me to use this command",
                ephemeral=True
            )
            return False

        return True

    def _build_queue_embed(self, queue) -> discord.Embed:
        """Build an embed showing the current queue."""
        embed = discord.Embed(
            title="🎵 Music Queue",
            color=0x5865F2
        )

        if current := queue.current():
            status = "▶️ Playing"
            if queue.is_paused():
                status = "⏸️ Paused"

            embed.add_field(
                name=f"{status} Now",
                value=f"**{current.title}**\nRequested by: <@{current.requester_id}>",
                inline=False
            )

        songs = queue.get_songs()
        if songs:
            queue_list = []
            display_count = min(len(songs), 10)

            for i in range(display_count):
                song = songs[i]
                queue_list.append(f"{i + 1}. **{song.title}** - <@{song.requester_id}>")

            embed.add_field(
                name="Up Next",
                value="\n".join(queue_list),
                inline=False
            )

            if len(songs) > 10:
                embed.add_field(
                    name="",
                    value=f"... and {len(songs) - 10} more songs",
                    inline=False
                )

        return embed

    async def close(self) -> None:
        """Clean shutdown of the bot."""
        self.logger.info("Shutting down Music bot")
        
        # Disconnect from all voice channels
        voice_clients_copy = dict(self.voice_connections)
        for guild_id, voice_client in voice_clients_copy.items():
            try:
                if voice_client.is_connected():
                    await voice_client.disconnect()
            except Exception as e:
                self.logger.error("Error disconnecting from voice channel", 
                                guild_id=guild_id, error=str(e))
        
        self.voice_connections.clear()
        
        # Clean up components
        try:
            await self.audio_extractor.close()
        except Exception as e:
            self.logger.error("Error closing audio extractor", error=str(e))
        
        # Clean up audio player
        if hasattr(self.audio_player, 'cleanup'):
            try:
                self.audio_player.cleanup()
            except Exception as e:
                self.logger.error("Error cleaning up audio player", error=str(e))
        
        await super().close()