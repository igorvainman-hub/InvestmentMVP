"""Local archive for normalized Flippa listings, separate from the pipeline."""

from __future__ import annotations

from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any, Iterable, Mapping

from deal_model import DealObject


logger = logging.getLogger(__name__)


class FlippaArchive:
    """Store normalized Flippa listings and retain the latest raw Apify response."""

    def __init__(
        self,
        archive_dir: str | Path = "./data/flippa_archive",
        raw_snapshot_path: str | Path = "./data/flippa_latest_raw.json",
    ) -> None:
        self.archive_dir = Path(archive_dir)
        self.raw_snapshot_path = Path(raw_snapshot_path)

    def save_batch(
        self,
        listings: Iterable[Mapping[str, Any]],
        raw_response: list[Mapping[str, Any]],
    ) -> list[DealObject]:
        """Save new normalized listings and overwrite the latest raw snapshot."""
        self._write_raw_snapshot(raw_response)
        existing_urls = {deal.url for deal in self.list_all() if deal.url}
        saved: list[DealObject] = []

        for listing in listings:
            url = listing.get("url")
            if not isinstance(url, str) or not url.strip():
                logger.warning("Skipping Flippa listing without a URL")
                continue
            if url in existing_urls:
                logger.info("Skipping existing Flippa listing: %s", url)
                continue

            allowed = {
                key: value
                for key, value in listing.items()
                if key in DealObject.__dataclass_fields__
            }
            deal = DealObject(source="Flippa", status="NEW", **allowed)
            self._write_deal(deal)
            existing_urls.add(deal.url)
            saved.append(deal)
        return saved

    def list_all(self) -> list[DealObject]:
        """Return all archived Flippa deals, oldest first."""
        if not self.archive_dir.exists():
            return []

        deals: list[DealObject] = []
        for path in sorted(self.archive_dir.glob("*.json")):
            try:
                with path.open("r", encoding="utf-8") as file:
                    deals.append(DealObject.from_dict(json.load(file)))
            except (OSError, json.JSONDecodeError) as error:
                logger.warning("Skipping unreadable archive file %s: %s", path, error)
        return sorted(deals, key=lambda deal: deal.created_at)

    def list_new_since(self, since: datetime) -> list[DealObject]:
        """Return archived deals first saved after the supplied timestamp."""
        result: list[DealObject] = []
        for deal in self.list_all():
            try:
                created_at = datetime.fromisoformat(deal.created_at)
            except ValueError:
                logger.warning("Skipping deal %s with invalid created_at", deal.id)
                continue
            if created_at > since:
                result.append(deal)
        return result

    def _write_raw_snapshot(self, raw_response: list[Mapping[str, Any]]) -> None:
        self.raw_snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        with self.raw_snapshot_path.open("w", encoding="utf-8") as file:
            json.dump(raw_response, file, ensure_ascii=False, indent=2)

    def _write_deal(self, deal: DealObject) -> None:
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        path = self.archive_dir / f"{deal.id}.json"
        with path.open("w", encoding="utf-8") as file:
            json.dump(deal.to_dict(), file, ensure_ascii=False, indent=2)
