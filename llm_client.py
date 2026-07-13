"""
Thin wrapper around the OpenAI API so agents don't deal with SDK details.

Usage:
    export OPENAI_API_KEY="sk-..."
    client = LLMClient()
    text = client.complete("Analyze this SaaS...", json_mode=True)

If OPENAI_API_KEY is not set, LLMClient falls back to a mock mode that
returns a clearly-labeled placeholder response, so the rest of the
pipeline (store, scoring math, CLI) can be tested without an API key.
"""

from __future__ import annotations
import os
import json


class LLMClient:
    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.mock = self.api_key is None
        self._client = None

        if not self.mock:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise RuntimeError(
                    "openai package not installed. Run: pip install openai --break-system-packages"
                )

    def complete(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        if self.mock:
            return self._mock_response(json_mode)

        kwargs = {}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            **kwargs,
        )
        return response.choices[0].message.content

    def _mock_response(self, json_mode: bool) -> str:
        if json_mode:
            return json.dumps({
                "_mock": True,
                "note": "OPENAI_API_KEY not set — this is a placeholder response.",
            })
        return "[MOCK RESPONSE — set OPENAI_API_KEY to get real analysis]"
