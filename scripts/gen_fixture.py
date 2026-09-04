from __future__ import annotations

import json
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from config import PipelineConfig
from preprocessing.trading_calendar import TradingCalendar

SP = timezone(timedelta(hours=-3))
SESSION_OPEN = time(9, 0)
BASE_PRICE = 129000.0
SEED = 42


def _bars_per_day(config: PipelineConfig) -> int:
    start = config.analysis.window.start
    end = config.analysis.window.end
    to_min = lambda s: int(s[:2]) * 60 + int(s[3:])
    return to_min(end) - to_min(start) + 1


def _day_returns(rng: np.random.Generator, common: np.ndarray, weight: float) -> np.ndarray:
    idio = rng.normal(0.0, 1.0, size=len(common))
    mix = weight * common + np.sqrt(max(1.0 - weight * weight, 0.0)) * idio
    return mix * 0.0006


def day_bars(day: date, returns: np.ndarray) -> list[dict]:
    start = datetime.combine(day, SESSION_OPEN, SP).astimezone(timezone.utc)
    price = BASE_PRICE
    bars = []
    for i, r in enumerate(returns):
        price *= float(np.exp(r))
        ts = start + timedelta(minutes=i)
        bars.append(
            {
                "symbol": "WINJ26",
                "timeframe": "M1",
                "sourceId": "mt5-demo",
                "time": int(ts.timestamp()),
                "timeUtc": ts.isoformat().replace("+00:00", "Z"),
                "timeSp": ts.astimezone(SP).isoformat(),
                "open": round(price, 1),
                "high": round(price + abs(r) * price, 1),
                "low": round(price - abs(r) * price, 1),
                "close": round(price, 1),
                "tickVolume": int(1200 + 300 * abs(r) / 0.0006),
                "spread": 5,
                "realVolume": int(12000 + 3000 * abs(r) / 0.0006),
            }
        )
    return bars


def main() -> None:
    config = PipelineConfig.load("config/pipeline.yaml")
    calendar = TradingCalendar(config.holidays)
    days = calendar.trading_days(config.period.start, config.period.end)[
        -config.reference_window_n :
    ]

    bars_per_day = _bars_per_day(config)
    rng = np.random.default_rng(SEED)
    common = rng.normal(0.0, 1.0, size=bars_per_day)
    weights = np.linspace(0.9, -0.4, num=len(days))

    full: list[dict] = []
    per_day: list[list[dict]] = []
    for day, weight in zip(days, weights):
        bars = day_bars(day, _day_returns(rng, common, float(weight)))
        per_day.append(bars)
        full.extend(bars)

    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("data/raw/ohlc_winj26_10d.json").write_text(json.dumps(full), encoding="utf-8")

    Path("tests/fixtures").mkdir(parents=True, exist_ok=True)
    Path("tests/fixtures/ohlc_winj26_sample.json").write_text(
        json.dumps(per_day[-1][:12], indent=2), encoding="utf-8"
    )
    print(f"{len(full)} barras em {len(days)} dias -> data/raw/ohlc_winj26_10d.json")


if __name__ == "__main__":
    main()
