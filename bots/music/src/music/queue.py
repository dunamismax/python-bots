"""Music queue management for the Music bot."""

import threading
from typing import List, Optional

from .models import Song


class MusicQueue:
    """Manages the music queue for a guild."""

    def __init__(self) -> None:
        """Initialize an empty music queue."""
        self._songs: List[Song] = []
        self._current: Optional[Song] = None
        self._is_playing: bool = False
        self._is_paused: bool = False
        self._should_skip: bool = False
        self._lock = threading.RLock()

    def add(self, song: Song) -> int:
        """Add a song to the queue and return its position."""
        with self._lock:
            self._songs.append(song)
            return len(self._songs) - 1

    def next(self) -> Optional[Song]:
        """Return and remove the next song from the queue."""
        with self._lock:
            if not self._songs:
                return None
            return self._songs.pop(0)

    def current(self) -> Optional[Song]:
        """Return the currently playing song."""
        with self._lock:
            return self._current

    def set_current(self, song: Optional[Song]) -> None:
        """Set the currently playing song."""
        with self._lock:
            self._current = song

    def is_playing(self) -> bool:
        """Return whether music is currently playing."""
        with self._lock:
            return self._is_playing

    def set_playing(self, playing: bool) -> None:
        """Set the playing status."""
        with self._lock:
            self._is_playing = playing

    def is_paused(self) -> bool:
        """Return whether music is currently paused."""
        with self._lock:
            return self._is_paused

    def set_paused(self, paused: bool) -> None:
        """Set the paused status."""
        with self._lock:
            self._is_paused = paused

    def should_skip(self) -> bool:
        """Return whether the current song should be skipped."""
        with self._lock:
            return self._should_skip

    def skip(self) -> None:
        """Mark the current song to be skipped."""
        with self._lock:
            self._should_skip = True

    def set_skip(self, skip: bool) -> None:
        """Set the skip flag."""
        with self._lock:
            self._should_skip = skip

    def is_empty(self) -> bool:
        """Return whether the queue is empty."""
        with self._lock:
            return len(self._songs) == 0

    def size(self) -> int:
        """Return the number of songs in the queue."""
        with self._lock:
            return len(self._songs)

    def get_songs(self) -> List[Song]:
        """Return a copy of all songs in the queue."""
        with self._lock:
            return self._songs.copy()

    def clear(self) -> None:
        """Clear the entire queue and reset all state."""
        with self._lock:
            self._songs.clear()
            self._current = None
            self._is_playing = False
            self._is_paused = False
            self._should_skip = False


class QueueManager:
    """Manages music queues for multiple guilds."""

    def __init__(self) -> None:
        """Initialize the queue manager."""
        self._queues: dict[str, MusicQueue] = {}
        self._lock = threading.RLock()

    def get_queue(self, guild_id: str) -> MusicQueue:
        """Get or create a queue for a guild."""
        with self._lock:
            if guild_id not in self._queues:
                self._queues[guild_id] = MusicQueue()
            return self._queues[guild_id]

    def clear_queue(self, guild_id: str) -> None:
        """Clear a guild's queue."""
        with self._lock:
            if guild_id in self._queues:
                self._queues[guild_id].clear()

    def cleanup(self) -> None:
        """Clear all queues."""
        with self._lock:
            for queue in self._queues.values():
                queue.clear()
            self._queues.clear()