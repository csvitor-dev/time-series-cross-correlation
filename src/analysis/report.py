from __future__ import annotations

from pathlib import Path

from analysis.cross_correlation import AnalysisOutput
from config import AnalysisConfig, PipelineConfig


def _coverage_table(output: AnalysisOutput, min_coverage: float) -> list[str]:
    lines = ["| dia | cobertura | |", "|---|---|---|"]
    for day in sorted(output.coverage):
        cov = output.coverage[day]
        flag = "⚠" if cov < min_coverage else ""
        lines.append(f"| {day.isoformat()} | {cov:.1%} | {flag} |")
    return lines


def _method_section(name: str, output: AnalysisOutput, heading: str = "###") -> list[str]:
    pairs = output.pairs[name].copy()
    pairs["abs"] = pairs["coefficient"].abs()
    top = pairs.sort_values("abs", ascending=False).head(10)
    significant = int((pairs["p_value"] < 0.05).sum())

    lines = [
        f"{heading} {name}",
        "",
        f"Pares: {len(pairs)} · significativos (p < 0.05): {significant}",
        "",
        "| d_i | d_j | lag (dias) | coef. | p-valor | lag (min) | estab. (σ) |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in top.itertuples(index=False):
        lines.append(
            f"| {row.d_i} | {row.d_j} | {row.lag_days} | {row.coefficient:.3f} | "
            f"{row.p_value:.3f} | {row.lag} | {row.stability_std:.3f} |"
        )
    scope = f"trend={output.trend}/" if output.trend else ""
    lines += ["", f"![heatmap {name}](correlations/{scope}heatmap_{name}.png)", ""]
    return lines


def _surrogate_parameters(analysis: AnalysisConfig) -> list[str]:
    names = set(analysis.methods)
    lines = []
    if "mi" in names:
        lines.append(f"- informação mútua: {analysis.mi_bins} bins por quantis")
    if names & {"rho_dcca", "mf_dcca"}:
        lines.append(f"- escala DCCA: {analysis.dcca_scale} min")
    if "mf_dcca" in names:
        lines.append(f"- ordem q do MF-DCCA (ρ_q): {analysis.mfdcca_q:g}")
    if names & {"mi", "rho_dcca", "mf_dcca"}:
        lines.append(
            f"- surrogates (deslocamento circular): {analysis.surrogates} · semente {analysis.seed}"
        )
    return lines


def _trend_parameters(analysis: AnalysisConfig) -> list[str]:
    if not analysis.trends:
        return []
    params = analysis.decomposition
    return [
        f"- tendências: {', '.join(analysis.trends)} (série = `{analysis.value}` da tendência)",
        f"- média móvel centrada: {params.ma_window} min · STL: período {params.stl_period} min"
        f"{' (robusto)' if params.stl_robust else ''}",
    ]


def write_report(
    outputs: dict[str | None, AnalysisOutput], config: PipelineConfig, path: str | Path
) -> Path:
    analysis = config.analysis
    output = next(iter(outputs.values()))
    lines = [
        f"# Amostragem — correlação cruzada ({config.symbol}, {len(output.coverage)} dias)",
        "",
        "## Parâmetros",
        "",
        f"- valor da série: `{analysis.value}`",
        f"- métodos: {', '.join(analysis.methods)}",
        f"- janela: {analysis.window.start}–{analysis.window.end} ({analysis.window.tz})",
        f"- cobertura mínima: {analysis.min_coverage:.0%}",
        f"- sub-janelas de estabilidade: {analysis.stability_subwindows}",
        *_surrogate_parameters(analysis),
        *_trend_parameters(analysis),
        "",
        "## Cobertura por dia",
        "",
        *_coverage_table(output, analysis.min_coverage),
        "",
        "## Resultados",
        "",
    ]
    for trend, result in outputs.items():
        heading = "###"
        if trend:
            lines += [f"### Tendência · {trend}", ""]
            heading = "####"
        for name in analysis.methods:
            lines += _method_section(name, result, heading)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
