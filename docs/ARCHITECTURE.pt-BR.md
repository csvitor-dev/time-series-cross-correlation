# Arquitetura do Projeto — Análise de Correlação Cruzada em Séries Temporais Financeiras

## 1. Visão Geral

Este documento descreve a arquitetura de software adotada para o projeto de análise de correlação cruzada em séries temporais financeiras, bem como os *concerns* (preocupações arquiteturais) que orientaram as decisões de design, alinhados ao escopo metodológico definido na pesquisa.

O objeto de estudo é o contrato futuro **Mini-Índice Ibovespa (WIN)**, com dados intradiários coletados entre junho de 2025 e junho de 2026, considerando exclusivamente dias de operação. A análise não compara ativos distintos entre si, mas investiga a **correlação de um dia de referência ($d_n$) com os dias anteriores da própria série** ($d_{n-1}, d_{n-2}, \dots, d_1$), formando uma matriz de defasagens que é posteriormente representada como mapa de calor e integrada a um **dashboard já existente**.

O sistema é organizado como um **pipeline em camadas (layered pipeline / pipes-and-filters)**, no qual os dados fluem de forma unidirecional desde a captura na fonte (MetaTrader 5) até a integração dos resultados de correlação ao dashboard. Cada camada possui responsabilidade única, comunica-se apenas com as camadas adjacentes por meio de contratos bem definidos (interfaces/schemas), e pode ser testada e evoluída de forma isolada.

Este estilo arquitetural foi escolhido por três razões principais:

1. **Separação de responsabilidades**: captura, limpeza, persistência, análise estatística e apresentação são preocupações distintas, com taxas de mudança e requisitos de qualidade diferentes.
2. **Extensibilidade**: a fonte de dados (MT5) é tratada como um detalhe de implementação isolado atrás de uma interface, permitindo eventual substituição por outra corretora ou provedor de dados sem impacto nas demais camadas (princípio da Inversão de Dependência). Da mesma forma, o método de correlação é tratado como um componente plugável, já que a pesquisa prevê a investigação de múltiplas técnicas (CCF, Pearson, Spearman, DCCA/MF-DCCA).
3. **Reprodutibilidade científica**: um pipeline com estágios explícitos e dados intermediários persistidos facilita auditoria, versionamento e repetição dos experimentos — requisito central em um projeto de caráter acadêmico e documental.

## 2. Visão em Camadas

```
┌─────────────────────────────────────────────────┐
│  Camada de Apresentação (Dashboard)              │
│  - Integração com dashboard existente            │
│  - Mapa de calor de correlação dia x dia         │
│  - Sobreposição gráfica de séries defasadas      │
├─────────────────────────────────────────────────┤
│  Camada de Análise (Correlation Engine)          │
│  - CCF (Cross-Correlation Function)              │
│  - Pearson / Spearman                            │
│  - DCCA / ρDCCA / MF-DCCA (métodos candidatos)   │
│  - Testes de significância e estabilidade        │
├─────────────────────────────────────────────────┤
│  Camada de Armazenamento (Data Store)            │
│  - Base de dados específica das séries (candles) │
│  - Estrutura de pares/defasagens (d_i, d_k)      │
├─────────────────────────────────────────────────┤
│  Camada de Pré-processamento (ETL/Cleaning)      │
│  - Ordenação cronológica, tratamento de data/hora│
│  - Backfill / imputação de lacunas               │
│  - Filtragem por dias de operação                │
├─────────────────────────────────────────────────┤
│  Camada de Captura (Data Acquisition)            │
│  - Integração com MetaTrader 5 (WIN, intradiário)│
└─────────────────────────────────────────────────┘
```

### 2.1 Camada de Captura (Data Acquisition)

Responsável por obter o histórico intradiário de cotações (estrutura de *candles*, OHLC) do contrato futuro WIN diretamente do terminal MetaTrader 5, via API oficial em Python, no período compreendido entre junho de 2025 e junho de 2026. Esta camada expõe uma interface abstrata de aquisição de dados, da qual o cliente MT5 é uma implementação concreta — isso isola o restante do sistema de particularidades da fonte (formato de retorno, fuso horário do servidor da corretora, limites de requisição), ainda que a troca de corretora não seja um requisito da pesquisa atual.

