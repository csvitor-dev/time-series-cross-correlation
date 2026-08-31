from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd


class PairStore:
    def __init__(self, processed: str | Path = "data/processed"):
        self._pairs = Path(processed) / "pairs"

    def _partition(self, reference_day: date) -> Path:
        return self._pairs / f"d_i={reference_day.isoformat()}" / "part.parquet"

    @staticmethod
    def _pairs_frame(reference_day: date, predecessors: list[date]) -> pd.DataFrame:
        rows = [
            {
                "d_i": reference_day.isoformat(),
                "d_k": d_k.isoformat(),
                "lag_days": (reference_day - d_k).days,
            }
            for d_k in sorted(predecessors)
            if d_k < reference_day
        ]
        return pd.DataFrame(rows, columns=["d_i", "d_k", "lag_days"])

    def build_pairs(self, reference_day: date, predecessors: list[date]) -> Path:
        target = self._partition(reference_day)
        target.parent.mkdir(parents=True, exist_ok=True)
        self._pairs_frame(reference_day, predecessors).to_parquet(target, index=False)
        return target

    def rebuild_current(self, reference_day: date, predecessors: list[date]) -> Path:
        return self.build_pairs(reference_day, predecessors)

    def read(self, reference_day: date) -> pd.DataFrame:
        return pd.read_parquet(self._partition(reference_day))
