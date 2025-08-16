"""Audio playback functionality for the Music bot."""

import asyncio
import sys
import threading
from typing import Dict, Optional

import discord

from . import logging

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
            # Check if voice client is still connected
            if not voice_client.is_connected():
                self.logger.error("Voice client not connected, cannot play song", 
                                guild_id=guild_id, song=next_song.title)
                queue.set_current(None)
                queue.set_playing(False)
                return

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
            
            ffmpeg_options = {
                "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                # Apply volume filter at the encoder to avoid PCM mixing
                "options": (f"-vn -filter:a volume={volume}" if volume != 0.5 else "-vn"),
            }
            
            # Prefer Opus output from FFmpeg to reduce CPU and avoid opus lib issues
            # Use from_probe to let discord.py detect stream parameters
            source = await discord.FFmpegOpusAudio.from_probe(
                source=song.url,
                **ffmpeg_options,
            )
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
            
            # Only allow HTTP(S) URLs
            if parsed.scheme not in ('https', 'http'):
                return False
                
            # Allow known safe domains for audio
            safe_domains = [
                # Primary sites
                'youtube.com', 'youtu.be', 'music.youtube.com',
                'soundcloud.com', 'spotify.com', 'bandcamp.com',
                'vimeo.com', 'twitch.tv',
                # Common CDNs/stream hosts returned by yt-dlp
                'googlevideo.com', 'ytimg.com', 'sndcdn.com', 'scdn.co'
            ]
            
            hostname = parsed.hostname or ""
            host = hostname.lower()
            if not any(host == d or host.endswith('.' + d) for d in safe_domains):
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
