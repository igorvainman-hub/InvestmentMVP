"""
Pipeline: INPUT -> Collector -> Analyzer -> Growth -> Scoring -> Store -> OUTPUT
"""

from __future__ import annotations
from deal_model import DealObject
from deal_store import DealStore
from llm_client import LLMClient
import traceback
from agents.collector import CollectorAgent
from agents.analyzer import AnalyzerAgent
from agents.growth import GrowthAgent
from agents.scoring import ScoringEngine
from agents.due_diligence import DueDiligenceAgent

# Due Diligence is only worth running for deals that look promising enough
# to actually spend seller/buyer time on.
DD_ELIGIBLE_DECISIONS = {"BUY", "WATCH"}
MANUAL_STATUSES = {"WATCHLIST", "ACQUIRED", "REJECTED"}


class InvestmentOSPipeline:
    def __init__(self, storage_dir: str = "./data", model: str = "gpt-4o-mini"):
        self.llm = LLMClient(model=model)
        self.store = DealStore(storage_dir=storage_dir)
        self.collector = CollectorAgent(self.llm)
        self.analyzer = AnalyzerAgent(self.llm)
        self.growth = GrowthAgent(self.llm)
        self.scorer = ScoringEngine(self.llm)
        self.due_diligence = DueDiligenceAgent(self.llm)

    def _log(self, deal: DealObject, step: str, detail: str = "") -> None:
        print(f"[pipeline] {step}: {detail or 'running'}")
        deal.log("pipeline", step, detail)

    def run_from_manual_fields(self, source: str = "Manual", **fields) -> DealObject:
        deal = self.collector.collect_manual(source=source, **fields)
        self._log(deal, "collector", "manual fields collected")
        return self._run_rest(deal)

    def run_from_notes(self, raw_notes: str, source: str = "Manual") -> DealObject:
        deal = self.collector.collect_from_notes(raw_notes, source=source)
        self._log(deal, "collector", "notes collected")
        return self._run_rest(deal)

    def _run_rest(self, deal: DealObject) -> DealObject:
        try:
            if self.llm.mock:
                self._log(deal, "pipeline", "mock mode: analysis skipped")
                deal.log("pipeline", "analysis_skipped", "OPENAI_API_KEY is not set; saved as a draft.")
                self.store.save(deal)
                return deal

            self._log(deal, "analyzer", "starting analysis")
            deal = self.analyzer.analyze(deal)
            self._log(deal, "analyzer", "completed")

            self._log(deal, "growth", "starting growth analysis")
            deal = self.growth.find_growth(deal)
            self._log(deal, "growth", "completed")

            self._log(deal, "scoring", "starting scoring")
            deal = self.scorer.score(deal)
            self._log(deal, "scoring", f"decision={deal.decision} score={deal.score}")

            if deal.decision in DD_ELIGIBLE_DECISIONS:
                self._log(deal, "due_diligence", "starting review")
                deal = self.due_diligence.review(deal)
                self._log(deal, "due_diligence", "completed")

            self._log(deal, "store", "saving deal")
            self.store.save(deal)
            self._log(deal, "store", "saved")
            return deal
        except Exception as exc:
            print(f"[pipeline] ERROR: {exc}")
            print(traceback.format_exc())
            raise

    def rerun_analysis(self, deal_id: str) -> DealObject:
        """Re-run analyzer/growth/scoring(/DD) on an existing deal (e.g. after editing fields)."""
        deal = self.store.load(deal_id)
        if deal is None:
            raise ValueError(f"Deal {deal_id} not found")
        previous_status = deal.status if deal.status in MANUAL_STATUSES else None
        deal = self._run_rest(deal)
        if previous_status:
            deal.set_status(previous_status, actor="pipeline")
            deal.log("pipeline", "manual_status_restored", previous_status)
            self.store.save(deal)
        return deal

    def set_status(self, deal_id: str, new_status: str, actor: str = "user") -> DealObject:
        """Manually move a deal to WATCHLIST / ACQUIRED / REJECTED etc."""
        deal = self.store.load(deal_id)
        if deal is None:
            raise ValueError(f"Deal {deal_id} not found")
        deal.set_status(new_status, actor=actor)
        self.store.save(deal)
        return deal
