"""Audio extraction functionality using yt-dlp."""

import asyncio
import json
import shutil
from typing import Any, Dict, Optional

import yt_dlp

from . import errors, logging

from .models import Song


class AudioExtractor:
    """Handles extracting audio information from various sources using yt-dlp."""

    def __init__(self) -> None:
        """Initialize the audio extractor."""
        self.logger = logging.with_component("audio_extractor")
        
        # yt-dlp options optimized for Discord streaming
        self.ytdl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best[height<=?480]",
            "noplaylist": True,
            "socket_timeout": 30,
            "retries": 3,
            "fragment_retries": 3,
            "extractor_retries": 2,
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "geo_bypass": True,
            "no_check_certificate": True,
            "prefer_free_formats": True,
            "extract_flat": False,
            "quiet": True,
            "no_warnings": True,
        }

    async def extract_song_info(self, query: str) -> Song:
        """Extract song information from a URL or search query."""
        if not self._is_ytdlp_available():
            raise errors.create_error(
                errors.ErrorType.DEPENDENCY, 
                "yt-dlp is not available"
            )

        self.logger.debug("Extracting song info", query=query[:100])

        try:
            # Run yt-dlp in a thread to avoid blocking
            info = await asyncio.get_event_loop().run_in_executor(
                None, self._extract_info, query
            )
            
            if not info:
                raise errors.create_error(
                    errors.ErrorType.NOT_FOUND,
                    "No video information found"
                )

            # Create Song object from extracted info
            song = self._create_song_from_info(info)
            
            if not song.is_valid():
                raise errors.create_error(
                    errors.ErrorType.NOT_FOUND,
                    "Incomplete song information or no audio URL found"
                )

            self.logger.info("Successfully extracted song info", 
                           title=song.title, 
                           duration=song.duration)
            return song

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e).lower()
            
            # Parse specific error cases
            if "403" in error_msg or "forbidden" in error_msg:
                raise errors.create_error(
                    errors.ErrorType.PERMISSION,
                    "Unable to access video (age-restricted or region-blocked)"
                )
            elif "private video" in error_msg:
                raise errors.create_error(
                    errors.ErrorType.PERMISSION,
                    "Video is private"
                )
            elif "video unavailable" in error_msg:
                raise errors.create_error(
                    errors.ErrorType.NOT_FOUND,
                    "Video is unavailable"
                )
            elif "no video results" in error_msg:
                raise errors.create_error(
                    errors.ErrorType.NOT_FOUND,
                    "No results found for search query"
                )
            elif "sign in to confirm" in error_msg:
                raise errors.create_error(
                    errors.ErrorType.PERMISSION,
                    "Video requires sign-in (age-restricted)"
                )
            else:
                raise errors.create_error(
                    errors.ErrorType.API,
                    f"yt-dlp failed: {str(e)}"
                )

        except Exception as e:
            self.logger.error("Failed to extract song info", error=str(e))
            raise errors.create_error(
                errors.ErrorType.UNKNOWN,
                f"Failed to extract song info: {str(e)}"
            )

    def _extract_info(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract info using yt-dlp (runs in thread)."""
        with yt_dlp.YoutubeDL(self.ytdl_opts) as ytdl:
            # Determine if it's a direct URL or search query
            if query.startswith(("http://", "https://")):
                search_query = query
            else:
                search_query = f"ytsearch:{query}"
            
            try:
                info = ytdl.extract_info(search_query, download=False)
                
                # Handle search results
                if "entries" in info and info["entries"]:
                    # Take the first search result
                    return info["entries"][0]
                else:
                    # Direct URL result
                    return info
                    
            except Exception as e:
                self.logger.error("yt-dlp extraction failed", error=str(e))
                raise

    def _create_song_from_info(self, info: Dict[str, Any]) -> Song:
        """Create a Song object from yt-dlp info."""
        title = self._get_string_from_dict(info, "title", "Unknown")
        webpage_url = self._get_string_from_dict(info, "webpage_url", "")
        
        # Extract duration if available
        duration = None
        if "duration" in info and isinstance(info["duration"], (int, float)):
            duration = int(info["duration"])
        
        # Get the best audio URL
        url = self._extract_best_audio_url(info)
        
        return Song(
            title=title,
            url=url,
            webpage_url=webpage_url,
            duration=duration
        )

    def _extract_best_audio_url(self, info: Dict[str, Any]) -> str:
        """Find the best audio URL from available formats."""
        # First try the direct URL field
        if "url" in info and info["url"]:
            return info["url"]

        # Look through formats for audio streams
        formats = info.get("formats", [])
        if not formats:
            return ""

        # Priority: audio-only > lowest video quality with audio
        best_audio_url = ""
        fallback_url = ""

        for fmt in formats:
            if not isinstance(fmt, dict):
                continue

            url = fmt.get("url", "")
            if not url:
                continue

            # Check format properties
            vcodec = fmt.get("vcodec", "")
            acodec = fmt.get("acodec", "")
            ext = fmt.get("ext", "")

            # Prefer audio-only formats (vcodec=none but acodec exists)
            if vcodec == "none" and acodec and acodec != "none":
                best_audio_url = url
                break  # Found audio-only, this is best

            # Fallback to formats with audio (even if they have video)
            if acodec and acodec != "none" and ext != "mhtml":
                fallback_url = url

        return best_audio_url or fallback_url

    def _get_string_from_dict(self, data: Dict[str, Any], key: str, default: str) -> str:
        """Safely extract a string value from a dictionary."""
        value = data.get(key)
        if isinstance(value, str):
            return value
        return default

    def _is_ytdlp_available(self) -> bool:
        """Check if yt-dlp is available in the system."""
        return shutil.which("yt-dlp") is not None

    async def close(self) -> None:
        """Clean up resources."""
        self.logger.debug("Audio extractor cleanup completed")
