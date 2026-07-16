"""
Deal Collector Agent
Turns raw input (url, description, price) into a draft DealObject.
MVP: mostly structures manual input; LLM call is optional to
auto-fill type/b2b_b2c/description if user gives just a URL + notes.
"""

from __future__ import annotations
from deal_model import DealObject
from llm_client import LLMClient
from pydantic import ValidationError
from agents.schemas import CollectorResponse

SYSTEM_PROMPT = """You are the Deal Collector Agent inside Investment OS.
Your job: take raw, messy notes or structured API data about a digital
asset (SaaS, website, extension, API, etc.) and extract only what is
explicitly present — you do not evaluate, score, or judge the deal.

Rules:
- Do NOT invent numbers (price, revenue, traffic) that weren't given — use null.
- Do NOT invent text fields you can't infer — use "" (empty string), not placeholder text.
- If the same fact appears multiple times with conflicting values, use the most recent/explicit one and note the conflict in "description".
- "description": 1-2 sentence neutral summary of what the asset is.
- "problem_solved": what user pain it addresses — do not repeat "description".
- "target_users": who buys/uses it — do not repeat "problem_solved".
- "type" must be exactly one of: SaaS, site, extension, API, other.
- "b2b_b2c" must be exactly one of: B2B, B2C, Both, unknown.

Return ONLY valid JSON matching this schema (no markdown, no commentary, no extra keys):
{...}

Example:
Input: "nichesite about dog training DogiT, ~2k visits/month per notes, sells ebook + affiliate links, owner says ~$300/mo revenue ..."
Output: {
    "name": "DogiT",
    "url": "",
    "type": "site",
    "b2b_b2c": "B2C",
    "price": null,
    "revenue": 300,
    "traffic": 2000,
    "description": "...",
    "problem_solved": "...",
    "target_users": "...",
    "monetization_model": "ebook sales + affiliate"
}
"""



class CollectorAgent:
    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or LLMClient()

    def collect_manual(self, source: str = "Manual", **fields) -> DealObject:
        """Directly build a DealObject from explicit fields (no LLM)."""
        deal = DealObject(source=source, **fields)
        deal.set_status("COLLECTED", actor="collector")
        deal.agent_outputs["collector"] = {"mode": "manual", "input_fields": fields}
        return deal

    def collect_from_notes(self, raw_notes: str, source: str = "Manual") -> DealObject:
        """Use the LLM to structure messy raw notes into a DealObject."""
        try:
            raw_data = self.llm.complete_json(SYSTEM_PROMPT, raw_notes)
        except Exception:
            raw_data = {"description": raw_notes, "name": "UNPARSED"}

        if isinstance(raw_data, dict) and raw_data.get("_mock"):
            raw_data = {"name": "Draft from notes", "description": raw_notes}

        if not isinstance(raw_data, dict):
            raw_data = {"description": raw_notes, "name": "UNPARSED"}

        # Validate/coerce with pydantic; fall back to minimal data on failure
        try:
            parsed = CollectorResponse.parse_obj(raw_data)
            data = parsed.dict(exclude_none=True)
        except ValidationError:
            data = {"description": raw_notes, "name": "UNPARSED"}
        deal = DealObject(
            source=source,
            **{k: v for k, v in data.items() if k in DealObject.__dataclass_fields__},
        )
        deal.set_status("COLLECTED", actor="collector")
        deal.agent_outputs["collector"] = {"mode": "notes", "raw_notes": raw_notes}
        return deal
