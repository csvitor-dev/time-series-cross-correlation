# Contratos

Modelos tipados que definem a fronteira entre a Camada de Captura e o resto do pipeline
(ARCHITECTURE §2.1). São o espelho, do lado deste projeto, do contrato OHLC que o
`qData_service` publica.

## Como o contrato OHLC é definido nas duas pontas de referência

### Servidor — `~/works/BotTrader-TCC/qData_service`

| Camada | Arquivo | Papel |
|---|---|---|
| Wire | `protos/ohlc.proto` | `OHLCBar`, `OHLCRequest`, `OHLCService.StreamOHLC` |
| Validação | `src/quantwin/schemas/ochl.py` | Pydantic `OHLCBar` / `OHLCBarsResponse` (snake_case) |
| Persistência | `src/quantwin/db/models.py` | ORM `OHLCBar` + `upsert` (ON CONFLICT `source_id,symbol,timeframe,time`) |
| Leitura | `src/quantwin/db/accessors.py` | `fetch_ohlc(symbol, timeframe, start_time, end_time, limit, offset, order_desc)` |
| REST | `FinHubLTI/docs/http_endpoint.md` | `GET /api/v1/distribution/ohlc`, resposta **camelCase** |

### Cliente — `~/works/BotTrader-TCC/FinHubLTI`

| Arquivo | Papel |
|---|---|
| `src/app/models/ohlc.model.ts` | `OHLCBarData` — "single source of truth", espelha o protobuf |
| `src/app/services/ohlc-data.service.ts` | monta query `symbol,timeframe,start_time,end_time,limit,order_desc`, header `Authorization: Bearer`, mapeia camelCase → domínio, ordena por `time` |
| `src/app/auth/auth.service.ts` | `POST /api/v1/auth/token` → `{ access_token, token_type }` |

## Divergência tratada aqui

O corpo de ingestão / proto usa `snake_case` (`time_utc`, `tick_volume`, `real_volume`);
a resposta REST de distribuição usa `camelCase` (`timeUtc`, `tickVolume`, `realVolume`).
`OHLCBar` (`ohlc.py`) aceita as duas grafias via `AliasChoices`, evitando o mapeamento manual
que o serviço Angular faz. Ver `docs/adr/0002-contrato-da-fonte-de-dados.md`.
