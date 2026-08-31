from datetime import date

from storage.pair_store import PairStore


def _days(*d):
    return [date(2026, 6, x) for x in d]


def test_pairs_only_reference_predecessors(tmp_path):
    store = PairStore(tmp_path / "processed")
    window = _days(17, 18, 19, 22, 30)
    store.build_pairs(date(2026, 6, 30), window)

    frame = store.read(date(2026, 6, 30))
    assert set(frame["d_k"]) == {"2026-06-17", "2026-06-18", "2026-06-19", "2026-06-22"}
    assert (frame["d_i"] > frame["d_k"]).all()
    assert list(frame["lag_days"]) == [13, 12, 11, 8]


def test_rebuild_current_does_not_touch_closed_partitions(tmp_path):
    store = PairStore(tmp_path / "processed")
    window = _days(17, 18, 19)
    for ref in window:
        store.build_pairs(ref, window)
    before = store.read(date(2026, 6, 18)).to_dict()

    store.rebuild_current(date(2026, 6, 19), window + _days(22))
    assert store.read(date(2026, 6, 18)).to_dict() == before
    assert len(store.read(date(2026, 6, 19))) == 2
