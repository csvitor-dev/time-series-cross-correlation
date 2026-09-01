# 0004 — Camada de Análise: correlação cruzada par a par

- Status: Aceito
- Data: 2026-08-31

## Contexto

O TCC (`Análise da correlação cruzada em séries financeiras do Mini-Índice Ibovespa`, §3.3–3.6)
modela a análise assim: a base $\mathscr{D} = (d_1, \dots, d_n)$ reúne $n$ séries diárias
intradiárias ($d_1$ o dia mais antigo, $d_n$ o mais recente). Para cada par $(d_i, d_j)$ com
$j < i$ define-se $v_{i,j} = \mathrm{corr}(d_i, d_j)$; fixado $d_i$, o período
$\mathscr{P}_i = (v_{i,j})_1^{\,j=i-1}$ reúne os coeficientes com todos os dias anteriores. A matriz
$\mathbf{V} = [v_{i,j}]_n^{i,j=1}$ é simétrica, tem diagonal 1 e é exibida como mapa de calor
(triângulo superior, rótulos $d_n \dots d_1$). A validação não é só visual: p-valor, comparação
entre defasagens e estabilidade entre janelas.

A Release 1 já entrega os candles M1 limpos e selados e a estrutura de pares. Falta calcular os
coeficientes.

## Decisão

1. **Série por dia = retorno log do close**: $r_t = \ln(\text{close}_t / \text{close}_{t-1})$.
   Aproxima estacionariedade, atenuando a limitação da CCF/Pearson citada no §3.6. Alternativas
   (`close`, `zscore`) ficam disponíveis por configuração.
2. **Janela intradiária fixa e uniforme** (`analysis.window`, ex. 09:00–17:55 America/Sao_Paulo),
   reindexada à grade M1. N constante entre todos os pares → coeficientes e p-valores comparáveis
   célula a célula; adere ao "janelas de tempo uniformes" do TCC; base direta para a estabilidade
   entre sub-janelas. Minutos ausentes viram retorno 0; a **cobertura** (minutos reais / total) é
   registrada por dia no manifesto e sinalizada no report abaixo de `min_coverage`.
   Descartado o alinhamento por interseção de minutos comuns (N variável por par).
3. **Métodos plugáveis** via `CorrelationMethod` (ABC). Esta release: **Pearson** e **Spearman**
   (`scipy.stats`). CCF com varredura de lags, ρDCCA e MF-DCCA entram depois pela mesma interface.
4. **scipy** como dependência (Pearson, Spearman, p-valores).
5. **Estabilidade**: cada par é recalculado em `stability_subwindows` blocos contíguos da janela;
   `stability_std` = desvio-padrão dos coeficientes entre blocos.
6. **Persistência**: `data/processed/correlations/method=<m>/{pairs,matrix}.parquet` — derivado e
   reproduzível, logo **sobrescrevível** (ao contrário de `seal_day`). Heatmap PNG por método.
7. **Camada de acesso a dados intocada**: a Análise lê os Parquet locais via
   `CandleStore.read_days`. A captura real continua atrás de `MarketDataSource` / `OHLCBar`.

## Consequências

- `V` e o heatmap saem direto de `pandas`/`numpy`, sem SQL.
- A janela é um parâmetro versionado → execuções reproduzíveis e comparáveis.
- Cobertura baixa num dia (pregão curto, feriado parcial) é visível no report, não silenciosa.
- `scipy` engorda o ambiente (~30 MB).

## Alternativas consideradas

- **Interseção de minutos comuns**: sem imputação, mas N variável degrada a comparação entre
  células e a significância.
- **CCF já nesta release**: dá uma função de lags que precisaria ser reduzida a escalar; adiado
  junto com ρDCCA/MF-DCCA para manter o escopo enxuto.
- **Implementar as estatísticas à mão** (sem scipy): mais código de estatística para manter.
