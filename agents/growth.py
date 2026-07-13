"""
Growth Agent
Finds concrete levers to increase the asset's value: features to add,
what to automate, where x2-x5 growth could come from.
Fills: growth_levers.
"""

from __future__ import annotations
import json
from deal_model import DealObject
from llm_client import LLMClient
from pydantic import ValidationError
from agents.schemas import GrowthResponse

SYSTEM_PROMPT = """You are the Growth Agent inside Investment OS.
Given an already-analyzed Deal Object (JSON, includes strengths/weaknesses/risks),
propose concrete, actionable growth levers — things a solo operator with limited \
time (a few hours on weekdays, partial weekends) and AI tools could realistically execute.
Prioritize leverage: automation, AI-driven features, pricing/packaging changes, \
distribution channels — not vague advice like "improve marketing".
Return ONLY valid JSON (no markdown, no commentary):
{
  "growth_levers": ["specific action 1", "specific action 2", "..."],
  "quick_wins": ["things doable in under a week"],
  "estimated_upside": "short qualitative estimate, e.g. '2-3x revenue in 6 months if X and Y are done'"
}"""


class GrowthAgent:
    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or LLMClient()

    def find_growth(self, deal: DealObject) -> DealObject:
        deal_json = json.dumps(deal.to_dict(), ensure_ascii=False, indent=2)
        try:
            raw = self.llm.complete_json(SYSTEM_PROMPT, deal_json)
        except Exception as exc:
            raise ValueError("Growth agent failed to produce valid JSON") from exc

        try:
            validated = GrowthResponse.parse_obj(raw)
        except ValidationError as exc:
            raise ValueError("Growth agent returned invalid structure") from exc

        data = validated.dict()
        deal.growth_levers = data.get("growth_levers", deal.growth_levers)
        deal.agent_outputs["growth"] = data

        return deal
