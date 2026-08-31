from datetime import date

import pandas as pd
import pytest

from storage.candle_store import CandleStore

_FRAME = pd.DataFrame({"time": [1, 2], "close": [10.0, 11.0]})


def test_second_seal_of_same_day_raises(tmp_path):
    store = CandleStore(tmp_path / "interim", tmp_path / "processed")
    day = date(2026, 6, 17)

    store.seal_day(day, _FRAME)
    assert store.is_sealed(day)

    with pytest.raises(FileExistsError):
        store.seal_day(day, _FRAME)
