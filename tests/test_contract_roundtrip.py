import json
from datetime import date

import pandas as pd
from conftest import FIXTURES

from contracts.ohlc import OHLCBar
from preprocessing.clean import clean
from storage.candle_store import CandleStore


def test_camelcase_payload_parses_into_contract():
    items = json.loads((FIXTURES / "ohlc_winj26_sample.json").read_text())
    bars = [OHLCBar.model_validate(item) for item in items]

    assert bars[0].tick_volume == items[0]["tickVolume"]
    assert bars[0].time_utc == items[0]["timeUtc"]
    assert bars[0].real_volume == items[0]["realVolume"]
    assert bars[0].source_id == items[0]["sourceId"]


def test_snake_case_payload_parses_into_contract():
    bar = OHLCBar.model_validate(
        {
            "time": 1,
            "time_utc": "2026-06-30T13:00:00Z",
            "time_sp": "2026-06-30T10:00:00-03:00",
            "open": 1.0,
            "high": 1.0,
            "low": 1.0,
            "close": 1.0,
            "tick_volume": 3,
            "spread": 5,
            "real_volume": 9,
        }
    )
    assert bar.tick_volume == 3 and bar.real_volume == 9


def test_roundtrip_through_sealed_parquet(tmp_path):
    items = json.loads((FIXTURES / "ohlc_winj26_sample.json").read_text())
    bars = [OHLCBar.model_validate(item) for item in items]
    frame = clean(bars)

    store = CandleStore(tmp_path / "interim", tmp_path / "processed")
    day = date(2026, 6, 30)
    store.write_current_day(frame, day)
    store.seal_day(day)

    back = store.read_days([day])
    assert list(back["close"]) == list(frame["close"])
    assert back["tick_volume"].dtype == frame["tick_volume"].dtype
