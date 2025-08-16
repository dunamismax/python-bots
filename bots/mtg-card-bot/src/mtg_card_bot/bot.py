"""Main MTG Card Bot Discord bot implementation."""

import asyncio
import io
import re
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import discord
import httpx
from . import config, errors, logging



from .cache import CardCache
from .scryfall import Card, ScryfallClient


class MultiResolvedCard:
    """Container for a resolved card query in multi-card lookups."""

    def __init__(self, query: str, card: Optional[Card] = None, 
                 used_fallback: bool = False, error: Optional[Exception] = None) -> None:
        self.query = query
        self.card = card
        self.used_fallback = used_fallback
        self.error = error


class MTGCardBot(discord.Client):
    """Discord bot for Magic: The Gathering card lookups."""

    def __init__(self, cfg: config.MTGConfig) -> None:
        """Initialize the MTG Card Bot."""
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.config = cfg

        self.logger = logging.with_component("mtg_card_bot")
        self.scryfall_client = ScryfallClient()
        self.cache = CardCache(
            ttl_seconds=cfg.cache_ttl,
            max_size=cfg.cache_size
        )
        self.http_client = httpx.AsyncClient(timeout=20.0)
        
        # Duplicate suppression structures
        # Track recent (author, normalized_content) to timestamp
        self._recent_commands: Dict[tuple[int, str], float] = {}
        # Track processed Discord message IDs
        self._processed_message_ids: set[int] = set()

    async def start(self) -> None:
        # Prefer static token from config; support multiple field names
        token = getattr(self.config, "token", None) or getattr(self.config, "discord_token", "")
        await super().start(token)

    async def setup_hook(self) -> None:
        """Called when the bot is starting up."""
        self.logger.info("MTG Card bot setup completed")

    async def on_ready(self) -> None:
        """Called when the bot is ready."""
        self.logger.info("Bot is ready", username=str(self.user))

    async def on_message(self, message: discord.Message) -> None:
        """Handle incoming messages."""
        # Ignore messages from bots
        if message.author.bot:
            return
        
        # If we've already processed this message (duplicate delivery), skip
        if message.id in self._processed_message_ids:
            return

        # Check if message starts with command prefix
        if not message.content.startswith(self.config.command_prefix):
            return

        # Remove prefix
        content = message.content[len(self.config.command_prefix):]
        
        # Suppress duplicate commands from the same user/content within a short window
        normalized = " ".join(content.lower().split())
        key = (message.author.id, normalized)
        now = time.time()
        last = self._recent_commands.get(key)
        if last is not None and (now - last) < 1.5:
            return
        self._recent_commands[key] = now
        self._processed_message_ids.add(message.id)
        
        # If the content contains semicolons, treat as multi-card lookup
        if ";" in content:
            await self._handle_multi_card_lookup(message, content)
            return

        parts = content.split()
        if not parts:
            return

        command = parts[0].lower()
        args = parts[1:]

        # Handle specific commands
        if command == "random":
            await self._handle_random_card(message)
        elif command == "help":
            await self._handle_help(message)
        elif command == "cache":
            await self._handle_cache_stats(message)
        else:
            # Treat as card lookup
            card_query = " ".join(parts)
            await self._handle_card_lookup(message, card_query)

    async def _handle_random_card(self, message: discord.Message) -> None:
        """Handle the random card command."""
        self.logger.info("Fetching random card", 
                        user_id=str(message.author.id),
                        username=message.author.name)
        
        try:
            card = await self.scryfall_client.get_random_card()
            await self._send_card_message(message.channel, card, False, "")
        except Exception as e:
            self.logger.error("Random card command failed", 
                            user_id=str(message.author.id),
                            error=str(e))
            await self._send_error_message(message.channel, 
                                         "Sorry, something went wrong while fetching a random card.")
            # metrics call omitted for simplicity

    async def _handle_card_lookup(self, message: discord.Message, card_query: str) -> None:
        """Handle card lookup with support for filtering parameters."""
        if not card_query:
            await self._send_error_message(message.channel, "Card query cannot be empty.")
            return

        self.logger.info("Looking up card", 
                        user_id=str(message.author.id),
                        username=message.author.name,
                        card_query=card_query)

        try:
            card, used_fallback = await self._resolve_card_query(card_query)
            await self._send_card_message(message.channel, card, used_fallback, card_query)
        except Exception as e:
            self.logger.error("Card lookup failed", 
                            user_id=str(message.author.id),
                            card_query=card_query,
                            error=str(e))
            
            # Provide helpful error messages based on error type
            if isinstance(e, errors.MTGError):
                if e.error_type == errors.ErrorType.NOT_FOUND:
                    if self._has_filter_parameters(card_query):
                        error_msg = f"No cards found for '{card_query}'. Try simpler filters like `e:set` or `is:foil`, or check the spelling."
                    else:
                        error_msg = f"Card '{card_query}' not found. Try partial names like 'bolt' for 'Lightning Bolt'."
                elif e.error_type == errors.ErrorType.RATE_LIMIT:
                    error_msg = "API rate limit exceeded. Please try again in a moment."
                else:
                    error_msg = "Sorry, something went wrong while searching for that card."
            else:
                error_msg = "Sorry, something went wrong while searching for that card."
            
            await self._send_error_message(message.channel, error_msg)

    async def _resolve_card_query(self, card_query: str) -> Tuple[Card, bool]:
        """Resolve a single card query into a card with caching and fallbacks."""
        card_query = card_query.strip()
        has_filters = self._has_filter_parameters(card_query)
        used_fallback = False

        if has_filters:
            # Use search API for filtered queries
            try:
                card = await self.scryfall_client.search_card_first(card_query)
            except Exception:
                # If filtered search fails, extract card name and try fallback
                card_name = self._extract_card_name(card_query)
                if card_name and len(card_name) >= 2:
                    card = await self.cache.get_or_set(
                        card_name,
                        self.scryfall_client.get_card_by_name
                    )
                    used_fallback = True
                else:
                    raise
        else:
            # Use cache for simple name lookups
            card = await self.cache.get_or_set(
                card_query,
                self.scryfall_client.get_card_by_name
            )

        if not card or not card.is_valid_card():
            raise errors.create_error(errors.ErrorType.NOT_FOUND, "No card found for query")

        return card, used_fallback

    async def _handle_multi_card_lookup(self, message: discord.Message, raw_content: str) -> None:
        """Handle a semicolon-separated list of card queries."""
        # Split on semicolons and trim spaces
        raw_parts = raw_content.split(";")
        queries = [q.strip() for q in raw_parts if q.strip()]

        if not queries:
            await self._send_error_message(message.channel, "No valid card queries provided.")
            return

        # If only one query, fallback to normal flow
        if len(queries) == 1:
            await self._handle_card_lookup(message, queries[0])
            return

        self.logger.info("Multi-card lookup", 
                        user_id=str(message.author.id),
                        username=message.author.name,
                        query_count=len(queries))

        # Resolve cards sequentially
        resolved_cards: List[MultiResolvedCard] = []
        for query in queries:
            try:
                card, used_fallback = await self._resolve_card_query(query)
                resolved_cards.append(MultiResolvedCard(query, card, used_fallback))
            except Exception as e:
                resolved_cards.append(MultiResolvedCard(query, error=e))

        # Check if any cards were successfully resolved
        success_count = sum(1 for r in resolved_cards 
                          if r.error is None and r.card and r.card.is_valid_card())
        
        if success_count == 0:
            await self._send_error_message(message.channel, 
                                         "Failed to resolve any requested cards.")
            return

        # Send cards in chunks of 4 for nice layout
        max_per_message = 4
        for i in range(0, len(resolved_cards), max_per_message):
            chunk = resolved_cards[i:i + max_per_message]
            await self._send_card_grid_message(message.channel, chunk)


    async def _send_card_grid_message(self, channel: discord.abc.Messageable, 
                                    items: List[MultiResolvedCard]) -> None:
        """Send a grid of card images and information."""
        files: List[discord.File] = []
        md_lines: List[str] = []

        for item in items:
            if item.error or not item.card or not item.card.is_valid_card():
                md_lines.append(f"- {item.query}: not found")
                continue

            name = item.card.get_display_name()
            label = name
            if item.used_fallback:
                label += " (closest match)"

            # Add masked link for clean display
            if item.card.scryfall_uri:
                md_lines.append(f"- [{label}]({item.card.scryfall_uri})")
            else:
                md_lines.append(f"- {label}")

            # Fetch image if available
            if item.card.has_image():
                image_url = item.card.get_best_image_url()
                try:
                    image_data, filename = await self._fetch_image(image_url, name)
                    files.append(discord.File(io.BytesIO(image_data), filename=filename))
                except Exception as e:
                    self.logger.warning("Failed to fetch image", 
                                      image_url=image_url, 
                                      error=str(e))

        # Send list embed first
        embed = discord.Embed(
            title="Requested Cards",
            description="\n".join(md_lines),
            color=0x5865F2
        )
        await channel.send(embed=embed)

        # Then send images if any were fetched
        if files:
            await channel.send(files=files)

    async def _fetch_image(self, url: str, card_name: str) -> Tuple[bytes, str]:
        """Fetch image data and return bytes with filename."""
        response = await self.http_client.get(url)
        response.raise_for_status()
        
        # Determine file extension
        content_type = response.headers.get("content-type", "")
        if "png" in content_type:
            ext = ".png"
        elif "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"
        else:
            # Try to guess from URL
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()
            if path.endswith(".png"):
                ext = ".png"
            elif path.endswith((".jpg", ".jpeg")):
                ext = ".jpg"
            else:
                ext = ".jpg"  # Default

        # Create safe filename
        safe_name = self._safe_filename(card_name)
        filename = f"{safe_name}{ext}"

        return response.content, filename

    def _safe_filename(self, name: str) -> str:
        """Create a safe filename from a card name."""
        # Replace unsafe characters with hyphens
        safe = re.sub(r'[^a-zA-Z0-9._-]+', '-', name.lower())
        safe = safe.strip('-._')
        if not safe:
            return "card"
        return safe[:64]  # Limit length

    def _has_filter_parameters(self, query: str) -> bool:
        """Check if the query contains Scryfall filter syntax."""
        essential_filters = [
            "e:", "set:", "frame:", "border:", "is:foil", "is:nonfoil", 
            "is:fullart", "is:textless", "is:borderless", "rarity:"
        ]
        
        lower_query = query.lower()
        return any(filter_param in lower_query for filter_param in essential_filters)

    def _extract_card_name(self, query: str) -> str:
        """Extract the card name from a filtered query for fallback purposes."""
        words = query.split()
        card_name_parts = []

        for word in words:
            lower_word = word.lower()
            
            # Skip known filter patterns with colons
            if ":" in lower_word:
                continue
            
            # Skip standalone filter keywords
            essential_keywords = ["foil", "nonfoil", "fullart", "textless", "borderless"]
            if lower_word not in essential_keywords:
                card_name_parts.append(word)

        return " ".join(card_name_parts).strip()

    async def _send_card_message(self, channel: discord.abc.Messageable, 
                               card: Card, used_fallback: bool, original_query: str) -> None:
        """Send a card image and details to a Discord channel."""
        if not card.is_valid_card():
            await self._send_error_message(channel, "Received invalid card data from API.")
            return

        if not card.has_image():
            # Send text-only message if no image is available
            embed = discord.Embed(
                title=card.get_display_name(),
                description=f"**{card.type_line}**\n{card.oracle_text}",
                color=0x9B59B6,
                url=card.scryfall_uri
            )
            
            embed.add_field(
                name="Set",
                value=f"{card.set_name} ({card.set_code.upper()})",
                inline=True
            )
            
            embed.add_field(
                name="Rarity",
                value=card.rarity.title(),
                inline=True
            )
            
            if card.artist:
                embed.add_field(
                    name="Artist",
                    value=card.artist,
                    inline=True
                )

            await channel.send(embed=embed)
            return

        # Create rich embed with card image
        embed = discord.Embed(
            title=card.get_display_name(),
            url=card.scryfall_uri,
            color=self._get_rarity_color(card.rarity)
        )
        
        embed.set_image(url=card.get_best_image_url())
        
        # Add mana cost and fallback notification
        descriptions = []
        
        if used_fallback:
            descriptions.append(f"*No exact match found for filters in `{original_query}`, showing closest match*")
        
        if card.mana_cost:
            descriptions.append(f"**Mana Cost:** {card.mana_cost}")
        
        if descriptions:
            embed.description = "\n".join(descriptions)

        # Footer with set, rarity, and artist
        footer_parts = [card.set_name, card.rarity.title()]
        if card.artist:
            footer_parts.append(f"Art by {card.artist}")
        
        embed.set_footer(text=" • ".join(footer_parts))

        await channel.send(embed=embed)

    def _get_rarity_color(self, rarity: str) -> int:
        """Return a color based on card rarity."""
        rarity_colors = {
            "mythic": 0xFF8C00,    # Dark orange
            "rare": 0xFFD700,      # Gold
            "uncommon": 0xC0C0C0,  # Silver
            "common": 0x000000,    # Black
            "special": 0xFF1493,   # Deep pink
            "bonus": 0x9370DB,     # Medium purple
        }
        return rarity_colors.get(rarity.lower(), 0x9B59B6)  # Default purple

    async def _handle_help(self, message: discord.Message) -> None:
        """Handle the help command."""
        self.logger.info("Showing help information",
                        user_id=str(message.author.id),
                        username=message.author.name)

        prefix = self.config.command_prefix
        embed = discord.Embed(
            title="MTG Card Bot Help",
            description="Look up cards, build grids, and filter versions.",
            color=0x3498DB
        )

        embed.add_field(
            name="Commands",
            value=(
                f"`{prefix}<card>` – Look up a card\n"
                f"`{prefix}<card1>; <card2>; ...` – Grid lookup (up to 10)\n"
                f"`{prefix}random` – Random card\n"
                f"`{prefix}cache` – Cache stats\n"
                f"`{prefix}help` – This menu"
            ),
            inline=False
        )

        embed.add_field(
            name="Old-School Favorites (pre-2003)",
            value=(
                f"`{prefix}black lotus e:lea` – Alpha 1993\n"
                f"`{prefix}ancestral recall e:lea` – Alpha 1993\n"
                f"`{prefix}time walk e:lea` – Alpha 1993\n"
                f"`{prefix}sol ring e:lea` – Alpha 1993"
            ),
            inline=False
        )

        embed.add_field(
            name="Multi-Card Demo (4-card grid)",
            value=f"`{prefix}city of brass e:arn; library of alexandria e:arn; juzam djinn e:arn; serendib efreet e:arn`",
            inline=False
        )

        embed.add_field(
            name="Filters",
            value="Set `e:lea|arn|leg|usg|tmp|ice` • Frame `frame:1993|1997` • Border `border:white` • Finish `is:foil|is:nonfoil` • Rarity `rarity:mythic|rare`",
            inline=False
        )

        embed.set_footer(text="Fuzzy and partial name matching supported.")

        await message.channel.send(embed=embed)


    async def _handle_cache_stats(self, message: discord.Message) -> None:
        """Handle the cache stats command."""
        self.logger.info("Showing cache statistics",
                        user_id=str(message.author.id),
                        username=message.author.name)

        cache_stats = self.cache.stats()

        embed = discord.Embed(
            title="Cache Performance Statistics",
            description="Card caching system metrics and utilization",
            color=0xE67E22
        )

        embed.add_field(
            name="Storage Utilization",
            value=(
                f"**Current Size:** {cache_stats.size} cards\n"
                f"**Maximum Size:** {cache_stats.max_size} cards\n"
                f"**Utilization:** {cache_stats.size / cache_stats.max_size * 100:.1f}%"
            ),
            inline=True
        )

        embed.add_field(
            name="Hit Performance",
            value=(
                f"**Hit Rate:** {cache_stats.hit_rate:.1f}%\n"
                f"**Cache Hits:** {cache_stats.hits}\n"
                f"**Cache Misses:** {cache_stats.misses}"
            ),
            inline=True
        )

        embed.add_field(
            name="Cache Management",
            value=(
                f"**Evictions:** {cache_stats.evictions}\n"
                f"**TTL Duration:** {cache_stats.ttl_seconds:.0f}s"
            ),
            inline=True
        )

        embed.set_footer(text="Efficient caching reduces API calls and improves response times")

        await message.channel.send(embed=embed)

    async def _send_error_message(self, channel: discord.abc.Messageable, message: str) -> None:
        """Send an error message to a Discord channel."""
        embed = discord.Embed(
            title="Error",
            description=message,
            color=0xE74C3C
        )
        
        try:
            await channel.send(embed=embed)
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
        self.logger.info("Shutting down MTG Card bot")
        try:
            await self.scryfall_client.close()
        except Exception as e:
            self.logger.warning("Error closing scryfall client", error=str(e))
        
        try:
            await self.http_client.aclose()
        except Exception as e:
            self.logger.warning("Error closing http client", error=str(e))
        
        await super().close()
