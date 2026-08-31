from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml


class Manifest:
    def __init__(self, processed: str | Path = "data/processed"):
        self._file = Path(processed) / "manifest.yaml"

    def write(
        self,
        *,
        symbol: str,
        timeframe: str,
        period: dict,
        reference_window_n: int,
        source: str,
        input_sha256: str,
        sealed_days: list[str],
    ) -> Path:
        payload = {
            "symbol": symbol,
            "timeframe": timeframe,
            "period": period,
            "reference_window_n": reference_window_n,
            "source": source,
            "input_sha256": input_sha256,
            "sealed_days": sealed_days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._file.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        return self._file

    def read(self) -> dict:
        return yaml.safe_load(self._file.read_text(encoding="utf-8"))
