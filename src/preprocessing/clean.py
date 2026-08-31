from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from contracts.ohlc import OHLCBar

_COLUMNS = [
    "time",
    "time_utc",
    "time_sp",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread",
    "real_volume",
    "symbol",
    "timeframe",
    "source_id",
]


def to_frame(bars: Iterable[OHLCBar]) -> pd.DataFrame:
    frame = pd.DataFrame([bar.model_dump() for bar in bars])
    if frame.empty:
        return pd.DataFrame(columns=_COLUMNS)
    return frame.reindex(columns=[c for c in _COLUMNS if c in frame.columns])


def clean(bars: Iterable[OHLCBar]) -> pd.DataFrame:
    frame = to_frame(bars)
    if frame.empty:
        return frame

    frame = (
        frame.drop_duplicates(subset="time", keep="last")
        .sort_values("time")
        .reset_index(drop=True)
    )
    frame["time_utc"] = pd.to_datetime(frame["time_utc"], utc=True)
    frame["time_sp"] = pd.to_datetime(frame["time_sp"])

    grid = pd.Index(
        range(int(frame["time"].iloc[0]), int(frame["time"].iloc[-1]) + 60, 60), name="time"
    )
    dtypes = frame.dtypes.to_dict()
    frame = (
        frame.set_index("time")
        .reindex(grid)
        .bfill()
        .ffill()
        .rename_axis("time")
        .reset_index()
    )
    return frame.astype(dtypes)
