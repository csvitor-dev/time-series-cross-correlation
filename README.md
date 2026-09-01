# Time Series Cross-Correlation

Projeto para o desenvolvimento de um algoritmo de análise de séries temporais por meio de **correlação cruzada** (cross-correlation), com o objetivo de subsidiar a discussão de resultados no Trabalho de Conclusão de Curso (TCC).

## Objetivo

Investigar e implementar técnicas de correlação cruzada aplicadas a séries temporais, permitindo identificar relações de dependência, defasagens (lags) e padrões de similaridade entre diferentes sinais/séries ao longo do tempo. Os resultados obtidos servirão como base experimental para a análise e discussão apresentadas no TCC.

## Status

🚧 **Release 2** em desenvolvimento — Camada de Análise: correlação cruzada par a par entre os
dias de operação, com matriz $\mathbf{V}$, p-valor, estabilidade entre sub-janelas e mapa de calor
(Pearson e Spearman; ver [docs/ARCHITECTURE.pt-BR.md](docs/ARCHITECTURE.pt-BR.md) §5 e
[ADR 0004](docs/adr/0004-camada-de-analise-correlacao-cruzada.md)).
A Release 1 (Captura → Pré-processamento → Armazenamento) já está em `main`.
Integração com o dashboard, CCF/ρDCCA/MF-DCCA e captura real via API ficam para releases seguintes.

## Requisitos

- Python 3.14.7
- `pip install -r requirements.txt` (dev: `requirements-dev.txt`)

## Arquitetura e contratos

- [docs/ARCHITECTURE.pt-BR.md](docs/ARCHITECTURE.pt-BR.md) — pipeline em camadas
- [docs/CONTRACTS.pt-BR.md](docs/CONTRACTS.pt-BR.md) — contrato OHLC (servidor `qData_service` x cliente)
- [docs/adr/](docs/adr/) — decisões arquiteturais

## Como executar

Configuração versionada em [config/pipeline.yaml](config/pipeline.yaml); segredos em `.env`
(ver `.env.example`).

```bash
# 1x: gera o fixture sintético offline em data/raw/ (semente fixa)
python scripts/gen_fixture.py

# pipeline completo offline (captura → ... → análise)
python main.py --offline

# só recalcular a correlação sobre os candles já armazenados
python main.py --analysis-only

# execução contra o qData_service (requer credenciais em .env)
python main.py
```

Saídas: `data/interim/current_day.parquet` (dia corrente, mutável),
`data/processed/candles/date=.../` (dias fechados, imutáveis),
`data/processed/pairs/d_i=.../` (estrutura de defasagens),
`data/processed/correlations/method=<m>/{pairs,matrix}.parquet` + `heatmap_<m>.png`,
e `data/processed/manifest.yaml`.

Uma amostragem executada de exemplo (com heatmap e `REPORT.md`) fica em [samples/](samples/)
(`python scripts/make_sample.py`).

## Testes

```bash
pytest
```

## Licença

Este projeto é de caráter acadêmico, desenvolvido no contexto de um Trabalho de Conclusão de Curso (TCC).
