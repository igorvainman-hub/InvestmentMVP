"""
Deal Object — core data model for Investment OS.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime
import uuid


STATUS_FLOW = ["NEW", "COLLECTED", "ANALYZED", "SCORED", "WATCHLIST", "ACQUIRED", "REJECTED"]


@dataclass
class DealObject:
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Lifecycle
    status: str = "NEW"  # NEW -> COLLECTED -> ANALYZED -> SCORED -> WATCHLIST | ACQUIRED | REJECTED
    source: str = "Manual"  # Acquire | Flippa | GitHub | Reddit | Twitter | Manual | other

    # Basic info
    name: str = ""
    url: str = ""
    type: str = ""              # SaaS | site | extension | API | other
    b2b_b2c: str = ""           # B2B | B2C | Both
    price: Optional[float] = None
    revenue: Optional[float] = None   # monthly, if known
    traffic: Optional[str] = None

    # Descriptive
    description: str = ""
    problem_solved: str = ""
    target_users: str = ""
    monetization_model: str = ""

    # Analysis (filled by Analyzer/Growth agents)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    ai_opportunities: List[str] = field(default_factory=list)
    growth_levers: List[str] = field(default_factory=list)
    competition_level: str = ""  # low | medium | high

    # Scoring (filled by Scoring Engine)
    score_breakdown: dict = field(default_factory=dict)  # e.g. {"market_potential": 20, ...}
    score: int = 0
    confidence: int = 0  # 0-100, how much data backs this score
    decision: str = ""  # BUY | WATCH | IGNORE
    notes: str = ""

    # Missing information / Due Diligence
    missing_info: List[str] = field(default_factory=list)       # what data is missing
    questions_for_seller: List[str] = field(default_factory=list)
    due_diligence_risks: List[str] = field(default_factory=list)

    # Per-agent raw outputs (replaces cramming everything into notes)
    agent_outputs: dict = field(default_factory=dict)  # {"collector": {...}, "analyzer": {...}, ...}

    # Change history: list of {"timestamp": "...", "actor": "...", "action": "...", "detail": "..."}
    history: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "DealObject":
        known = {k: v for k, v in data.items() if k in DealObject.__dataclass_fields__}
        return DealObject(**known)

    def touch(self):
        self.updated_at = datetime.utcnow().isoformat()

    def log(self, actor: str, action: str, detail: str = ""):
        """Append an entry to the change history."""
        self.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "actor": actor,
            "action": action,
            "detail": detail,
        })

    def set_status(self, new_status: str, actor: str = "system"):
        if new_status not in STATUS_FLOW:
            raise ValueError(f"Unknown status '{new_status}'. Must be one of {STATUS_FLOW}")
        old = self.status
        self.status = new_status
        self.log(actor, "status_change", f"{old} -> {new_status}")
