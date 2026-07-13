"""
Due Diligence Agent
Answers the question the other four agents don't: "what do I still need
to find out before actually buying this?"

Fills: missing_info (extends Analyzer's version with DD-specific gaps),
due_diligence_risks, questions_for_seller.

Runs AFTER Scoring, since it's most useful once a deal looks promising
enough (WATCH/BUY) to be worth the seller's and buyer's time.
"""

from __future__ import annotations
import json
from deal_model import DealObject
from llm_client import LLMClient
from pydantic import ValidationError
from agents.schemas import DueDiligenceResponse

SYSTEM_PROMPT = """You are the Due Diligence Agent inside Investment OS.
The other agents already answered: what is this? is it a good business? how to grow it? \
buy/watch/ignore? Your job is different: figure out what the buyer still needs to \
verify before actually committing money, and what to ask the seller.

Think like a skeptical buyer doing pre-purchase diligence on a small digital asset.
Consider things like: MRR history and trend, churn, customer concentration, \
hosting/infrastructure cost, tech debt, code quality/ownership, legal risks (licensing, \
trademarks, data privacy), owner time commitment required, traffic source dependency \
(e.g. single SEO keyword, single ad channel), and reason for selling.

Given the Deal Object (JSON, already analyzed and scored), return ONLY valid JSON:
{
  "missing_info": ["specific data point still needed 1", "..."],
  "due_diligence_risks": ["risk that needs verification before buying 1", "..."],
  "questions_for_seller": ["direct question to ask the seller 1", "..."],
  "dd_summary": "1-2 sentence summary of the biggest open question before buying"
}"""


class DueDiligenceAgent:
    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or LLMClient()

    def review(self, deal: DealObject) -> DealObject:
        deal_json = json.dumps(deal.to_dict(), ensure_ascii=False, indent=2)

        try:
            raw = self.llm.complete_json(SYSTEM_PROMPT, deal_json)
        except Exception as exc:
            raise ValueError("Due diligence agent failed to produce valid JSON") from exc

        try:
            validated = DueDiligenceResponse.parse_obj(raw)
        except ValidationError as exc:
            raise ValueError("Due diligence agent returned invalid structure") from exc

        data = validated.dict()

        # Merge with (don't overwrite) Analyzer's missing_info — dedupe while preserving order
        combined_missing = list(deal.missing_info) + list(data.get("missing_info", []))
        deal.missing_info = list(dict.fromkeys(combined_missing))

        deal.due_diligence_risks = data.get("due_diligence_risks", deal.due_diligence_risks)
        deal.questions_for_seller = data.get("questions_for_seller", deal.questions_for_seller)

        deal.agent_outputs["due_diligence"] = data
        deal.log("due_diligence", "reviewed", data.get("dd_summary", ""))

        return deal
