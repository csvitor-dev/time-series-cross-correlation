from __future__ import annotations

import json
from pathlib import Path

from contracts.market_data_source import MarketDataSource
from contracts.ohlc import OHLCBar, OHLCRequest


class FixtureSource(MarketDataSource):
    def __init__(self, path: str | Path = "data/raw"):
        self._path = Path(path)
        self._bars: list[OHLCBar] | None = None

    def _load(self) -> list[OHLCBar]:
        if self._bars is None:
            files = (
                [self._path]
                if self._path.is_file()
                else sorted(self._path.glob("*.json"))
            )
            bars: list[OHLCBar] = []
            for file in files:
                items = json.loads(file.read_text(encoding="utf-8"))
                bars.extend(OHLCBar.model_validate(item) for item in items)
            self._bars = sorted(bars, key=lambda bar: bar.time)
        return self._bars

    def fetch_ohlc(self, request: OHLCRequest) -> list[OHLCBar]:
        window = [
            bar
            for bar in self._load()
            if request.start_time <= bar.time <= request.end_time
        ]
        if request.symbol:
            window = [b for b in window if b.symbol in (None, request.symbol)]
        return window
