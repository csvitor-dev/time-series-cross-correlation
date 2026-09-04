import numpy as np
import pandas as pd

from visualization.heatmap import plot_heatmap


def test_generates_non_empty_png(tmp_path):
    labels = ["2026-06-19", "2026-06-18", "2026-06-17"]
    matrix = pd.DataFrame(
        [[1.0, 0.3, -0.2], [0.3, 1.0, 0.6], [-0.2, 0.6, 1.0]],
        index=labels,
        columns=labels,
    )
    path = plot_heatmap(matrix, "pearson", tmp_path / "heatmap.png")
    assert path.exists()
    assert path.stat().st_size > 1000
