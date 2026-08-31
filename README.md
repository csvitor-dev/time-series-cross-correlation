# Time Series Cross-Correlation

Projeto para o desenvolvimento de um algoritmo de análise de séries temporais por meio de **correlação cruzada** (cross-correlation), com o objetivo de subsidiar a discussão de resultados no Trabalho de Conclusão de Curso (TCC).

## Objetivo

Investigar e implementar técnicas de correlação cruzada aplicadas a séries temporais, permitindo identificar relações de dependência, defasagens (lags) e padrões de similaridade entre diferentes sinais/séries ao longo do tempo. Os resultados obtidos servirão como base experimental para a análise e discussão apresentadas no TCC.

## Status

🚧 **Release 1** em desenvolvimento — camadas de Captura, Pré-processamento e Armazenamento
(ver [docs/ARCHITECTURE.pt-BR.md](docs/ARCHITECTURE.pt-BR.md) §4). A Camada de Análise
(correlação + mapa de calor) e a integração com o dashboard ficam para a Release 2.

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
# execução offline, a partir de data/raw/ (sem acesso à API)
python main.py --offline

# execução contra o qData_service (requer credenciais em .env)
python main.py
```

Saídas: `data/interim/current_day.parquet` (dia corrente, mutável),
`data/processed/candles/date=.../` (dias fechados, imutáveis),
`data/processed/pairs/d_i=.../` (matriz de defasagens) e `data/processed/manifest.yaml`.

Uma amostragem executada de exemplo fica em [samples/](samples/)
(`python scripts/make_sample.py`).

## Testes

```bash
pytest
```

## Licença

Este projeto é de caráter acadêmico, desenvolvido no contexto de um Trabalho de Conclusão de Curso (TCC).
