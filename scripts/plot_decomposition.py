from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from analysis.decomposition import get_decomposer
from analysis.series import _minute_grid, day_close
from config import PipelineConfig

COLOR_OBSERVED = "dimgray"
COLOR_TREND = {"moving_average": "blue", "stl": "red"}
LABEL_TREND = {"moving_average": "média móvel", "stl": "STL"}


def _hhmm(minute: int) -> str:
    return f"{minute // 60:02d}:{minute % 60:02d}"


def _latest_day(candles: Path) -> date:
    days = sorted(p.name.removeprefix("date=") for p in candles.glob("date=*"))
    if not days:
        raise ValueError(f"nenhum pregão em {candles}")
    return date.fromisoformat(days[-1])


def _format_axis(ax, grid: np.ndarray, ylabel: str) -> None:
    ticks = np.linspace(0, len(grid) - 1, num=8, dtype=int)
    ax.set_xticks(ticks, [_hhmm(int(grid[t])) for t in ticks])
    ax.tick_params(labelsize=12)
    ax.set_ylabel(ylabel, fontsize=13)
    ax.grid(True, linestyle="--", alpha=0.4)


def _save(fig, path: Path) -> None:
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"gráfico salvo em {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plota um pregão do WIN e sua decomposição")
    parser.add_argument("--config", default="config/sample.yaml")
    parser.add_argument("--candles", default="samples/win-10d-example/candles")
    parser.add_argument("--day", type=date.fromisoformat, default=None)
    parser.add_argument("--out-dir", default="samples/win-10d-example/decomposition")
    args = parser.parse_args()

    config = PipelineConfig.load(args.config)
    cfg = config.analysis
    candles = Path(args.candles)
    day = args.day or _latest_day(candles)
    frame = pd.read_parquet(candles / f"date={day.isoformat()}" / "part.parquet")

    close, coverage = day_close(frame, cfg)
    grid = _minute_grid(cfg)
    x = np.arange(len(grid))
    title = f"{config.symbol} {config.timeframe} · {day.isoformat()} ({coverage:.0%})"
    xlabel = f"({cfg.window.tz})"

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(x, close, color=COLOR_OBSERVED, linewidth=1.0, label="close")
    _format_axis(ax, grid, "close")
    ax.set_xlabel(xlabel, fontsize=13)
    ax.set_title(title, fontsize=16)
    ax.legend(loc="upper right", fontsize=11)
    out_dir = Path(args.out_dir)
    _save(fig, out_dir / "series.png")

    parts = {name: get_decomposer(name, cfg.decomposition).decompose(close) for name in COLOR_TREND}
    params = cfg.decomposition

    fig, axes = plt.subplots(3, 1, figsize=(12, 11), sharex=True)
    axes[0].plot(x, close, color=COLOR_OBSERVED, linewidth=0.8, alpha=0.6, label="close")
    for name, result in parts.items():
        axes[0].plot(x, result.trend, color=COLOR_TREND[name], linewidth=1.6,
                     label=f"tendência · {LABEL_TREND[name]}")
    _format_axis(axes[0], grid, "close")
    axes[0].legend(loc="upper right", fontsize=11)

    axes[1].plot(x, parts["stl"].seasonal, color=COLOR_TREND["stl"], linewidth=1.0,
                 label=f"sazonal · STL (período {params.stl_period} min)")
    _format_axis(axes[1], grid, "sazonal")
    axes[1].legend(loc="upper right", fontsize=11)

    for name, result in parts.items():
        axes[2].plot(x, result.resid, color=COLOR_TREND[name], linewidth=0.8, alpha=0.8,
                     label=f"resíduo · {LABEL_TREND[name]}")
    axes[2].axhline(0, color="black", linewidth=0.8, alpha=0.6)
    _format_axis(axes[2], grid, "resíduo")
    axes[2].set_xlabel(xlabel, fontsize=13)
    axes[2].legend(loc="upper right", fontsize=11)

    fig.suptitle(
        f"Decomposição — {title}\n"
        f"média móvel centrada ({params.ma_window} min) · STL (período {params.stl_period} min)",
        fontsize=16,
    )
    _save(fig, out_dir / "decomposed.png")


if __name__ == "__main__":
    main()
