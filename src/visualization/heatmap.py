from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_heatmap(matrix: pd.DataFrame, method: str, path: str | Path) -> Path:
    labels = list(matrix.columns)
    data = matrix.to_numpy(dtype=float)

    fig, ax = plt.subplots(figsize=(1.1 * len(labels) + 2, 1.1 * len(labels) + 1))
    image = ax.imshow(data, cmap="RdBu_r", vmin=-1.0, vmax=1.0)

    ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(labels)), labels, fontsize=8)
    ax.set_title(f"Mapa de calor correlacional — {method}")

    for i in range(len(labels)):
        for j in range(len(labels)):
            value = data[i, j]
            if not np.isnan(value):
                ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=7)

    fig.colorbar(image, ax=ax, shrink=0.8, label="coeficiente")
    fig.tight_layout()

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
