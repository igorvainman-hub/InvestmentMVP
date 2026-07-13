"""
Deal Collector Agent
Turns raw input (url, description, price) into a draft DealObject.
MVP: mostly structures manual input; LLM call is optional to
auto-fill type/b2b_b2c/description if user gives just a URL + notes.
"""

from __future__ import annotations
from deal_model import DealObject
from llm_client import LLMClient

SYSTEM_PROMPT = """You are the Deal Collector Agent inside Investment OS.
Your job: take raw, messy notes about a digital asset (SaaS, website, \
extension, API, etc.) and structure them into a clean draft.
Do NOT invent numbers (price, revenue, traffic) that weren't given — leave blank/null if unknown.
Return ONLY valid JSON matching this schema (no markdown, no commentary):
{
  "name": "",
  "url": "",
  "type": "SaaS | site | extension | API | other",
  "b2b_b2c": "B2B | B2C | Both | unknown",
  "price": null,
  "revenue": null,
  "traffic": null,
  "description": "",
  "problem_solved": "",
  "target_users": "",
  "monetization_model": ""
}"""


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
        raw = self.llm.complete(SYSTEM_PROMPT, raw_notes, json_mode=True)
        import json
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"description": raw_notes, "name": "UNPARSED"}
        if data.get("_mock"):
            data = {
                "name": "Draft from notes",
                "description": raw_notes,
            }
        data.pop("_mock", None)
        data.pop("note", None)
        deal = DealObject(
            source=source,
            **{k: v for k, v in data.items() if k in DealObject.__dataclass_fields__},
        )
        deal.set_status("COLLECTED", actor="collector")
        deal.agent_outputs["collector"] = {"mode": "notes", "raw_notes": raw_notes, "parsed": data}
        return deal
