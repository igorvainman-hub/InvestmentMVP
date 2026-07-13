"""
Deal Analyzer Agent — the "main brain".
Analyzes the business: product, market, monetization, weaknesses, AI potential.
Fills: strengths, weaknesses, risks, ai_opportunities, competition_level.
"""

from __future__ import annotations
import json
from deal_model import DealObject
from llm_client import LLMClient

SYSTEM_PROMPT = """You are the Deal Analyzer Agent inside Investment OS — the main analytical brain.
Given a structured Deal Object (JSON), analyze the underlying business critically and honestly.
Do not be optimistic by default — flag real risks and weaknesses.
Also identify what key information is MISSING that would be needed for a confident decision
(e.g. MRR history, churn, customer count, tech stack, owner involvement, traffic source).
Return ONLY valid JSON with these keys (no markdown, no commentary):
{
  "strengths": ["..."],
  "weaknesses": ["..."],
  "risks": ["..."],
  "ai_opportunities": ["..."],
  "competition_level": "low | medium | high",
  "missing_info": ["specific missing data point 1", "..."],
  "analysis_summary": "2-4 sentence plain-language summary of what this business is and whether it's worth pursuing"
}"""


class AnalyzerAgent:
    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or LLMClient()

    def analyze(self, deal: DealObject) -> DealObject:
        deal_json = json.dumps(deal.to_dict(), ensure_ascii=False, indent=2)
        raw = self.llm.complete(SYSTEM_PROMPT, deal_json, json_mode=True)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}

        deal.strengths = data.get("strengths", deal.strengths)
        deal.weaknesses = data.get("weaknesses", deal.weaknesses)
        deal.risks = data.get("risks", deal.risks)
        deal.ai_opportunities = data.get("ai_opportunities", deal.ai_opportunities)
        deal.competition_level = data.get("competition_level", deal.competition_level)
        deal.missing_info = data.get("missing_info", deal.missing_info)

        deal.agent_outputs["analyzer"] = data
        deal.set_status("ANALYZED", actor="analyzer")

        return deal
