# samples/

Amostragens **executadas** do procedimento — cada subpasta é o resultado de uma corrida completa
do pipeline sobre um recorte de dados, versionada junto com os artefatos produzidos.

- `win-10d-example/` — corrida contra o `qData_service` (`python scripts/make_sample.py`,
  requer credenciais em `.env`) sobre os 10 últimos pregões do WINQ26 até 2026-08-14
  (`config/sample.yaml`):
  - `candles/date=.../` — candles M1 selados por pregão
  - `pairs/d_i=.../` — estrutura de pares de defasagem $\mathcal{P}_i$
  - `correlations/method=<m>/` — coeficientes $v_{i,j}$, p-valor e estabilidade (`pairs.parquet`)
    e a matriz $\mathbf{V}$ (`matrix.parquet`), para Pearson e Spearman
  - `correlations/heatmap_<m>.png` — mapa de calor da matriz $\mathbf{V}$ completa e simétrica
  - `REPORT.md` — parâmetros, cobertura por dia e os pares de maior associação
  - `manifest.yaml` — metadados da execução

Os dados são reais (M1 do WINQ26, fonte `qData_service`), então a associação entre pregões
é fraca — o mapa de calor reflete a estrutura efetivamente presente no mercado no período.
