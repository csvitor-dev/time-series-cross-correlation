from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Period(BaseModel):
    start: date
    end: date


class Paths(BaseModel):
    raw: Path = Path("data/raw")
    interim: Path = Path("data/interim")
    processed: Path = Path("data/processed")


class Window(BaseModel):
    start: str = "09:00"
    end: str = "17:55"
    tz: str = "America/Sao_Paulo"


class AnalysisConfig(BaseModel):
    value: str = "log_return"
    methods: list[str] = ["pearson", "spearman"]
    window: Window = Window()
    min_coverage: float = 0.90
    stability_subwindows: int = 3


class PipelineConfig(BaseModel):
    symbol: str
    timeframe: str
    period: Period
    reference_window_n: int
    source: str
    paths: Paths = Paths()
    holidays: list[date] = []
    analysis: AnalysisConfig = AnalysisConfig()

    @classmethod
    def load(cls, path: str | Path = "config/pipeline.yaml") -> "PipelineConfig":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return cls.model_validate(data)


class QDataSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="QDATA_", env_file=".env", extra="ignore")

    auth_url: str = ""
    http_url: str = ""
    username: str = ""
    password: str = ""
