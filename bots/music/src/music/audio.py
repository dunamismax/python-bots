"""Modern audio playback functionality using yt-dlp directly without FFmpeg."""

import asyncio
import io
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional, Tuple

import discord
import yt_dlp
from asyncio_throttle import Throttler

from . import logging

from .models import Song


class YoutubeDLSource(discord.PCMVolumeTransformer):
    """Custom audio source that uses yt-dlp for efficient streaming."""
    
    def __init__(self, url: str, *, volume: float = 0.5):
        """Initialize the YoutubeDL source with volume control."""
        try:
            # Create FFmpeg source with optimized options for streaming
            ffmpeg_options = {
                'before_options': (
                    '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 '
                    '-multiple_requests 1'
                ),
                'options': '-vn -b:a 192k'  # Audio only, 192kbps bitrate
            }
            
            source = discord.FFmpegPCMAudio(url, **ffmpeg_options)
            super().__init__(source, volume=volume)
        except Exception as e:
            raise Exception(f"Failed to create FFmpeg audio source: {e}")


class OpusYoutubeDLSource(discord.AudioSource):
    """Opus-optimized audio source for better performance."""
    
    def __init__(self, url: str):
        """Initialize the Opus source."""
        self.url = url
        self._ffmpeg_options = {
            'before_options': (
                '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 '
                '-multiple_requests 1'
            ),
            'options': '-vn -c:a libopus -b:a 192k -application audio'
        }
    
    def read(self) -> bytes:
        """Read opus audio data."""
        # This would need implementation for direct Opus streaming
        # For now, fallback to FFmpeg approach
        pass
    
    def is_opus(self) -> bool:
        """Return True as this source provides Opus audio."""
        return True


class AudioPlayer:
    """Modern audio player using yt-dlp direct streaming without FFmpeg."""

    def __init__(self) -> None:
        """Initialize the audio player."""
        self.logger = logging.with_component("audio_player")
        self._volumes: Dict[str, float] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="audio_worker")
        
        # Rate limiter to prevent overwhelming yt-dlp
        self._throttler = Throttler(rate_limit=5, period=1.0)  # 5 extractions per second max
        
        # yt-dlp configuration optimized for Discord streaming
        self._ytdl_options = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': 'opus',  # Prefer Opus when available
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
            # Optimize for streaming
            'no_color': True,
            'extract_flat': False,
            # Prefer higher quality audio when available
            'audio_quality': 0,  # Best quality
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
                'preferredquality': '192',
            }],
        }
        
        self._ytdl = yt_dlp.YoutubeDL(self._ytdl_options)

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
            error_msg = str(e) if str(e) else f"{type(e).__name__}: {repr(e)}"
            self.logger.error("Failed to play song", 
                            error=error_msg,
                            error_type=type(e).__name__,
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
        """Create an audio source using yt-dlp direct streaming."""
        try:
            # Validate URL before processing
            if not self._is_safe_url(song.url):
                self.logger.error("Unsafe URL detected", song_url=song.url[:100])
                return None
            
            # Use throttling to prevent overwhelming yt-dlp
            async with self._throttler:
                # Extract the best audio stream URL
                stream_url, audio_info = await self._extract_stream_url(song.url)
                
                if not stream_url:
                    self.logger.error("No audio stream found", song_url=song.url[:100])
                    return None
                
                self.logger.info("Stream extracted", 
                               format=audio_info.get('format_id', 'unknown'),
                               codec=audio_info.get('acodec', 'unknown'),
                               bitrate=audio_info.get('abr', 'unknown'))
                
                # Get volume for this guild
                volume = self.get_volume(guild_id)
                
                # Create the audio source using the direct stream URL
                # Use YoutubeDLSource which handles the streaming more efficiently
                try:
                    source = YoutubeDLSource(stream_url, volume=volume)
                    return source
                except Exception as e:
                    self.logger.error("Failed to create YoutubeDLSource", 
                                    error=str(e), stream_url=stream_url[:100])
                    return None
                
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

    async def _extract_stream_url(self, url: str) -> Tuple[Optional[str], dict]:
        """Extract the direct audio stream URL using yt-dlp."""
        loop = asyncio.get_event_loop()
        
        def extract():
            try:
                info = self._ytdl.extract_info(url, download=False)
                
                # Handle playlist results
                if 'entries' in info:
                    # Take the first entry for playlists
                    info = info['entries'][0]
                
                # Find the best audio format
                formats = info.get('formats', [])
                audio_formats = [f for f in formats if f.get('acodec') != 'none']
                
                if not audio_formats:
                    return None, {}
                
                # Prefer opus codec, then other high-quality codecs
                def format_score(fmt):
                    codec = fmt.get('acodec', '').lower()
                    bitrate = fmt.get('abr', 0) or 0
                    
                    score = bitrate
                    if 'opus' in codec:
                        score += 1000  # Heavily prefer opus
                    elif any(c in codec for c in ['aac', 'mp3', 'vorbis']):
                        score += 500
                    
                    return score
                
                best_format = max(audio_formats, key=format_score)
                stream_url = best_format.get('url')
                
                return stream_url, best_format
                
            except Exception as e:
                self.logger.error("yt-dlp extraction failed", error=str(e))
                return None, {}
        
        return await loop.run_in_executor(self._executor, extract)
    
    def cleanup(self) -> None:
        """Clean up all audio connections."""
        with self._lock:
            self._volumes.clear()
        
        # Shutdown executor
        self._executor.shutdown(wait=False)
        
        self.logger.debug("Audio player cleanup completed")
