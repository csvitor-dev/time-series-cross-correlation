import numpy as np
import pandas as pd

from storage.correlation_store import CorrelationStore


def test_roundtrip_pairs_and_matrix(tmp_path):
    store = CorrelationStore(tmp_path / "processed")
    pairs = pd.DataFrame(
        {
            "method": ["pearson"],
            "d_i": ["2026-06-18"],
            "d_j": ["2026-06-17"],
            "lag_days": [1],
            "coefficient": [0.5],
            "p_value": [0.01],
            "n": [500],
            "stability_std": [0.03],
        }
    )
    matrix = pd.DataFrame(
        np.eye(2), index=["2026-06-18", "2026-06-17"], columns=["2026-06-18", "2026-06-17"]
    )

    store.write("pearson", pairs, matrix)

    pd.testing.assert_frame_equal(store.read_pairs("pearson"), pairs)
    pd.testing.assert_frame_equal(store.read_matrix("pearson"), matrix)


def test_write_overwrites(tmp_path):
    store = CorrelationStore(tmp_path / "processed")
    empty = pd.DataFrame(columns=["coefficient"])
    matrix = pd.DataFrame(np.eye(1), index=["d"], columns=["d"])
    store.write("spearman", empty, matrix)
    store.write("spearman", empty, matrix)
    assert store.read_matrix("spearman").shape == (1, 1)
