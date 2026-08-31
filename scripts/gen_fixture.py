from __future__ import annotations

import json
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from config import PipelineConfig
from preprocessing.trading_calendar import TradingCalendar

SP = timezone(timedelta(hours=-3))
BARS_PER_DAY = 6
BASE_PRICE = 129000.0


def day_bars(day: date, seed: int) -> list[dict]:
    start = datetime.combine(day, time(13, 0), timezone.utc)
    bars = []
    for i in range(BARS_PER_DAY):
        ts = start + timedelta(minutes=i)
        price = BASE_PRICE + seed * 50 + i * 25
        bars.append(
            {
                "symbol": "WINJ26",
                "timeframe": "M1",
                "sourceId": "mt5-demo",
                "time": int(ts.timestamp()),
                "timeUtc": ts.isoformat().replace("+00:00", "Z"),
                "timeSp": ts.astimezone(SP).isoformat(),
                "open": price,
                "high": price + 30,
                "low": price - 20,
                "close": price + 10,
                "tickVolume": 1500 + i * 10,
                "spread": 5,
                "realVolume": 15000 + i * 100,
            }
        )
    return bars


def main() -> None:
    config = PipelineConfig.load("config/pipeline.yaml")
    calendar = TradingCalendar(config.holidays)
    days = calendar.trading_days(config.period.start, config.period.end)[
        -config.reference_window_n :
    ]

    full = [bar for n, day in enumerate(days) for bar in day_bars(day, n)]
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("data/raw/ohlc_winj26_10d.json").write_text(json.dumps(full, indent=2), encoding="utf-8")

    Path("tests/fixtures").mkdir(parents=True, exist_ok=True)
    Path("tests/fixtures/ohlc_winj26_sample.json").write_text(
        json.dumps(day_bars(days[-1], len(days) - 1), indent=2), encoding="utf-8"
    )
    print(f"{len(full)} barras em {len(days)} dias -> data/raw/ohlc_winj26_10d.json")


if __name__ == "__main__":
    main()
