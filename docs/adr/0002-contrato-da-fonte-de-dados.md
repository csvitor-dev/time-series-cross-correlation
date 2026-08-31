# 0002 — Contrato da fonte de dados e cliente REST do qData_service

- Status: Aceito
- Data: 2026-08-31

## Contexto

A Camada de Captura precisa dos candles do WIN, mas ainda não há acesso à API. A ARCHITECTURE
prevê o MetaTrader 5 como fonte, isolado atrás de uma interface. Existe um serviço interno,
`qData_service` (`~/works/BotTrader-TCC/qData_service`), que já ingere do MT5 e publica OHLC via
REST (`GET /api/v1/distribution/ohlc`, auth Bearer) e gRPC — consumido pelo `FinHubLTI`.

O contrato OHLC aparece em quatro formas no servidor (proto → schema Pydantic → ORM com `upsert`
→ accessor `fetch_ohlc`) e é espelhado no cliente por uma interface TS (`OHLCBarData`) mais um
serviço que monta a query, injeta o Bearer e mapeia a resposta. As chaves divergem: proto e
ingestão usam `snake_case`; a resposta REST de distribuição usa `camelCase`.

## Decisão

1. Definir `MarketDataSource` (ABC) como fronteira da Captura, com `fetch_ohlc(OHLCRequest)`.
2. Release 1: implementação `QDataHTTPSource` — autentica em `/api/v1/auth/token`, pagina
   `/api/v1/distribution/ohlc` com Bearer, converte cada item em `OHLCBar`. `FixtureSource` cobre
   o desenvolvimento offline enquanto não há credenciais.
3. `OHLCBar` (Pydantic) replica os campos do `schemas/ochl.py` do qData e aceita as duas grafias
   via `AliasChoices`, absorvendo no contrato a tradução que o `ohlc-data.service.ts` faz à mão.
4. O MT5 permanece como fonte upstream do próprio qData; uma futura `MT5DataSource` entra pela
   mesma interface sem afetar as demais camadas.

## Consequências

- O resto do pipeline depende só de `MarketDataSource` + `OHLCBar`.
- Mudanças no wire do qData ficam confinadas a `acquisition/` e `contracts/ohlc.py`.
- Sem acesso à API, `QDataHTTPSource` é validado apenas por teste com mock (`respx`).

## Alternativas consideradas

- **Cliente gRPC**: streaming nativo, mas exige toolchain de protobuf e o caso da Release 1 é
  carga histórica em lote — REST basta. Fica para depois.
- **Dois modelos separados (ingest vs distribution)**: mais fiel, porém duplica o schema; os
  aliases resolvem com um só modelo.
