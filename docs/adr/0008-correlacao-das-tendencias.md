# 0008 — Correlação das tendências na janela 10:00–17:00

- Status: Aceito
- Data: 2026-10-05

## Contexto

A Release 4 (ADR 0006) entregou a decomposição de tendência e a Release 5 (ADR 0007) os métodos
Informação Mútua, ρDCCA e MF-DCCA. Falta fechar a amostragem comparando os 10 pregões pela
**forma da tendência**, e não pelo retorno minuto a minuto, restrita ao trecho mais líquido do
pregão: sem o leilão/abertura (antes das 10:00) e sem o fechamento (depois das 17:00).

## Decisão

1. **Tendência como série de entrada**: `analysis.trends` lista os decompositores aplicados ao close
   de cada pregão antes de correlacionar (`[]` mantém o comportamento das releases anteriores). A
   série correlacionada é `analysis.value` aplicado à tendência — com `log_return`, o retorno log
   da tendência, que preserva a inclinação minuto a minuto e é a entrada natural do DCCA (que
   integra a série no perfil).
2. **Ambas as tendências** (`[moving_average, stl]`) na mesma execução: o motor roda uma vez por
   tendência, e cada resultado vai para uma partição própria,
   `correlations/trend=<t>/method=<m>/` + `heatmap_<m>.png`. O manifesto registra as tendências e os
   parâmetros de decomposição; o `REPORT.md` tem uma seção por tendência.
3. **Janela contínua 10:00–17:00**, sem cortes intermediários; a decomposição é feita dentro da
   janela.
4. **Só MI, ρDCCA e MF-DCCA**: Pearson/Spearman/CCF sobre séries suavizadas inflam a correlação
   pela autocorrelação induzida pelo filtro; os três métodos escolhidos têm significância por
   surrogates de deslocamento circular, que preservam essa autocorrelação (ADR 0007).
5. **`dcca_scale` = 60 min**: a tendência já remove flutuações abaixo de ~30 min, então a escala
   DCCA deve ficar acima do horizonte de suavização; 60 min ainda deixa caixas suficientes nas
   sub-janelas de estabilidade (~140 min).
6. **Amostragem separada** `samples/win-10d-trend/` gerada a partir de `config/sample-trend.yaml`
   (`python scripts/make_sample.py --config config/sample-trend.yaml --dest samples/win-10d-trend`),
   sem alterar `samples/win-10d-example/`.

## Consequências

- `pipeline.analyze` passa a devolver um dicionário `{tendência: AnalysisOutput}` (`None` sem
  tendência); `run`, o report e o `main.py` iteram sobre ele.
- As associações entre tendências são bem mais fortes que entre retornos crus (|ρDCCA| até ~0,8),
  como esperado para séries de baixa frequência; o p-valor por surrogates evita lê-las como
  significativas só por serem suaves.
- Bordas: a média móvel usa janela parcial e o STL extrapola nas extremidades da janela
  10:00–17:00; os primeiros/últimos ~15 min da tendência são menos confiáveis.
- O custo dobra com duas tendências (~1 min para a amostragem com 199 surrogates).

## Alternativas consideradas

- **Correlacionar o nível da tendência (`value: close`)**: dominado pela direção global do
  pregão (alta × queda), quase sempre perto de ±1 nos métodos lineares e sem significado para o
  DCCA, que espera incrementos.
- **Correlacionar o resíduo (série sem tendência)**: responde a outra pergunta (oscilações de curto
  prazo) — fica disponível trocando a série, mas não é o foco desta release.
- **Duas janelas separadas (10:00–11:30 e 14:00–17:00)**: adiado; por ora a janela é contínua.
- **Decompor o pregão inteiro e recortar a janela depois**: reduz o efeito de borda, mas exige uma
  segunda grade (sessão completa × janela de análise); adiado.
