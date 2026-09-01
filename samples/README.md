# samples/

Amostragens **executadas** do procedimento — cada subpasta é o resultado de uma corrida completa
do pipeline sobre um recorte de dados, versionada junto com os artefatos produzidos.

- `win-10d-example/` — corrida offline (`python scripts/gen_fixture.py && python scripts/make_sample.py`)
  sobre 10 dias sintéticos do WIN:
  - `candles/date=.../` — candles M1 selados por pregão
  - `pairs/d_i=.../` — estrutura de pares de defasagem $\mathcal{P}_i$
  - `correlations/method=<m>/` — coeficientes $v_{i,j}$, p-valor e estabilidade (`pairs.parquet`)
    e a matriz $\mathbf{V}$ (`matrix.parquet`), para Pearson e Spearman
  - `correlations/heatmap_<m>.png` — mapa de calor (triângulo superior de $\mathbf{V}$)
  - `REPORT.md` — parâmetros, cobertura por dia e os pares de maior associação
  - `manifest.yaml` — metadados da execução

Os dados são sintéticos (semente fixa em `scripts/gen_fixture.py`): um fator comum diário com peso
decrescente entre os dias, para o mapa de calor exibir estrutura real.
