from datetime import date

from analysis.cross_correlation import CrossCorrelationEngine
from analysis.report import write_report
from config import AnalysisConfig, Period, PipelineConfig, Window
from test_cross_correlation import _frames


def _config(trends: list[str]) -> PipelineConfig:
    return PipelineConfig(
        symbol="WINQ26",
        timeframe="M1",
        period=Period(start=date(2026, 6, 1), end=date(2026, 6, 30)),
        reference_window_n=3,
        source="fixture",
        analysis=AnalysisConfig(
            methods=["pearson"],
            window=Window(start="09:00", end="10:59", tz="America/Sao_Paulo"),
            trends=trends,
        ),
    )


def test_report_has_one_section_per_trend(tmp_path):
    config = _config(["moving_average", "stl"])
    frames = _frames(3)
    outputs = {t: CrossCorrelationEngine(config.analysis, t).run(frames) for t in config.analysis.trends}
    text = write_report(outputs, config, tmp_path / "REPORT.md").read_text(encoding="utf-8")
    assert "### Tendência · moving_average" in text
    assert "### Tendência · stl" in text
    assert "correlations/trend=stl/heatmap_pearson.png" in text
    assert "- tendências: moving_average, stl" in text


def test_report_without_trends_keeps_flat_layout(tmp_path):
    config = _config([])
    outputs = {None: CrossCorrelationEngine(config.analysis).run(_frames(3))}
    text = write_report(outputs, config, tmp_path / "REPORT.md").read_text(encoding="utf-8")
    assert "Tendência" not in text
    assert "](correlations/heatmap_pearson.png)" in text
