from __future__ import annotations

from datetime import date
from pathlib import Path

from acquisition.fixture_source import FixtureSource
from acquisition.qdata_client import QDataHTTPSource
from config import PipelineConfig
from contracts.market_data_source import MarketDataSource
from preprocessing.clean import clean
from preprocessing.trading_calendar import TradingCalendar
from storage.candle_store import CandleStore
from storage.manifest import Manifest
from storage.pair_store import PairStore
from utils.hashing import sha256_paths


def build_source(config: PipelineConfig, offline: bool) -> MarketDataSource:
    if offline or config.source == "fixture":
        return FixtureSource(config.paths.raw)
    return QDataHTTPSource()


def run(config: PipelineConfig, *, offline: bool = False, today: date | None = None) -> dict:
    calendar = TradingCalendar(config.holidays)
    source = build_source(config, offline)
    candles = CandleStore(config.paths.interim, config.paths.processed)
    pairs = PairStore(config.paths.processed)
    manifest = Manifest(config.paths.processed)

    all_days = calendar.trading_days(config.period.start, config.period.end)
    window = all_days[-config.reference_window_n :]
    current_day = today or window[-1]

    sealed: list[date] = []
    for day, bars in source.iter_days(config.symbol, config.timeframe, window):
        if not bars:
            continue
        frame = clean(bars)
        candles.write_current_day(frame, day)
        if day < current_day:
            if not candles.is_sealed(day):
                candles.seal_day(day, frame)
            sealed.append(day)

    processed_window = sealed + [current_day]
    for reference_day in processed_window:
        predecessors = [d for d in processed_window if d < reference_day]
        pairs.build_pairs(reference_day, predecessors)

    raw_files = sorted(Path(config.paths.raw).glob("*.json"))
    manifest_file = manifest.write(
        symbol=config.symbol,
        timeframe=config.timeframe,
        period={"start": config.period.start.isoformat(), "end": config.period.end.isoformat()},
        reference_window_n=config.reference_window_n,
        source="fixture" if offline or config.source == "fixture" else config.source,
        input_sha256=sha256_paths(raw_files) if raw_files else "",
        sealed_days=[d.isoformat() for d in sealed],
    )
    return {
        "sealed_days": sealed,
        "current_day": current_day,
        "manifest": manifest_file,
    }
