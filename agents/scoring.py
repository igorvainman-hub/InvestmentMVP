"""
Scoring Engine
Combines rules + LLM judgment into a 0-100 score and a BUY/WATCH/IGNORE decision.

Score = Market Potential (0-25) + AI Leverage (0-25) + Ease of Improvement (0-20)
        + Revenue Stability (0-20) + Entry Cost Fit (0-10)

The sub-scores are produced by the LLM (since they require judgment about
the specific business), but the final aggregation and decision thresholds
are deterministic rules — so the decision is always explainable and
reproducible from the breakdown.
"""

from __future__ import annotations
import json
from deal_model import DealObject
from llm_client import LLMClient

SYSTEM_PROMPT = """You are the Scoring Engine inside Investment OS.
Given a fully-analyzed Deal Object (JSON: description, strengths, weaknesses, \
risks, ai_opportunities, growth_levers, competition_level, price, revenue, missing_info), \
score it on these dimensions. Be strict and realistic, not generous.
Also estimate a confidence level (0-100): how much this score can be trusted given
how much solid data (revenue, traffic, price, etc.) was actually available vs. missing/unknown.
A deal with many unknowns (see missing_info) should get LOW confidence even if the score looks good.
Return ONLY valid JSON with integer sub-scores in these exact ranges:
{
  "market_potential": 0-25,
  "ai_leverage": 0-25,
  "ease_of_improvement": 0-20,
  "revenue_stability": 0-20,
  "entry_cost_fit": 0-10,
  "confidence": 0-100,
  "reasoning": "1-3 sentences justifying the sub-scores, referencing specific facts from the deal"
}"""

DECISION_THRESHOLDS = {
    "BUY": 70,     # score >= 70
    "WATCH": 45,   # 45 <= score < 70
    # below 45 -> IGNORE
}


class ScoringEngine:
    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or LLMClient()

    def score(self, deal: DealObject) -> DealObject:
        deal_json = json.dumps(deal.to_dict(), ensure_ascii=False, indent=2)
        raw = self.llm.complete(SYSTEM_PROMPT, deal_json, json_mode=True)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("Scoring engine returned invalid JSON") from exc
        if not isinstance(data, dict) or not data:
            raise ValueError("Scoring engine returned an empty JSON object")

        breakdown = {
            "market_potential": self._clamp(data.get("market_potential", 0), 25),
            "ai_leverage": self._clamp(data.get("ai_leverage", 0), 25),
            "ease_of_improvement": self._clamp(data.get("ease_of_improvement", 0), 20),
            "revenue_stability": self._clamp(data.get("revenue_stability", 0), 20),
            "entry_cost_fit": self._clamp(data.get("entry_cost_fit", 0), 10),
        }
        total = sum(breakdown.values())
        confidence = self._clamp(data.get("confidence", 0), 100)

        deal.score_breakdown = breakdown
        deal.score = total
        deal.confidence = confidence
        deal.decision = self._decide(total)
        deal.agent_outputs["scoring"] = data
        deal.set_status("SCORED", actor="scoring")

        return deal

    @staticmethod
    def _clamp(value, max_value) -> int:
        try:
            value = int(value)
        except (TypeError, ValueError):
            value = 0
        return max(0, min(value, max_value))

    @staticmethod
    def _decide(total: int) -> str:
        if total >= DECISION_THRESHOLDS["BUY"]:
            return "BUY"
        if total >= DECISION_THRESHOLDS["WATCH"]:
            return "WATCH"
        return "IGNORE"
