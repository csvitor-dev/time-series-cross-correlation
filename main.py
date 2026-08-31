from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import PipelineConfig
from pipeline import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Time Series Cross-Correlation pipeline (Release 1)")
    parser.add_argument("--config", default="config/pipeline.yaml")
    parser.add_argument("--offline", action="store_true", help="usa FixtureSource (data/raw)")
    parser.add_argument("--today", type=date.fromisoformat, default=None, help="define d_n")
    args = parser.parse_args()

    config = PipelineConfig.load(args.config)
    result = run(config, offline=args.offline, today=args.today)

    print(f"dia corrente (d_n): {result['current_day']}")
    print(f"dias selados: {', '.join(d.isoformat() for d in result['sealed_days']) or '-'}")
    print(f"manifesto: {result['manifest']}")


if __name__ == "__main__":
    main()
