from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from analysis.series import _minute_grid, day_series
from config import AnalysisConfig, PipelineConfig
from pipeline import build_source
from preprocessing.clean import clean
from preprocessing.trading_calendar import TradingCalendar

COLOR_REF = "red"
COLOR_LAGS = ["blue", "green", "darkorange", "purple", "brown", "teal"]
COLOR_WINDOW = "green"


def _parse_lags(raw: str) -> list[int]:
    if ".." in raw:
        return list(range(*[int(part) for part in raw.split("..")]))
    return [int(part) for part in raw.split(",") if part.strip()]


def _parse_window(raw: str | None) -> tuple[int, int] | None:
    if not raw:
        return None
    start, end = raw.split("-")
    to_min = lambda s: int(s[:2]) * 60 + int(s[3:])
    return to_min(start), to_min(end)


def _hhmm(minute: int) -> str:
    return f"{minute // 60:02d}:{minute % 60:02d}"


def _calendar_days(config: PipelineConfig) -> list[date]:
    return TradingCalendar(config.holidays).trading_days(
        config.period.start, config.period.end
    )


def _reference_day(config: PipelineConfig, today: date | None) -> date:
    days = _calendar_days(config)
    if today is None:
        return days[-config.reference_window_n :][-1]
    if today not in days:
        raise ValueError(f"{today} não é um dia de pregão no período configurado")
    return today


def _series_for_day(config: PipelineConfig, cfg: AnalysisConfig, day: date, offline: bool):
    source = build_source(config, offline)
    for fetched, bars in source.iter_days(config.symbol, config.timeframe, [day]):
        if not bars:
            raise ValueError(f"sem candles para {fetched}")
        return day_series(clean(bars), cfg)
    raise ValueError(f"sem candles para {day}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plota séries intradiárias reais do qData")
    parser.add_argument("--config", default="config/pipeline.yaml")
    parser.add_argument("--offline", action="store_true", help="usa FixtureSource (data/raw)")
    parser.add_argument("--symbol", default=None, help="sobrescreve o símbolo da configuração")
    parser.add_argument("--today", type=date.fromisoformat, default=None, help="dia de referência d_i")
    parser.add_argument("--days", default=None, help="datas ISO explícitas, ex.: 2026-09-03,2026-09-04")
    parser.add_argument("--lags", default="1", help="lags em dias de pregão, ex.: 1,2,5")
    parser.add_argument("--value", default=None, help="close | log_return | zscore")
    parser.add_argument("--window", default=None, help="janela destacada, ex.: 12:00-13:00")
    parser.add_argument("--close-line", action="store_true", help="linha tracejada no close de cada série")
    parser.add_argument("--title", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    config = PipelineConfig.load(args.config)
    if args.symbol:
        config = config.model_copy(update={"symbol": args.symbol})
    cfg = config.analysis

    if args.value:
        cfg = cfg.model_copy(update={"value": args.value})

    if args.days:
        explicit = [date.fromisoformat(part) for part in args.days.split(",") if part.strip()]
        d_i = explicit[0]
        lag_days = [(None, day) for day in explicit[1:]]
    else:
        calendar = _calendar_days(config)
        d_i = _reference_day(config, args.today)
        idx = calendar.index(d_i)
        lag_days = []
        for lag in _parse_lags(args.lags):
            if idx - lag < 0:
                raise ValueError(f"lag {lag} ultrapassa o início do período")
            lag_days.append((lag, calendar[idx - lag]))

    grid = _minute_grid(cfg)[1:]
    x = np.arange(len(grid))
    ticks = np.linspace(0, len(grid) - 1, num=8, dtype=int)

    ref_tag = "S1" if args.days else "D[n]"
    plan = [(ref_tag, d_i, COLOR_REF)]
    for order, (lag, day) in enumerate(lag_days):
        tag = f"D[n-{lag}]" if lag is not None else f"S{order + 2}"
        plan.append((tag, day, COLOR_LAGS[order % len(COLOR_LAGS)]))

    fig, ax = plt.subplots(figsize=(12, 6))
    first_close = 0.0

    for tag, day, color in plan:
        series = _series_for_day(config, cfg, day, args.offline)
        values = series.values
        ax.plot(x[: len(values)], values, color=color, linewidth=1.0,
                label=f"{tag} · {day.isoformat()} ({series.coverage:.0%})")
        
        if day == d_i and len(values):
            first_close = float(values[np.isfinite(values)][-1])

    if args.close_line and first_close:
        ax.axhline(first_close, color="black", linestyle="--", linewidth=1.0, alpha=0.6)
    window = _parse_window(args.window)

    if window is not None:
        base = int(grid[0])
        left = window[0] - base
        right = window[1] - base
        ax.axvspan(left, right, color=COLOR_WINDOW, alpha=0.12)
        ax.axvline(left, color=COLOR_WINDOW, linestyle="--", linewidth=1.5)
        ax.axvline(right, color=COLOR_WINDOW, linestyle="--", linewidth=1.5, label="janela")

    ax.set_xticks(ticks, [_hhmm(int(grid[t])) for t in ticks])
    ax.set_xlabel(f"({cfg.window.tz})")
    ax.set_ylabel(cfg.value)
    ax.set_title(args.title or f"{config.symbol} {config.timeframe}")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()

    out = Path(args.out or f"data/processed/plots/series_{d_i.isoformat()}.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"gráfico salvo em {out}")


if __name__ == "__main__":
    main()
