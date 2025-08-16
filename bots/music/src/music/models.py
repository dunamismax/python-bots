"""Data models for the Music bot."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Song:
    """Represents a song in the music queue."""
    
    title: str
    url: str
    webpage_url: str = ""
    duration: Optional[int] = None
    requester_id: str = ""
    requester_name: str = ""
    
    def is_valid(self) -> bool:
        """Check if the song has valid data."""
        return bool(self.title and self.url)
    
    def get_display_name(self) -> str:
        """Get the display name for the song."""
        return self.title or "Unknown Song"