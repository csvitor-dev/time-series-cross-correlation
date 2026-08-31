# 0001 — Pipeline em camadas (pipes-and-filters)

- Status: Aceito
- Data: 2026-08-31

## Contexto

O projeto precisa ir da captura de candles intradiários do WIN até a integração de resultados de
correlação a um dashboard existente. Captura, limpeza, persistência, análise estatística e
apresentação têm taxas de mudança e requisitos de qualidade distintos. O trabalho é de caráter
acadêmico: exige reprodutibilidade e auditabilidade.

## Decisão

Organizar o sistema como um pipeline em camadas unidirecional (Captura → Pré-processamento →
Armazenamento → Análise → Apresentação). Cada camada fala apenas com as adjacentes por meio de
contratos explícitos (schemas/interfaces) e persiste seus dados intermediários. A fonte de dados
e o método de correlação são componentes plugáveis atrás de interfaces (Inversão de Dependência).

## Consequências

- Cada camada é testável e evolui isoladamente; dados intermediários persistidos permitem
  reexecutar etapas sem recaptura.
- A Release 1 entrega apenas Captura, Pré-processamento e Armazenamento.
- Custo: mais fronteiras e serialização entre etapas do que uma abordagem monolítica.

## Alternativas consideradas

- **Script único monolítico**: mais rápido de escrever, mas inviabiliza troca de fonte/método,
  testes isolados e auditoria — requisitos centrais da pesquisa.