### 2.2 Camada de Pré-processamento (ETL/Cleaning)

Responsável por adequar a base extraída à análise estatística: organização cronológica dos registros, tratamento das informações de data e hora, preenchimento de lacunas por *backfill* e mecanismos equivalentes de imputação operacional (preservando-se o *datatype* originalmente retornado pelo pacote cliente MT5), e filtragem para contemplar exclusivamente os dias de operação do período analisado. O resultado é uma série estruturada a partir dos *candles* (OHLC), pronta para ser organizada em pares de dias na etapa seguinte.

### 2.3 Camada de Armazenamento (Data Store)

Responsável por persistir a base de dados específica das séries, já limpa e organizada cronologicamente. Esta camada também estrutura os **pares de defasagem** definidos na metodologia: para cada dia de referência $d_i$, é mantido o conjunto $\mathcal{P}_i = (v_{i,k})$ dos pares $(d_i, d_k)$ com os dias anteriores $d_k$, formando a base sobre a qual a matriz de correlação será calculada. Um formato tipado e eficiente (ex.: Parquet ou SQLite) serve como fronteira estável entre o pré-processamento e a análise, permitindo reexecutar os cálculos sem necessidade de recaptura dos dados.

### 2.4 Camada de Análise (Correlation Engine)

Responsável pelo cálculo estatístico da correlação entre o dia de referência e cada um dos dias anteriores da série, dentro de uma mesma janela intradiária. Esta camada é projetada para suportar múltiplos métodos de correlação, conforme previsto na metodologia:

- **CCF (Cross-Correlation Function)**: medida de associação entre as duas séries em diferentes defasagens temporais, núcleo metodológico da pesquisa;
- **Pearson**: força e direção da relação linear, adequada a dados com distribuição normal bivariada;
- **Spearman**: relação monotônica baseada em *ranks*, mais robusta a *outliers*;
- **DCCA / ρDCCA / MF-DCCA**: métodos candidatos para avaliação de dependência de longo alcance e propriedades multifractais em séries não estacionárias.

Além do cálculo dos coeficientes, esta camada é responsável por procedimentos de validação estatística — testes de significância, comparação entre defasagens e análise de estabilidade dos resultados em diferentes janelas de tempo — de modo que a identificação de correlações não se baseie exclusivamente em inspeção visual.

### 2.5 Camada de Apresentação (Dashboard)

Responsável por integrar os resultados da análise a um **dashboard já existente**, expandido com o novo recurso de correlação. Contempla a geração do mapa de calor correlacional (matriz $d_i \times d_k$), a exibição simultânea das séries temporais com sobreposição gráfica, e a disponibilização dos resultados numéricos e gráficos para observação comparativa de tendências, variações e defasagens.

## 3. Concerns (CoCs) Arquiteturais

Concerns são as preocupações que orientam e restringem as decisões de arquitetura, no sentido definido pela ISO/IEC/IEEE 42010. Para este projeto, foram identificados os seguintes concerns:

### 3.1 Concerns Funcionais

| Concern | Descrição |
|---|---|
| Captura de dados | Obtenção confiável do histórico intradiário do WIN via MT5, no período jun/2025–jun/2026 |
| Consistência temporal | Ordenação cronológica, tratamento de data/hora e filtragem por dias de operação |
| Estruturação de defasagens | Organizar a base em pares $(d_i, d_k)$ para cada dia de referência, conforme a modelagem $\mathcal{P}_i$ |
| Cálculo de correlação | Suportar múltiplos métodos (CCF, Pearson, Spearman, DCCA/MF-DCCA) sobre os pares de dias |
| Validação estatística | Aplicar testes de significância e análise de estabilidade entre janelas de tempo |
| Integração com dashboard | Disponibilizar resultados numéricos e o mapa de calor no dashboard existente |

### 3.2 Concerns Não Funcionais (Atributos de Qualidade)

