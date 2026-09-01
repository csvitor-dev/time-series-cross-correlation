from __future__ import annotations

from pathlib import Path

import pandas as pd


class CorrelationStore:
    def __init__(self, processed: str | Path = "data/processed"):
        self._root = Path(processed) / "correlations"

    def _dir(self, method: str) -> Path:
        return self._root / f"method={method}"

    def write(self, method: str, pairs: pd.DataFrame, matrix: pd.DataFrame) -> Path:
        target = self._dir(method)
        target.mkdir(parents=True, exist_ok=True)
        pairs.to_parquet(target / "pairs.parquet", index=False)
        matrix.to_parquet(target / "matrix.parquet")
        return target

    def read_pairs(self, method: str) -> pd.DataFrame:
        return pd.read_parquet(self._dir(method) / "pairs.parquet")

    def read_matrix(self, method: str) -> pd.DataFrame:
        return pd.read_parquet(self._dir(method) / "matrix.parquet")

    def heatmap_path(self, method: str) -> Path:
        return self._root / f"heatmap_{method}.png"
