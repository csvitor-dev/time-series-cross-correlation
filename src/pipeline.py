from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from acquisition.fixture_source import FixtureSource
from acquisition.qdata_client import QDataHTTPSource
from analysis.cross_correlation import AnalysisOutput, CrossCorrelationEngine
from config import PipelineConfig
from contracts.market_data_source import MarketDataSource
from preprocessing.clean import clean
from preprocessing.trading_calendar import TradingCalendar
from storage.candle_store import CandleStore
from storage.correlation_store import CorrelationStore
from storage.manifest import Manifest
from storage.pair_store import PairStore
from utils.hashing import sha256_paths
from visualization.heatmap import plot_heatmap


def build_source(config: PipelineConfig, offline: bool) -> MarketDataSource:
    if offline or config.source == "fixture":
        return FixtureSource(config.paths.raw)
    return QDataHTTPSource()


def _window_days(config: PipelineConfig) -> list[date]:
    all_days = TradingCalendar(config.holidays).trading_days(
        config.period.start, config.period.end
    )
    return all_days[-config.reference_window_n :]


def _load_frames(config: PipelineConfig, days: list[date]) -> dict[date, pd.DataFrame]:
    candles = CandleStore(config.paths.interim, config.paths.processed)
    frames: dict[date, pd.DataFrame] = {}
    for day in days:
        if candles.is_sealed(day):
            frames[day] = candles.read_days([day])
    current = candles.current_day_file
    if current.exists():
        frame = pd.read_parquet(current)
        frames[date.fromisoformat(str(frame["date"].iloc[0]))] = frame
    return frames


def analyze(config: PipelineConfig, *, days: list[date] | None = None) -> AnalysisOutput:
    days = days or _window_days(config)
    frames = _load_frames(config, days)

    engine = CrossCorrelationEngine(config.analysis)
    output = engine.run(frames)

    store = CorrelationStore(config.paths.processed)
    for method in config.analysis.methods:
        store.write(method, output.pairs[method], output.matrix[method])
        plot_heatmap(output.matrix[method], method, store.heatmap_path(method))
    return output


def _analysis_manifest(config: PipelineConfig, output: AnalysisOutput) -> dict:
    method = config.analysis.methods[0]
    return {
        "value": config.analysis.value,
        "methods": config.analysis.methods,
        "window": config.analysis.window.model_dump(),
        "min_coverage": config.analysis.min_coverage,
        "pairs": int(len(output.pairs[method])),
        "coverage": {d.isoformat(): round(c, 4) for d, c in sorted(output.coverage.items())},
    }


def run(config: PipelineConfig, *, offline: bool = False, today: date | None = None) -> dict:
    source = build_source(config, offline)
    candles = CandleStore(config.paths.interim, config.paths.processed)
    pairs = PairStore(config.paths.processed)
    manifest = Manifest(config.paths.processed)

    window = _window_days(config)
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

    output = analyze(config, days=window)

    raw_files = sorted(Path(config.paths.raw).glob("*.json"))
    manifest_file = manifest.write(
        symbol=config.symbol,
        timeframe=config.timeframe,
        period={"start": config.period.start.isoformat(), "end": config.period.end.isoformat()},
        reference_window_n=config.reference_window_n,
        source="fixture" if offline or config.source == "fixture" else config.source,
        input_sha256=sha256_paths(raw_files) if raw_files else "",
        sealed_days=[d.isoformat() for d in sealed],
        analysis=_analysis_manifest(config, output),
    )
    return {
        "sealed_days": sealed,
        "current_day": current_day,
        "manifest": manifest_file,
        "analysis": output,
    }
