"""Convert Flippa Actor items to the existing Collector/DealObject format."""

from __future__ import annotations

import logging
from typing import Any, Mapping


logger = logging.getLogger(__name__)


COLLECTOR_FIELDS = (
    "source",
    "source_id",
    "name",
    "url",
    "type",
    "description",
    "monetization_model",
    "target_users",
    "price",
    "monthly_revenue",
    "monthly_profit",
    "profit_margin",
    "traffic",
    "organic_traffic",
    "site_age",
    "verified_revenue",
    "verified_traffic",
)


def normalize_flippa_listing(item: Mapping[str, Any]) -> dict[str, Any]:
    """Return one Flippa listing using only fields accepted by CollectorAgent."""
    basic_info = item.get("basic_info")
    if not isinstance(basic_info, Mapping):
        basic_info = {}

    name = _first_text(item.get("property_name"), basic_info.get("name"), item.get("title"))
    url = _first_text(item.get("listing_url"), item.get("url"))
    summary = _first_text(item.get("summary"), item.get("title"))
    source_id = _first_text(
        str(item.get("source_id")) if item.get("source_id") is not None else "",
        str(item.get("id")) if item.get("id") is not None else "",
        str(item.get("listing_id")) if item.get("listing_id") is not None else "",
    )

    if not name:
        logger.warning("Flippa listing has no name")
    if not url:
        logger.warning("Flippa listing '%s' has no URL", name or "unknown")

    return {
        "source": "Flippa",
        "source_id": source_id,
        "name": name,
        "url": url,
        "type": _normalize_type(item.get("property_type")),
        "description": summary,
        "monetization_model": _first_text(item.get("monetization")),
        "target_users": "",
        "price": _to_number(item.get("price"), "price", name),
        "monthly_revenue": _to_number(item.get("revenue_average"), "revenue_average", name),
        "monthly_profit": None,
        "profit_margin": None,
        "traffic": _to_traffic(item.get("uniques_per_month"), name),
        "organic_traffic": None,
        "site_age": None,
        "verified_revenue": None,
        "verified_traffic": None,
    }


def _first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _normalize_type(value: Any) -> str:
    if not isinstance(value, str):
        return "other"

    normalized = value.strip().lower()
    type_map = {
        "saas": "SaaS",
        "website": "site",
        "ios_app": "other",
        "android_app": "other",
    }
    return type_map.get(normalized, "other")


def _to_number(value: Any, field: str, listing_name: str) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        logger.warning("Flippa listing '%s' has invalid %s", listing_name or "unknown", field)
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").replace("$", "").strip())
        except ValueError:
            pass
    logger.warning("Flippa listing '%s' has invalid %s", listing_name or "unknown", field)
    return None


def _to_traffic(value: Any, listing_name: str) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        logger.warning("Flippa listing '%s' has invalid uniques_per_month", listing_name or "unknown")
        return None
    if isinstance(value, (int, float, str)):
        return str(value)
    logger.warning("Flippa listing '%s' has invalid uniques_per_month", listing_name or "unknown")
    return None
