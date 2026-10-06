# 0006 — Decomposição das séries com foco na tendência

- Status: Aceito
- Data: 2026-10-05

## Contexto

As Releases 2 e 3 (ADRs 0004 e 0005) correlacionam o retorno log do close minuto a minuto. O
retorno log é estacionário, mas é dominado pelo ruído de microestrutura do M1, que tende a esconder
a forma do movimento do pregão (quedas, lateralizações, recuperações). Para comparar pregões pela
sua **tendência**, é preciso separar a componente de baixa frequência do close das oscilações de
curto prazo antes de correlacionar.

## Decisão

1. **Módulo `analysis.decomposition`** com a interface `Decomposer.decompose(values) ->
   Decomposition(observed, trend, seasonal, resid)`, satisfazendo
   `observed = trend + seasonal + resid` — plugável como `CorrelationMethod`.
2. **Dois decompositores**:
   - `moving_average`: média móvel **centrada** de `ma_window` minutos (padrão 30), com
     `min_periods=1` nas bordas para preservar o comprimento da grade; não estima sazonalidade
     (`seasonal = 0`, `resid = observed − trend`).
   - `stl`: STL (Cleveland et al., 1990) via `statsmodels`, com `stl_period` minutos (padrão 30) e
     ajuste robusto (`stl_robust`, padrão `true`) para atenuar o peso de picos de abertura.
3. **Entrada é o close na grade M1 da janela** (`analysis.series.day_close`), já com
   *forward/backward fill* — mesma grade usada pelo motor de correlação, para que a tendência possa
   ser consumida diretamente por ele.
4. **Parâmetros versionados** em `analysis.decomposition` (`ma_window`, `stl_period`,
   `stl_robust`), mantendo a reprodutibilidade.
5. Nesta release a decomposição **não altera o motor de correlação**; o artefato é a figura de um
   pregão do WIN bruto e decomposto (`scripts/plot_decomposition.py`). O uso da tendência como
   série de entrada das correlações fica para uma release seguinte.

## Consequências

- Nova dependência: `statsmodels` (e `patsy`, transitiva).
- Com período de 30 min o STL produz uma tendência mais suave que a média móvel de mesma janela
  (o suavizador de tendência do STL tem ~1,5 período); ambas acompanham o close nas mesmas
  inflexões do pregão.
- A "sazonalidade" do STL em dados intradiários de um único pregão não é um ciclo de mercado
  conhecido: é a oscilação de curto prazo removida da tendência. Não é interpretada isoladamente.
- O STL exige ao menos `2 · stl_period + 1` pontos; janelas curtas demais falham explicitamente.

## Alternativas consideradas

- **Filtro de Hodrick–Prescott**: depende de um $\lambda$ sem calibração consolidada para M1
  intradiário; média móvel e STL têm parâmetros em minutos, diretamente interpretáveis.
- **Decomposição clássica (`seasonal_decompose`)**: perde as bordas (NaN em meia janela de cada
  lado) e não é robusta a *outliers*; o STL resolve ambos.
- **Média móvel causal (só passado)**: introduz atraso de meia janela na tendência; como a análise é
  *ex post* sobre pregões fechados, a centrada é preferível.
