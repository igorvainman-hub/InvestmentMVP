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
Given an already-analyzed Deal Object (JSON, includes strengths/weaknesses/risks/missing_info),
propose concrete, actionable growth levers — things a solo operator with limited 
time (a few hours on weekdays, partial weekends) and standard AI tools (LLM APIs, 
no custom ML training) could realistically execute.

Prioritize leverage: automation, AI-driven features, pricing/packaging changes, 
distribution channels — not vague advice like "improve marketing".

Base your suggestions ONLY on the provided Deal Object. Do not assume market facts 
or competitor behavior not stated in the input. Avoid proposing levers that ignore 
or contradict risks already identified in "risks" or "weaknesses".

Limit to the 3-5 highest-leverage levers, not an exhaustive list.

Return ONLY valid JSON (no markdown, no commentary):
{
  "growth_levers": ["specific action 1", "specific action 2", "..."],
  "quick_wins": ["things doable in under a week"],
  "growth_confidence": "high | medium | low — how confident these levers are likely to move the needle, given how much relevant data was available",
  "growth_rationale": "1-2 sentences explaining what these levers depend on
(e.g. 'assumes traffic is organic and improvable via SEO')"
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
