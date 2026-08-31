# 0003 — Armazenamento em Parquet separado por mutabilidade

- Status: Aceito
- Data: 2026-08-31

## Contexto

A análise compara um dia de referência `d_n` com os dias anteriores da própria série. `d_n` é o
pregão corrente: ainda recebe barras e será relido/reescrito várias vezes ao longo do dia. Os
antecessores `d_1..d_{n-1}` são pregões fechados e imutáveis. A Camada de Análise (release futura)
consome os dados de forma vetorizada (pandas/numpy) e o número de pares `(d_i, d_k)` cresce com
`n²`. Requisitos: reprodutibilidade, versionamento e auditabilidade.

## Decisão

Separar por **mutabilidade**, não por tecnologia:

- **Dias fechados**: uma partição **Parquet imutável** por pregão em
  `data/processed/candles/date=YYYY-MM-DD/part.parquet`. Escreve uma vez; `seal_day` recusa
  sobrescrever partição existente.
- **Dia corrente**: buffer mutável único `data/interim/current_day.parquet`, reescrito a cada
  atualização. Ao fechar o pregão, `seal_day` promove o buffer a partição imutável.
- **Pares `P_i`**: Parquet particionado por `d_i` em `data/processed/pairs/d_i=YYYY-MM-DD/`. Só o
  conjunto de `d_n` é recalculado (`rebuild_current`); pares entre dias fechados são estáveis.
- **Manifesto** `data/processed/manifest.yaml` por execução: símbolo, timeframe, período, `n`,
  fonte, `sha256` dos inputs, dias selados, timestamp.

## Consequências

- Leitura direta e vetorizada pela Análise, sem camada SQL.
- Dias fechados nunca mudam → diffs e versionamento previsíveis; recomputo barato para `d_n`.
- Parquet exige `pyarrow`; atualizar um dia fechado (correção) implica remover a partição
  manualmente — deliberado, para forçar rastreabilidade.
- `data/interim` e `data/processed` são artefatos gerados (fora do git); `samples/` guarda uma
  amostragem executada versionada.

## Alternativas consideradas

- **SQLite** (candles + pares em tabelas, `upsert` como no qData): bom para query ad-hoc e
  ingestão incremental, mas a Análise é vetorizada (SQL→DataFrame vira overhead), o I/O de pares
  escala pior em `n²` e o binário polui o histórico. Fora da Release 1.
- **Tudo em Parquet reescrevendo o dia inteiro a cada poll**: simples, mas perde a garantia de
  imutabilidade dos dias fechados.
- **Híbrido (SQLite p/ dia corrente + Parquet p/ o resto)**: cobre os dois usos ao custo de duas
  tecnologias de storage já na Release 1 — adiado até haver necessidade real de query incremental.
