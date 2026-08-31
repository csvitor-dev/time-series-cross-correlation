# samples/

Amostragens **executadas** do procedimento — cada subpasta é o resultado de uma corrida completa
do pipeline sobre um recorte de dados, versionado junto com os artefatos produzidos.

- `win-10d-example/` — corrida offline (`scripts/make_sample.py`) sobre os 10 dias de
  `data/raw/ohlc_winj26_10d.json`: candles selados (`candles/date=.../`), matriz de pares
  (`pairs/d_i=.../`) e `manifest.yaml`.

Na Release 2 (Camada de Análise) cada amostragem passa a incluir também o mapa de calor de
correlação e o report de discussão.
