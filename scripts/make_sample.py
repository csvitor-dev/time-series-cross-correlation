from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from analysis.report import write_report
from config import PipelineConfig
from pipeline import run

DEST = Path("samples/win-10d-example")


def main() -> None:
    config = PipelineConfig.load("config/pipeline.yaml")
    result = run(config, offline=True)

    processed = Path(config.paths.processed)
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)
    shutil.copytree(processed / "candles", DEST / "candles")
    shutil.copytree(processed / "pairs", DEST / "pairs")
    shutil.copytree(processed / "correlations", DEST / "correlations")
    shutil.copy2(processed / "manifest.yaml", DEST / "manifest.yaml")

    write_report(result["analysis"], config, DEST / "REPORT.md")
    print(f"amostragem escrita em {DEST}")


if __name__ == "__main__":
    main()
