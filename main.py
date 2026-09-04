from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import PipelineConfig
from pipeline import analyze, run


def main() -> None:
    parser = argparse.ArgumentParser(description="Time Series Cross-Correlation pipeline")
    parser.add_argument("--config", default="config/pipeline.yaml")
    parser.add_argument("--offline", action="store_true", help="usa FixtureSource (data/raw)")
    parser.add_argument("--today", type=date.fromisoformat, default=None, help="define d_n")
    parser.add_argument(
        "--analysis-only",
        action="store_true",
        help="recalcula a correlação sobre os candles já armazenados",
    )
    args = parser.parse_args()

    config = PipelineConfig.load(args.config)

    if args.analysis_only:
        output = analyze(config)
        for method in config.analysis.methods:
            print(f"{method}: {len(output.pairs[method])} pares")
        return

    result = run(config, offline=args.offline, today=args.today)
    print(f"dia corrente (d_n): {result['current_day']}")
    print(f"dias selados: {', '.join(d.isoformat() for d in result['sealed_days']) or '-'}")
    print(f"manifesto: {result['manifest']}")


if __name__ == "__main__":
    main()
