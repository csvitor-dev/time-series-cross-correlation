from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import date, datetime, time, timezone

from contracts.ohlc import OHLCBar, OHLCRequest

_SP = timezone.utc


class MarketDataSource(ABC):
    @abstractmethod
    def fetch_ohlc(self, request: OHLCRequest) -> list[OHLCBar]: ...

    def iter_days(
        self, symbol: str, timeframe: str, days: list[date]
    ) -> Iterator[tuple[date, list[OHLCBar]]]:
        for day in days:
            start = int(datetime.combine(day, time.min, _SP).timestamp())
            end = int(datetime.combine(day, time.max, _SP).timestamp())
            request = OHLCRequest(
                symbol=symbol,
                timeframe=timeframe,
                start_time=start,
                end_time=end,
                order_desc=False,
            )
            yield day, self.fetch_ohlc(request)
