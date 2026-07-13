"""Minimal Apify client for fetching raw Flippa actor datasets.

No network request is made when this module is imported. A request happens only
when ``ApifyFlippaClient.fetch_listings`` is explicitly called.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class ApifyFlippaClient:
    """Run a configured Apify actor and return its dataset items unchanged."""

    API_BASE_URL = "https://api.apify.com/v2"

    def __init__(self, actor_id: str, api_token: str | None = None) -> None:
        self.actor_id = actor_id
        self.api_token = api_token or os.getenv("APIFY_API_TOKEN")

    def fetch_listings(self, actor_input: dict[str, Any]) -> list[dict[str, Any]]:
        """Run the actor synchronously and return the raw dataset JSON items.

        ``actor_id`` and ``actor_input`` depend on the selected Apify Flippa
        actor. This method intentionally does not normalize or persist data.
        """
        if not self.api_token:
            raise ValueError("APIFY_API_TOKEN is not configured")

        actor_id = quote(self.actor_id, safe="~")
        url = f"{self.API_BASE_URL}/acts/{actor_id}/run-sync-get-dataset-items"
        payload = json.dumps(actor_input).encode("utf-8")
        request = Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Apify request failed with HTTP {error.code}: {detail}") from error
        except URLError as error:
            raise RuntimeError(f"Could not reach Apify: {error.reason}") from error
        except json.JSONDecodeError as error:
            raise RuntimeError("Apify returned invalid JSON") from error

        if not isinstance(data, list):
            raise RuntimeError("Apify dataset response must be a JSON list")
        if not all(isinstance(item, dict) for item in data):
            raise RuntimeError("Apify dataset items must be JSON objects")
        return data
