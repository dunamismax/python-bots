"""Database functionality for Discord bots."""

import json
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime

import aiosqlite

from . import errors


@dataclass
class Song:
    """Represents a song in a playlist."""
    title: str
    url: str
    webpage_url: str
    duration: int | None = None
    added_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Playlist:
    """Represents a music playlist."""
    id: int
    name: str
    owner_id: str
    guild_id: str
    songs: list[Song] = field(default_factory=list)


class Database:
    """Database connection with bot functionality."""

    def __init__(self, database_url: str = "bot.db"):
        self.database_url = database_url or "bot.db"
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Connect to the database."""
        try:
            self._connection = await aiosqlite.connect(self.database_url)
            self._connection.row_factory = aiosqlite.Row
            await self._migrate()
        except Exception as e:
            raise errors.new_database_error("Failed to connect to database", e)

    async def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None

    @asynccontextmanager
    async def transaction(self):
        """Create a database transaction context."""
        if not self._connection:
            raise errors.new_database_error("Database not connected", None)

        try:
            await self._connection.execute("BEGIN")
            yield self._connection
            await self._connection.commit()
        except Exception as e:
            await self._connection.rollback()
            raise errors.new_database_error("Transaction failed", e)

    async def _migrate(self) -> None:
        """Create necessary database tables."""
        migration_sql = """
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            owner_id TEXT NOT NULL,
            guild_id TEXT NOT NULL,
            songs TEXT DEFAULT '[]',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_playlists_owner_guild 
        ON playlists(owner_id, guild_id);
        """

        try:
            await self._connection.executescript(migration_sql)
            await self._connection.commit()
        except Exception as e:
            raise errors.new_database_error("Database migration failed", e)

    async def create_playlist(self, name: str, owner_id: str, guild_id: str) -> int:
        """Create a new playlist."""
        if not self._connection:
            raise errors.new_database_error("Database not connected", None)

        try:
            cursor = await self._connection.execute(
                "INSERT INTO playlists (name, owner_id, guild_id) VALUES (?, ?, ?)",
                (name, owner_id, guild_id)
            )
            await self._connection.commit()
            return cursor.lastrowid
        except Exception as e:
            raise errors.new_database_error("Failed to create playlist", e)

    async def get_playlist(self, playlist_id: int) -> Playlist | None:
        """Retrieve a playlist by ID."""
        if not self._connection:
            raise errors.new_database_error("Database not connected", None)

        try:
            cursor = await self._connection.execute(
                "SELECT id, name, owner_id, guild_id, songs FROM playlists WHERE id = ?",
                (playlist_id,)
            )
            row = await cursor.fetchone()

            if not row:
                return None

            # Parse songs JSON
            songs_data = json.loads(row["songs"])
            songs = [Song(**song) for song in songs_data]

            return Playlist(
                id=row["id"],
                name=row["name"],
                owner_id=row["owner_id"],
                guild_id=row["guild_id"],
                songs=songs
            )
        except json.JSONDecodeError as e:
            raise errors.new_database_error("Failed to parse songs JSON", e)
        except Exception as e:
            raise errors.new_database_error("Failed to get playlist", e)

    async def get_user_playlists(self, owner_id: str, guild_id: str) -> list[Playlist]:
        """Retrieve all playlists for a user in a guild."""
        if not self._connection:
            raise errors.new_database_error("Database not connected", None)

        try:
            cursor = await self._connection.execute(
                """SELECT id, name, owner_id, guild_id, songs 
                   FROM playlists 
                   WHERE owner_id = ? AND guild_id = ? 
                   ORDER BY created_at DESC""",
                (owner_id, guild_id)
            )
            rows = await cursor.fetchall()

            playlists = []
            for row in rows:
                # Parse songs JSON
                songs_data = json.loads(row["songs"])
                songs = [Song(**song) for song in songs_data]

                playlist = Playlist(
                    id=row["id"],
                    name=row["name"],
                    owner_id=row["owner_id"],
                    guild_id=row["guild_id"],
                    songs=songs
                )
                playlists.append(playlist)

            return playlists
        except json.JSONDecodeError as e:
            raise errors.new_database_error("Failed to parse songs JSON", e)
        except Exception as e:
            raise errors.new_database_error("Failed to get user playlists", e)

    async def add_song_to_playlist(self, playlist_id: int, song: Song) -> None:
        """Add a song to a playlist."""
        # Get current playlist
        playlist = await self.get_playlist(playlist_id)
        if not playlist:
            raise errors.new_not_found_error("Playlist not found")

        # Add song to list
        playlist.songs.append(song)

        # Convert to JSON
        songs_json = json.dumps([song.__dict__ for song in playlist.songs])

        try:
            await self._connection.execute(
                "UPDATE playlists SET songs = ? WHERE id = ?",
                (songs_json, playlist_id)
            )
            await self._connection.commit()
        except Exception as e:
            raise errors.new_database_error("Failed to update playlist", e)

    async def remove_song_from_playlist(self, playlist_id: int, song_index: int) -> None:
        """Remove a song from a playlist by index."""
        # Get current playlist
        playlist = await self.get_playlist(playlist_id)
        if not playlist:
            raise errors.new_not_found_error("Playlist not found")

        # Check index bounds
        if song_index < 0 or song_index >= len(playlist.songs):
            raise errors.new_validation_error("Invalid song index")

        # Remove song from list
        playlist.songs.pop(song_index)

        # Convert to JSON
        songs_json = json.dumps([song.__dict__ for song in playlist.songs])

        try:
            await self._connection.execute(
                "UPDATE playlists SET songs = ? WHERE id = ?",
                (songs_json, playlist_id)
            )
            await self._connection.commit()
        except Exception as e:
            raise errors.new_database_error("Failed to update playlist", e)

    async def delete_playlist(self, playlist_id: int, owner_id: str) -> None:
        """Delete a playlist."""
        try:
            cursor = await self._connection.execute(
                "DELETE FROM playlists WHERE id = ? AND owner_id = ?",
                (playlist_id, owner_id)
            )
            await self._connection.commit()

            if cursor.rowcount == 0:
                raise errors.new_not_found_error("Playlist not found or not owned by user")
        except Exception as e:
            if isinstance(e, errors.BotError):
                raise
            raise errors.new_database_error("Failed to delete playlist", e)


# Global database instance
_database: Database | None = None


async def get_database() -> Database:
    """Get the global database instance."""
    global _database
    if _database is None:
        raise errors.new_database_error("Database not initialized", None)
    return _database


async def initialize_database(database_url: str = "bot.db") -> None:
    """Initialize the global database."""
    global _database
    _database = Database(database_url)
    await _database.connect()


async def close_database() -> None:
    """Close the global database."""
    global _database
    if _database:
        await _database.close()
        _database = None
