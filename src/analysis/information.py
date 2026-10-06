from __future__ import annotations

import numpy as np
from scipy import stats


def quantile_bins(x: np.ndarray, bins: int) -> np.ndarray:
    ranks = stats.rankdata(x, method="average")
    return np.minimum(((ranks - 0.5) * bins / len(x)).astype(int), bins - 1)


def mutual_information(x: np.ndarray, y: np.ndarray, bins: int) -> float:
    bx = quantile_bins(x, bins)
    by = quantile_bins(y, bins)
    joint = np.bincount(bx * bins + by, minlength=bins * bins).reshape(bins, bins) / len(x)
    px = joint.sum(axis=1, keepdims=True)
    py = joint.sum(axis=0, keepdims=True)
    mask = joint > 0
    return float(np.sum(joint[mask] * np.log(joint[mask] / (px @ py)[mask])))


def linfoot(mi: float) -> float:
    return float(np.sqrt(1.0 - np.exp(-2.0 * max(mi, 0.0))))
