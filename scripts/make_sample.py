from __future__ import annotations

import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from analysis.report import write_report
from config import PipelineConfig
from pipeline import run

DEST = Path("samples/win-10d-example")
GENERATED = ("candles", "pairs", "correlations")


def main() -> None:
    config = PipelineConfig.load("config/sample.yaml")
    result = run(config, offline=False, today=date.max)

    processed = Path(config.paths.processed)
    current_partition = processed / "pairs" / f"d_i={result['current_day'].isoformat()}"
    shutil.rmtree(current_partition, ignore_errors=True)
    DEST.mkdir(parents=True, exist_ok=True)
    for part in GENERATED:
        shutil.rmtree(DEST / part, ignore_errors=True)
        shutil.copytree(processed / part, DEST / part)
    shutil.copy2(processed / "manifest.yaml", DEST / "manifest.yaml")

    write_report(result["analysis"], config, DEST / "REPORT.md")
    print(f"amostragem escrita em {DEST}")


if __name__ == "__main__":
    main()
