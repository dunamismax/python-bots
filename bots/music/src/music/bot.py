"""Main Music Discord bot implementation."""

import asyncio
import sys
import time
from typing import Optional

import discord
from discord.ext import commands

from . import config, logging

from .audio import AudioPlayer
from .extractor import AudioExtractor
from .queue import QueueManager





class MusicBot(commands.Bot):
    """Discord bot for music streaming with yt-dlp integration."""

    def __init__(self, cfg: config.MusicConfig) -> None:
        """Initialize the Music bot."""
        # Override command prefix for music bot (slash commands only)
        cfg.command_prefix = "/music_disabled"
        
        # Enable voice intents and ensure all necessary permissions
        intents = discord.Intents.default()
        intents.voice_states = True
        intents.guilds = True
        intents.message_content = True
        intents.guild_messages = True
        
        super().__init__(command_prefix=cfg.command_prefix, intents=intents)
        self.config = cfg
        
        self.logger = logging.with_component("music")
        
        # Initialize music components
        self.queue_manager = QueueManager()
        self.audio_player = AudioPlayer()
        self.audio_extractor = AudioExtractor()
        
        # Store database connection if configured
        self.database: Optional[object] = None  # TODO: Implement database
        
        # Track voice connections
        self.voice_connections: dict[str, discord.VoiceClient] = {}

    async def start(self) -> None:
        token = getattr(self.config, "token", None) or getattr(self.config, "discord_token", "")
        await super().start(token)

    async def setup_hook(self) -> None:
        """Called when the bot is starting up."""
        # Load Opus for voice connections
        if not discord.opus.is_loaded():
            try:
                discord.opus.load_opus('opus')
                self.logger.info("Opus loaded successfully")
            except Exception as e:
                self.logger.warning(f"Could not load opus library: {e}")
                # Try to load opus with different names and paths
                opus_paths = [
                    '/opt/homebrew/lib/libopus.dylib',  # macOS Homebrew path
                    '/usr/local/lib/libopus.dylib',     # macOS alternative path
                    'libopus.so.0',                     # Linux
                    'libopus.0.dylib',                  # macOS
                    'opus.dll'                          # Windows
                ]
                
                for opus_path in opus_paths:
                    try:
                        discord.opus.load_opus(opus_path)
                        self.logger.info(f"Opus loaded successfully with {opus_path}")
                        break
                    except:
                        continue
                else:
                    self.logger.error("Failed to load any opus library - audio may not work")
        else:
            self.logger.info("Opus already loaded")
            
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

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        """Handle voice state updates to manage bot disconnections."""
        guild_id = str(member.guild.id)
        
        # Handle the bot's own voice state changes
        if member.id == self.user.id:
            # Bot was disconnected from voice channel
            if before.channel is not None and after.channel is None:
                self.logger.info("Bot was disconnected from voice channel", 
                               guild_id=guild_id, 
                               channel_name=before.channel.name)
                
                # Clean up voice connection and queue
                if guild_id in self.voice_connections:
                    del self.voice_connections[guild_id]
                    
                # Clear the queue for this guild
                self.queue_manager.clear_queue(guild_id)
                
            # Bot was moved to a different channel
            elif before.channel != after.channel and after.channel is not None:
                self.logger.info("Bot was moved to different voice channel", 
                               guild_id=guild_id,
                               old_channel=before.channel.name if before.channel else "None",
                               new_channel=after.channel.name)
        
        # Handle other users leaving/joining when bot is in voice
        elif guild_id in self.voice_connections:
            voice_client = self.voice_connections[guild_id]
            
            # Check if bot is now alone in the voice channel
            if voice_client.channel:
                # Count non-bot members in the channel
                human_members = [m for m in voice_client.channel.members if not m.bot]
                
                if len(human_members) == 0:
                    self.logger.info("Bot is now alone in voice channel, scheduling disconnect", 
                                   guild_id=guild_id, 
                                   channel_name=voice_client.channel.name)
                    
                    # Schedule disconnect after 30 seconds if still alone
                    asyncio.create_task(self._auto_disconnect_if_alone(guild_id, 30))

    async def _auto_disconnect_if_alone(self, guild_id: str, delay_seconds: int) -> None:
        """Automatically disconnect from voice if alone after a delay."""
        await asyncio.sleep(delay_seconds)
        
        # Check if bot is still connected and still alone
        if guild_id not in self.voice_connections:
            return
            
        voice_client = self.voice_connections[guild_id]
        if not voice_client.is_connected() or not voice_client.channel:
            return
            
        # Count non-bot members
        human_members = [m for m in voice_client.channel.members if not m.bot]
        
        if len(human_members) == 0:
            self.logger.info("Auto-disconnecting due to being alone in voice channel", 
                           guild_id=guild_id, 
                           channel_name=voice_client.channel.name)
            
            try:
                # Stop playback and disconnect
                if voice_client.is_playing():
                    voice_client.stop()
                await voice_client.disconnect()
                del self.voice_connections[guild_id]
                
                # Clear queue
                self.queue_manager.clear_queue(guild_id)
                
            except Exception as e:
                self.logger.error("Error during auto-disconnect", 
                                guild_id=guild_id, error=str(e))

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
        """Get existing voice connection or create a new one with robust error handling."""
        if guild_id in self.voice_connections:
            voice_client = self.voice_connections[guild_id]
            if voice_client.channel == channel and voice_client.is_connected():
                return voice_client
            # Different channel or disconnected, disconnect and reconnect
            try:
                await voice_client.disconnect(force=True)
            except Exception as e:
                self.logger.warning("Error disconnecting voice client", error=str(e))
            finally:
                if guild_id in self.voice_connections:
                    del self.voice_connections[guild_id]

        # Check bot permissions before attempting connection
        bot_member = channel.guild.get_member(self.user.id)
        if not bot_member:
            raise Exception("Bot is not a member of this guild")
            
        permissions = channel.permissions_for(bot_member)
        if not permissions.connect:
            raise Exception("Bot lacks 'Connect' permission for this voice channel")
        if not permissions.speak:
            raise Exception("Bot lacks 'Speak' permission for this voice channel")

        # Create new voice connection with retry logic
        for attempt in range(3):
            try:
                self.logger.info(f"Attempting voice connection (attempt {attempt + 1}/3)", 
                               channel_name=channel.name, guild_id=guild_id)
                
                voice_client = await asyncio.wait_for(
                    channel.connect(reconnect=False, timeout=60.0), 
                    timeout=45.0
                )
                
                self.voice_connections[guild_id] = voice_client
                self.logger.info("Voice connection established successfully", 
                               channel_name=channel.name, guild_id=guild_id)
                return voice_client
                
            except asyncio.TimeoutError:
                self.logger.warning(f"Voice connection attempt {attempt + 1} timed out")
                if attempt == 2:  # Last attempt
                    raise Exception("Voice connection timed out after 3 attempts")
                await asyncio.sleep(2)  # Wait before retry
                
            except discord.errors.ClientException as e:
                if "already connected" in str(e).lower():
                    # Handle edge case where Discord thinks we're still connected
                    existing_voice = discord.utils.get(self.voice_clients, guild=channel.guild)
                    if existing_voice:
                        await existing_voice.disconnect(force=True)
                    continue
                else:
                    self.logger.error(f"Discord client error on attempt {attempt + 1}", error=str(e))
                    if attempt == 2:
                        raise Exception(f"Failed to connect to voice channel: {str(e)}")
                    await asyncio.sleep(2)
                    
            except Exception as e:
                self.logger.error(f"Voice connection attempt {attempt + 1} failed", error=str(e))
                if attempt == 2:  # Last attempt
                    raise Exception(f"Failed to connect to voice channel after 3 attempts: {str(e)}")
                await asyncio.sleep(2)  # Wait before retry

        raise Exception("Unexpected error in voice connection logic")

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
        
        # Disconnect from all voice channels with force
        for guild_id, voice_client in list(self.voice_connections.items()):
            try:
                if voice_client.is_connected():
                    # Stop any playing audio first
                    if voice_client.is_playing():
                        voice_client.stop()
                    # Force disconnect
                    await voice_client.disconnect(force=True)
                    self.logger.info("Disconnected from voice channel", guild_id=guild_id)
            except Exception as e:
                self.logger.error("Error disconnecting from voice channel", 
                                guild_id=guild_id, error=str(e))
        
        self.voice_connections.clear()
        
        # Clear all queues
        try:
            for guild_id in list(self.queue_manager._queues.keys()):
                self.queue_manager.clear_queue(guild_id)
        except Exception as e:
            self.logger.warning("Error clearing queues", error=str(e))
        
        # Clean up components
        try:
            await self.audio_extractor.close()
        except Exception as e:
            self.logger.warning("Error closing audio extractor", error=str(e))
            
        try:
            self.audio_player.cleanup()
        except Exception as e:
            self.logger.warning("Error cleaning up audio player", error=str(e))
        
        # Close the Discord client session
        await super().close()
