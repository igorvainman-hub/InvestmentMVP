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
from pydantic import ValidationError
from agents.schemas import ScoringResponse

SYSTEM_PROMPT = """You are the Scoring Engine inside Investment OS.
Given a fully-analyzed Deal Object (JSON: description, strengths, weaknesses, \
risks, ai_opportunities, growth_levers, competition_level, price, revenue, missing_info), \
score it on 5 dimensions. Base scores ONLY on the provided data — do not use \
outside knowledge about the company or market.

Be strict and realistic, not generous. Higher scores require explicit supporting \
evidence in the Deal Object, not assumptions.

Scoring criteria (each range reflects the dimension's relative weight):

- market_potential (0-25): based on competition_level, described demand/niche size, \
and traffic trend if mentioned. No evidence of demand → score in lower third.
- ai_leverage (0-25): based on the number and specificity of ai_opportunities. \
Generic or absent ai_opportunities → score in lower third.
- ease_of_improvement (0-20): based on weaknesses and growth_levers — how much \
effort/expertise the fixes described would require for a solo, part-time operator.
- revenue_stability (0-20): based on revenue figures, monetization_model, and any \
stability-related risks flagged. Single/unclear revenue source or flagged volatility \
risk → score in lower third.
- entry_cost_fit (0-10): based on price alone, in absence of a stated budget — \
score relative to typical micro-SaaS/small-asset acquisition ranges, and say so \
explicitly in reasoning if budget context is missing.

Also estimate "confidence" (0-100): how much this score can be trusted given \
how much solid data (revenue, traffic, price, etc.) was actually available vs. \
missing/unknown, per missing_info. A deal with many unknowns should get LOW \
confidence even if the score looks good.

All sub-scores must be whole integers, no decimals.

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
        try:
            raw = self.llm.complete_json(SYSTEM_PROMPT, deal_json)
        except Exception as exc:
            raise ValueError("Scoring engine failed to produce valid JSON") from exc

        try:
            validated = ScoringResponse.parse_obj(raw)
        except ValidationError as exc:
            raise ValueError("Scoring engine returned invalid structure") from exc

        breakdown = {
            "market_potential": int(validated.market_potential),
            "ai_leverage": int(validated.ai_leverage),
            "ease_of_improvement": int(validated.ease_of_improvement),
            "revenue_stability": int(validated.revenue_stability),
            "entry_cost_fit": int(validated.entry_cost_fit),
        }
        total = sum(breakdown.values())
        confidence = int(validated.confidence)

        deal.score_breakdown = breakdown
        deal.score = total
        deal.confidence = confidence
        deal.decision = self._decide(total)
        deal.agent_outputs["scoring"] = validated.dict()
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
