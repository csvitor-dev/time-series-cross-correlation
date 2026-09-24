# 0005 — CCF com varredura de lags

- Status: Aceito
- Data: 2026-09-21

## Contexto

A Release 2 (ADR 0004) entregou Pearson e Spearman, ambos correlações de defasagem zero entre o
retorno log de $d_i$ e $d_j$. O TCC (§3.6) trata a CCF (Cross-Correlation Function) como o núcleo
metodológico: uma medida de associação entre as duas séries em diferentes defasagens
**intradiárias** (minutos dentro da janela), não apenas na defasagem zero. A ADR 0004 já havia
adiado a CCF citando o problema de reduzir uma função de lags a um escalar comparável célula a
célula na matriz $\mathbf{V}$.

## Decisão

1. **CCF por varredura de lag inteiro em minutos**: para um par $(d_i, d_j)$ já alinhados pela
   grade M1 uniforme, calcula-se $\mathrm{corr}(r_{i,t}, r_{j,t+k})$ para
   $k \in [-\text{max\_lag}, \text{max\_lag}]$ via Pearson, deslizando a janela nas bordas.
2. **Redução a escalar**: o coeficiente reportado na matriz $\mathbf{V}$ é o de **maior módulo**
   entre os lags varridos, e o lag correspondente (`lag`, em minutos) é persistido junto ao par —
   preserva a comparabilidade célula a célula da matriz (like Pearson/Spearman) sem descartar a
   informação de defasagem, que fica disponível na tabela de pares.
3. **`max_lag` parametrizável** (`analysis.ccf_max_lag`, padrão 5 minutos): mantém a
   reprodutibilidade e a filosofia de janela intradiária fixa da ADR 0004.
4. **Mesma interface `CorrelationMethod`**: `CCFMethod` implementa `compute` e é plugável via
   `analysis.methods: [..., ccf]`, sem alterar a Camada de Armazenamento ou o motor
   (`CrossCorrelationEngine`). `CorrelationResult` ganha o campo `lag: int = 0` (0 para
   Pearson/Spearman, mantendo compatibilidade).
5. **Estabilidade e significância reaproveitadas**: `stability_std` recalcula a CCF (com nova
   varredura de lag) em cada sub-janela, e o p-valor reportado é o do Pearson no lag ótimo.

## Consequências

- A tabela de pares ganha a coluna `lag` (minutos, dentro de `[-max_lag, max_lag]`); 0 para
  Pearson/Spearman.
- `max_lag` grande demais ($n \leq 3 + 2 \cdot \text{max\_lag}$ minutos na janela) degrada para
  `nan`, sinalizando amostra insuficiente em vez de resultado espúrio.
- O custo computacional por par cresce linearmente com `max_lag` (uma chamada a `pearsonr` por
  lag), aceitável para os tamanhos de janela do projeto.

## Alternativas consideradas

- **Reportar a função de lags completa por par**: mais fiel à CCF, mas inviabiliza a matriz
  $\mathbf{V}$ escalar por célula; adiado — pode ser exposto depois como artefato auxiliar por par.
- **Usar `scipy.signal.correlate`**: mais rápido para `max_lag` grande, mas não devolve p-valor por
  lag; como a janela é pequena (minutos), o laço com `pearsonr` é suficiente e mantém o teste de
  significância por lag.
