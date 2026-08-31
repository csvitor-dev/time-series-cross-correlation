from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta


class TradingCalendar:
    def __init__(self, holidays: Iterable[date] = ()):
        self._holidays = set(holidays)

    def is_trading_day(self, day: date) -> bool:
        return day.weekday() < 5 and day not in self._holidays

    def trading_days(self, start: date, end: date) -> list[date]:
        days: list[date] = []
        current = start
        while current <= end:
            if self.is_trading_day(current):
                days.append(current)
            current += timedelta(days=1)
        return days
