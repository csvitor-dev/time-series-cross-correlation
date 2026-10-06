from __future__ import annotations

import argparse
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from analysis.report import write_report
from config import PipelineConfig
from pipeline import run

GENERATED = ("candles", "pairs", "correlations")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera uma amostragem executada em samples/")
    parser.add_argument("--config", default="config/sample.yaml")
    parser.add_argument("--dest", default="samples/win-10d-example")
    args = parser.parse_args()

    config = PipelineConfig.load(args.config)
    dest = Path(args.dest)
    processed = Path(config.paths.processed)
    shutil.rmtree(processed / "correlations", ignore_errors=True)
    result = run(config, offline=False, today=date.max)

    current_partition = processed / "pairs" / f"d_i={result['current_day'].isoformat()}"
    shutil.rmtree(current_partition, ignore_errors=True)
    dest.mkdir(parents=True, exist_ok=True)
    for part in GENERATED:
        shutil.rmtree(dest / part, ignore_errors=True)
        shutil.copytree(processed / part, dest / part)
    shutil.copy2(processed / "manifest.yaml", dest / "manifest.yaml")

    write_report(result["analysis"], config, dest / "REPORT.md")
    print(f"amostragem escrita em {dest}")


if __name__ == "__main__":
    main()
