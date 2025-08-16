"""Audio playback functionality for the Music bot."""

import asyncio
import sys
import threading
from pathlib import Path
from typing import Dict, Optional

import discord

# Add shared_lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared_lib" / "src"))

from shared import logging

from .models import Song


class AudioPlayer:
    """Manages audio playback for multiple guilds."""

    def __init__(self) -> None:
        """Initialize the audio player."""
        self.logger = logging.with_component("audio_player")
        self._volumes: Dict[str, float] = {}
        self._lock = threading.RLock()

    async def play_next(self, bot, guild_id: str, voice_client: discord.VoiceClient, queue) -> None:
        """Play the next song in queue."""
        self.logger.debug("Playing next song", guild_id=guild_id)

        # Check if queue is empty
        if queue.is_empty():
            queue.set_playing(False)
            queue.set_current(None)
            self.logger.info("Queue is empty, stopping playback", guild_id=guild_id)
            return

        # Get next song
        next_song = queue.next()
        if next_song is None:
            queue.set_playing(False)
            queue.set_current(None)
            return

        # Set current song and playing state
        queue.set_current(next_song)
        queue.set_playing(True)
        queue.set_skip(False)

        self.logger.info("Playing next song", 
                        guild_id=guild_id, 
                        song=next_song.title)

        try:
            # Create audio source
            audio_source = await self._create_audio_source(next_song, guild_id)
            
            if audio_source is None:
                self.logger.error("Failed to create audio source", song=next_song.title)
                # Try next song on error
                queue.set_current(None)
                queue.set_playing(False)
                await self.play_next(bot, guild_id, voice_client, queue)
                return

            # Play the audio
            def after_playing(error):
                if error:
                    self.logger.error("Audio playback error", error=str(error))
                
                # Schedule next song in event loop
                asyncio.run_coroutine_threadsafe(
                    self._handle_song_finished(bot, guild_id, voice_client, queue),
                    bot.loop
                )

            voice_client.play(audio_source, after=after_playing)
            
        except Exception as e:
            self.logger.error("Failed to play song", 
                            error=str(e), 
                            song=next_song.title)
            # Clear current song and try next song on error
            queue.set_current(None)
            queue.set_playing(False)
            await self.play_next(bot, guild_id, voice_client, queue)

    async def _handle_song_finished(self, bot, guild_id: str, voice_client: discord.VoiceClient, queue) -> None:
        """Handle when a song finishes playing."""
        self.logger.debug("Song finished", guild_id=guild_id)
        
        # Clear current song
        queue.set_current(None)
        queue.set_playing(False)
        
        # Play next song if available and not skipped
        if not queue.should_skip():
            await self.play_next(bot, guild_id, voice_client, queue)
        else:
            # Song was skipped, reset skip flag and play next
            queue.set_skip(False)
            await self.play_next(bot, guild_id, voice_client, queue)

    async def _create_audio_source(self, song: Song, guild_id: str) -> Optional[discord.AudioSource]:
        """Create an audio source for the song."""
        try:
            # Validate URL before processing
            if not self._is_safe_url(song.url):
                self.logger.error("Unsafe URL detected", song_url=song.url[:100])
                return None
                
            # Get volume for this guild
            volume = self.get_volume(guild_id)
            
            # Use yt-dlp to stream the audio
            ytdl_opts = {
                "format": "bestaudio[ext=m4a]/bestaudio/best",
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
            }
            
            ffmpeg_options = {
                "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                "options": "-vn"
            }
            
            # Create the audio source
            source = discord.FFmpegPCMAudio(
                song.url,
                **ffmpeg_options
            )
            
            # Apply volume if not default
            if volume != 0.5:
                source = discord.PCMVolumeTransformer(source, volume=volume)
                
            return source
            
        except Exception as e:
            self.logger.error("Failed to create audio source", 
                            error=str(e), 
                            song_url=song.url[:100])
            return None

    def _is_safe_url(self, url: str) -> bool:
        """Validate that the URL is safe for audio playback."""
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            
            # Only allow HTTPS URLs
            if parsed.scheme != 'https':
                return False
                
            # Allow known safe domains for audio
            safe_domains = [
                'youtube.com', 'youtu.be', 'music.youtube.com',
                'soundcloud.com', 'spotify.com', 'bandcamp.com',
                'vimeo.com', 'twitch.tv'
            ]
            
            hostname = parsed.hostname or ""
            if not any(domain in hostname.lower() for domain in safe_domains):
                return False
                
            return True
            
        except Exception:
            return False

    def get_volume(self, guild_id: str) -> float:
        """Get the volume for a guild."""
        with self._lock:
            return self._volumes.get(guild_id, 0.5)  # Default volume

    def set_volume(self, guild_id: str, volume: float) -> None:
        """Set the volume for a guild."""
        with self._lock:
            self._volumes[guild_id] = max(0.0, min(1.0, volume))  # Clamp between 0 and 1

    def cleanup_guild(self, guild_id: str) -> None:
        """Clean up audio data for a specific guild."""
        with self._lock:
            self._volumes.pop(guild_id, None)
        self.logger.debug("Guild audio cleanup completed", guild_id=guild_id)

    def cleanup(self) -> None:
        """Clean up all audio connections."""
        with self._lock:
            self._volumes.clear()
        self.logger.debug("Audio player cleanup completed")