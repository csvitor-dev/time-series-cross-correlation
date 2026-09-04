from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from config import AnalysisConfig


@dataclass(frozen=True)
class DaySeries:
    day: date
    values: np.ndarray
    coverage: float


def _minute_grid(cfg: AnalysisConfig) -> np.ndarray:
    start = pd.Timestamp(cfg.window.start)
    end = pd.Timestamp(cfg.window.end)
    start_min = start.hour * 60 + start.minute
    end_min = end.hour * 60 + end.minute
    return np.arange(start_min, end_min + 1)


def day_series(frame: pd.DataFrame, cfg: AnalysisConfig) -> DaySeries:
    grid = _minute_grid(cfg)
    local = (
        pd.to_datetime(frame["time"], unit="s", utc=True)
        .dt.tz_convert(cfg.window.tz)
    )
    minute = local.dt.hour * 60 + local.dt.minute

    day = pd.DataFrame(
        {
            "minute": minute.to_numpy(),
            "close": frame["close"].to_numpy(dtype=float),
            "imputed": frame.get("imputed", pd.Series(False, index=frame.index)).to_numpy(),
        }
    )
    day = day[day["minute"].isin(grid)].drop_duplicates("minute", keep="last")
    day = day.set_index("minute").reindex(grid)

    imputed = day["imputed"].fillna(True).astype(bool).to_numpy()
    real = day["close"].notna().to_numpy() & ~imputed
    coverage = float(real.sum()) / len(grid)

    close = day["close"].ffill().bfill()
    log_return = np.log(close / close.shift(1)).to_numpy()[1:]
    log_return = np.nan_to_num(log_return, nan=0.0, posinf=0.0, neginf=0.0)

    if cfg.value == "close":
        values = close.to_numpy()[1:]
    elif cfg.value == "zscore":
        base = close.to_numpy()[1:]
        std = base.std()
        values = (base - base.mean()) / std if std else np.zeros_like(base)
    else:
        values = log_return

    return DaySeries(day=_frame_day(frame), values=values, coverage=coverage)


def _frame_day(frame: pd.DataFrame) -> date:
    if "date" in frame.columns:
        return date.fromisoformat(str(frame["date"].iloc[0]))
    return pd.to_datetime(frame["time"].iloc[0], unit="s", utc=True).date()


def align(a: DaySeries, b: DaySeries) -> tuple[np.ndarray, np.ndarray]:
    n = min(len(a.values), len(b.values))
    return a.values[:n], b.values[:n]
