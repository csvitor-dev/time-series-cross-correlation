from __future__ import annotations

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def _detrending_operator(scale: int) -> np.ndarray:
    t = np.arange(scale + 1, dtype=float)
    design = np.column_stack([np.ones_like(t), t])
    return np.eye(scale + 1) - design @ np.linalg.pinv(design)


def detrended_boxes(x: np.ndarray, scale: int) -> np.ndarray:
    profile = np.cumsum(x - x.mean())
    boxes = sliding_window_view(profile, scale + 1)
    return boxes @ _detrending_operator(scale)


def box_covariances(
    x: np.ndarray, y: np.ndarray, scale: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rx = detrended_boxes(x, scale)
    ry = detrended_boxes(y, scale)
    return (rx * ry).mean(axis=1), (rx * rx).mean(axis=1), (ry * ry).mean(axis=1)


def rho_q(x: np.ndarray, y: np.ndarray, scale: int, q: float) -> float:
    fxy, fxx, fyy = box_covariances(x, y, scale)
    half = q / 2
    cross = np.mean(np.sign(fxy) * np.abs(fxy) ** half)
    denominator = np.sqrt(np.mean(fxx**half) * np.mean(fyy**half))
    return float(cross / denominator) if denominator > 0 else float("nan")
