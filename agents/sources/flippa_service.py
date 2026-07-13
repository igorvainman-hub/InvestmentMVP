"""Explicit, isolated Flippa import service."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from deal_model import DealObject

from agents.sources.apify_flippa import ApifyFlippaClient
from agents.sources.flippa_archive import FlippaArchive
from agents.sources.flippa_normalizer import normalize_flippa_listing


DEFAULT_ACTOR_ID = "epicscrapers~flippa-scraper"


class FlippaService:
    """Fetch, normalize, and archive Flippa listings only when explicitly invoked."""

    def __init__(
        self,
        actor_id: str = DEFAULT_ACTOR_ID,
        client: ApifyFlippaClient | None = None,
        archive: FlippaArchive | None = None,
    ) -> None:
        self.client = client or ApifyFlippaClient(actor_id=actor_id)
        self.archive = archive or FlippaArchive()

    def fetch_and_archive(self, **filters: Any) -> list[DealObject]:
        """Run the Actor, overwrite the raw snapshot, and archive only new URLs.

        Calling this method performs a paid Apify request. It is intentionally
        never called during object construction or module import.
        """
        raw_response = self.client.fetch_listings(filters)
        normalized = [normalize_flippa_listing(item) for item in raw_response]
        return self.archive.save_batch(normalized, raw_response)

    def list_new_since(self, since: datetime) -> list[DealObject]:
        """Read newly archived Flippa listings without calling Apify."""
        return self.archive.list_new_since(since)
