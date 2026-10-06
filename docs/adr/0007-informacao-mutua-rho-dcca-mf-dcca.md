# 0007 — Informação Mútua, ρDCCA e MF-DCCA (ρ_q)

- Status: Aceito
- Data: 2026-10-05

## Contexto

Pearson, Spearman e CCF (ADRs 0004 e 0005) medem associação linear ou monotônica e supõem séries
aproximadamente estacionárias. O TCC prevê também dependências **não lineares** e a correlação em
séries **não estacionárias**, com atenção às **grandes flutuações** — o que motiva a Informação
Mútua, o ρDCCA (Zebende, 2011) e o MF-DCCA (Zhou, 2008). Os três precisam caber na matriz
$\mathbf{V}$ escalar por célula e no mesmo `CorrelationMethod` plugável.

## Decisão

1. **Informação Mútua (`mi`)**: estimador *plug-in* sobre bins por **quantis** (`mi_bins`, padrão
   8; invariante a transformações monotônicas), com o viés de amostra finita subtraído pela média
   da MI dos *surrogates*. O escalar reportado é o **coeficiente de Linfoot**
   $\sqrt{1 - e^{-2\,\mathrm{MI}}} \in [0, 1]$, que coincide com $|\rho|$ no caso gaussiano —
   comparável aos demais, mas **sem sinal**.
2. **Núcleo DCCA compartilhado** (`analysis.dcca`): perfil acumulado de cada série, caixas
   **sobrepostas** de tamanho $s+1$ (`dcca_scale`, padrão 20 min) com tendência linear removida
   por caixa, e as covariâncias $f^2_{xy}, f^2_{xx}, f^2_{yy}$ por caixa.
3. **ρDCCA (`rho_dcca`)**: $\rho_{DCCA}(s) = F^2_{xy} / (F_{xx} F_{yy})$ (Zebende, 2011).
4. **MF-DCCA (`mf_dcca`) reduzido a ρ_q** (Kwapień, Oświęcimka e Drożdż, 2015):
   $\rho_q(s) = F^{xy}_q / \sqrt{F^{xx}_q F^{yy}_q}$, com
   $F^{xy}_q = \langle \mathrm{sign}(f^2_{xy})\,|f^2_{xy}|^{q/2} \rangle$. Fica em $[-1, 1]$ e
   generaliza o ρDCCA ($\rho_2 = \rho_{DCCA}$); $q > 2$ realça as grandes flutuações
   (`mfdcca_q`, padrão 4). Só o ρ_q é reportado — expoentes $h_{xy}(q)$ e largura do espectro
   ficam fora.
5. **Significância por surrogates de deslocamento circular**: $y$ é rotacionado por $k$ minutos
   ($k$ sorteado sem reposição entre $n/10$ e $n - n/10$; `surrogates`, padrão 199; `seed`, padrão
   0), o que preserva a autocorrelação de cada série e quebra só o alinhamento entre elas. O
   p-valor é $(1 + \#\{|T^*| \geq |T|\}) / (1 + N)$.

## Consequências

- O heatmap de `mi` ocupa só a metade positiva da escala; associação negativa aparece como
  positiva. A leitura do sinal fica com ρDCCA/MF-DCCA.
- Ler ρDCCA e MF-DCCA lado a lado indica a origem da associação: $\rho_4 > \rho_{DCCA}$ sugere
  correlação concentrada nos movimentos extremos; $\rho_4 < \rho_{DCCA}$, nas flutuações típicas.
- O p-valor mínimo atingível é $1/(1+N) = 0{,}005$ com 199 surrogates. O custo cresce
  linearmente com $N$ (~40 s para a amostragem de 10 pregões com os seis métodos).
- Resultados reprodutíveis: mesma semente, mesmos surrogates.
- `dcca_scale` grande demais para a janela ($n < 2(s+1)$, inclusive nas sub-janelas de
  estabilidade) degrada para `nan`, como no CCF.

## Alternativas consideradas

- **MI pelo estimador KSG (k-vizinhos)**: menos viesado em variáveis contínuas, mas o M1 do WIN tem
  muitos empates (retornos discretos em *ticks*), o que degrada estimadores por distância; bins por
  quantis com correção por surrogates são robustos a empates.
- **Expoente $h_{xy}(q)$ ou largura $\Delta h_{xy}$ como escalar do MF-DCCA**: medem persistência e
  complexidade, não intensidade de associação, e exigem ajuste em log-log com poucas escalas por
  pregão — ruidosos por par.
- **Permutação aleatória como hipótese nula**: destrói a autocorrelação e torna o teste
  anticonservador para séries persistentes (como as tendências); o deslocamento circular a
  preserva.
- **Valores críticos tabelados do ρDCCA (Podobnik et al., 2011)**: válidos só para ruído branco
  gaussiano; os surrogates valem para qualquer estrutura marginal.
