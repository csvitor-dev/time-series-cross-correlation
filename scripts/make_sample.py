from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from config import PipelineConfig
from pipeline import run

DEST = Path("samples/win-10d-example")


def main() -> None:
    config = PipelineConfig.load("config/pipeline.yaml")
    run(config, offline=True)

    processed = Path(config.paths.processed)
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)
    shutil.copytree(processed / "candles", DEST / "candles")
    shutil.copytree(processed / "pairs", DEST / "pairs")
    shutil.copy2(processed / "manifest.yaml", DEST / "manifest.yaml")
    print(f"amostragem escrita em {DEST}")


if __name__ == "__main__":
    main()
