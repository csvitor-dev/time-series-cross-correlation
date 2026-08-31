from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd


class CandleStore:
    def __init__(self, interim: str | Path = "data/interim", processed: str | Path = "data/processed"):
        self._interim = Path(interim)
        self._candles = Path(processed) / "candles"

    @property
    def current_day_file(self) -> Path:
        return self._interim / "current_day.parquet"

    def _partition(self, day: date) -> Path:
        return self._candles / f"date={day.isoformat()}" / "part.parquet"

    def write_current_day(self, frame: pd.DataFrame, day: date) -> Path:
        self._interim.mkdir(parents=True, exist_ok=True)
        frame = frame.assign(date=day.isoformat())
        frame.to_parquet(self.current_day_file, index=False)
        return self.current_day_file

    def seal_day(self, day: date, frame: pd.DataFrame | None = None) -> Path:
        target = self._partition(day)
        if target.exists():
            raise FileExistsError(f"partição selada e imutável já existe: {target}")
        if frame is None:
            frame = pd.read_parquet(self.current_day_file)
        frame = frame.assign(date=day.isoformat())
        target.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(target, index=False)
        return target

    def is_sealed(self, day: date) -> bool:
        return self._partition(day).exists()

    def read_days(self, days: list[date]) -> pd.DataFrame:
        frames = [
            pd.read_parquet(self._partition(day)) for day in days if self._partition(day).exists()
        ]
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True).sort_values(["date", "time"]).reset_index(drop=True)
