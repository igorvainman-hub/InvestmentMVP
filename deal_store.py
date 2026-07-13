"""
Deal Store — simple JSON-file-based persistence for DealObjects.
Each deal is stored as a separate JSON file under storage_dir/deals/<id>.json
"""

from __future__ import annotations
import json
import os
from typing import List, Optional

from deal_model import DealObject


class DealStore:
    def __init__(self, storage_dir: str = "./data"):
        self.storage_dir = storage_dir
        self.deals_dir = os.path.join(storage_dir, "deals")
        os.makedirs(self.deals_dir, exist_ok=True)

    def _path(self, deal_id: str) -> str:
        return os.path.join(self.deals_dir, f"{deal_id}.json")

    def save(self, deal: DealObject) -> str:
        deal.touch()
        with open(self._path(deal.id), "w", encoding="utf-8") as f:
            json.dump(deal.to_dict(), f, ensure_ascii=False, indent=2)
        return deal.id

    def load(self, deal_id: str) -> Optional[DealObject]:
        path = self._path(deal_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return DealObject.from_dict(json.load(f))

    def delete(self, deal_id: str) -> bool:
        path = self._path(deal_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def list_all(self) -> List[DealObject]:
        deals = []
        for fname in sorted(os.listdir(self.deals_dir)):
            if fname.endswith(".json"):
                with open(os.path.join(self.deals_dir, fname), "r", encoding="utf-8") as f:
                    deals.append(DealObject.from_dict(json.load(f)))
        return deals

    def list_by_decision(self, decision: str) -> List[DealObject]:
        return [d for d in self.list_all() if d.decision == decision]

    def sorted_by_score(self, descending: bool = True) -> List[DealObject]:
        return sorted(self.list_all(), key=lambda d: d.score, reverse=descending)