| Concern | Descrição | Impacto na arquitetura |
|---|---|---|
| **Reprodutibilidade** | Mesma entrada e mesmos parâmetros devem produzir a mesma saída, essencial para a validação documental/acadêmica | Estágios de pipeline explícitos, dados intermediários persistidos, parâmetros (período, método de correlação, janela) versionados em arquivo de configuração |
| **Extensibilidade metodológica** | A pesquisa prevê a comparação entre diferentes métodos de correlação (CCF, Pearson, Spearman, DCCA, MF-DCCA) | Camada de Análise projetada com interface plugável por método, permitindo adicionar/comparar técnicas sem alterar as demais camadas |
| **Testabilidade** | Cada camada deve poder ser testada isoladamente | Separação clara entre captura, processamento, estruturação de pares e análise; uso de dados sintéticos/mockados nos testes |
| **Integridade dos dados** | Tratamento de lacunas e ausências sem descaracterizar o *datatype* original retornado pelo MT5 | Camada de pré-processamento dedicada a *backfill*/imputação e à preservação de tipos de dados |
| **Escalabilidade combinatória** | O número de pares $(d_i, d_k)$ cresce quadraticamente com o tamanho da amostra ($n$ dias) | Estrutura de armazenamento otimizada para consulta por pares; cálculo vetorizado na camada de análise |
| **Integração com sistema existente** | O dashboard já existe e será expandido, não substituído | Camada de Apresentação desacoplada via contrato de dados (API/schema) que o dashboard consome, minimizando acoplamento com sua implementação atual |
| **Rastreabilidade/Auditabilidade** | Cada execução deve registrar metadados suficientes para auditoria acadêmica | Metadados de captura e do método de correlação aplicado armazenados junto à base processada |

### 3.3 Premissas e Restrições Assumidas

As seguintes premissas, já declaradas na metodologia da pesquisa, orientam diretamente as decisões arquiteturais:

- **Ativo analisado**: contrato futuro Mini-Índice Ibovespa (WIN), único instrumento em estudo
- **Período**: junho de 2025 a junho de 2026, exclusivamente dias de operação
- **Granularidade**: dados intradiários, estruturados em *candles* (OHLC)
- **Unidade de correlação**: dia contra dia (não ativo contra ativo) — cada par $(d_i, d_k)$ é uma observação
- **Tamanho de amostra de referência**: $n=10$ dias, conforme exemplo apresentado na metodologia (parametrizável)
- **Tratamento de ausências**: *backfill* e mecanismos equivalentes de imputação, preservando o *datatype* original
- **Métodos de correlação candidatos**: CCF (núcleo metodológico), Pearson, Spearman, DCCA/ρDCCA e MF-DCCA
- **Validação**: não exclusivamente visual — inclui testes de significância, comparação entre defasagens e estabilidade entre janelas
- **Canal de apresentação**: dashboard já existente, a ser expandido (não é escopo criar um novo painel do zero)

## 4. Escopo da Release 1

A primeira release contempla as camadas de **Captura**, **Pré-processamento** e **Armazenamento** (incluindo a estruturação dos pares de defasagem), com o objetivo de produzir a base de dados específica das séries — organizada segundo a modelagem $\mathcal{P}_i = (v_{i,k})$ — pronta para consumo pela camada de Análise em uma release subsequente, que incluirá o cálculo dos coeficientes de correlação e a geração do mapa de calor a ser integrado ao dashboard.

## 5. Escopo da Release 2

A segunda release implementa a **Camada de Análise**: dada a base de dias selados, calcula a matriz de correlação $\mathbf{V} = [v_{i,j}]$ entre as séries diárias, com $v_{i,j} = \mathrm{corr}(d_i, d_j)$ para $j < i$, e persiste os coeficientes, o p-valor par a par e uma medida de estabilidade entre sub-janelas. A série de cada dia é o **retorno log do close** numa **janela intradiária uniforme** parametrizada. Os métodos são plugáveis (`CorrelationMethod`); esta release entrega **Pearson** e **Spearman** — CCF com varredura de lags, ρDCCA e MF-DCCA entram depois pela mesma interface. A visualização gera o **mapa de calor** da matriz $\mathbf{V}$ completa e simétrica (embora, por $v_{i,j}=v_{j,i}$, apenas o triângulo superior seja informativo). A integração ao dashboard existente permanece fora de escopo. Ver `docs/adr/0004-camada-de-analise-correlacao-cruzada.md`.