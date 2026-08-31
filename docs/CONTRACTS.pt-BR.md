# Contratos de dados — servidor x cliente

Observação de como o contrato OHLC é definido nos dois projetos de referência
(`~/works/BotTrader-TCC/`) e como este projeto se posiciona em relação a eles.

## Servidor — `qData_service` (FastAPI + gRPC)

O contrato é declarado uma vez no wire e propagado para dentro:

```
protos/ohlc.proto            OHLCBar / OHLCRequest / OHLCService.StreamOHLC   (fonte de verdade)
  └─ schemas/ochl.py         Pydantic OHLCBar / OHLCBarsResponse              (validação, snake_case)
       └─ db/models.py       ORM OHLCBar + upsert ON CONFLICT                 (persistência)
            └─ db/accessors.py  fetch_ohlc(symbol, timeframe, start, end, limit, offset, order_desc)
```

Exposição:

| Protocolo | Rota | Auth |
|---|---|---|
| REST | `POST /api/v1/auth/token` → `{ access_token, token_type }` | — |
| REST | `GET /api/v1/distribution/ohlc?symbol&timeframe&start_time&end_time&limit&offset&order_desc` | `Authorization: Bearer` |
| gRPC | `OHLCService/StreamOHLC` (server-streaming) | metadata `authorization: Bearer` |

A resposta REST de distribuição usa **camelCase** (`timeUtc`, `tickVolume`, `realVolume`),
enquanto o corpo de ingestão e o proto usam **snake_case**.

## Cliente — `FinHubLTI` (Angular)

Espelha o proto numa interface única e concentra a tradução num serviço:

```
models/ohlc.model.ts            interface OHLCBarData  ("single source of truth", espelha o proto)
services/ohlc-data.service.ts   monta query, injeta Bearer, mapeia camelCase→domínio, ordena por time
auth/auth.service.ts            login → guarda access_token + protocolo escolhido (grpc-web | https)
```

O switch de protocolo é preferência do usuário salva no login; em `https` o serviço bate na rota
REST, em `grpc-web` abre o stream. "Live" em REST é emulado com polling (`setInterval`).

## Este projeto

Entra como **mais um cliente** dessa API, do lado Python:

| Papel | Referência no servidor/cliente | Aqui |
|---|---|---|
| Modelo do wire | `schemas/ochl.py` / `ohlc.model.ts` | `src/contracts/ohlc.py` (`OHLCBar`, aceita as duas grafias via `AliasChoices`) |
| Requisição | tabela de query params | `src/contracts/ohlc.py` (`OHLCRequest.as_query()`) |
| Auth | `auth.service.ts` | `src/contracts/auth.py` + `QDataHTTPSource.authenticate()` |
| Consumo REST | `ohlc-data.service.ts::fetchHttpData` | `src/acquisition/qdata_client.py` |
| Fronteira plugável | — | `src/contracts/market_data_source.py` (`MarketDataSource`) |

Decisões relacionadas: `docs/adr/0002-contrato-da-fonte-de-dados.md`.
