# Relatorio FASE 1: Ensemble LLM vs Modelo Probabilistico FASE 0
Cenario: SLZ-C-ARMY-V5-FAST
N: 8 personas
Sinteses OK: 8
Custo: $0.0000

## Resultados Gerais
- Taxa de conversao (sintetizador): 0.0%
- Agendaram: 0/8
- Divergence score medio: 0.353

## Distribuicao de Decisoes
### Sintetizador
- clicou: 4 (50.0%)
- visualizou: 4 (50.0%)

### Modelos individuais
- visualizou: 19 (42.2%)
- clicou: 17 (37.8%)
- agendou: 5 (11.1%)
- ignorou: 4 (8.9%)

## Objecoes Consolidadas
- area_externa: 7
- contract_fear: 6
- existing_solution: 6
- concorrencia_local: 4
- skepticism: 4
- complexity: 3
- need_lack: 3
- timing: 2

## Por Source
| Source | OK | Fail | Avg Latency | Avg Tokens |
|---|---|---|---|---|
| cline | 6 | 2 | 25906ms | 0 |
| gocat | 24 | 0 | 11556ms | 1889 |
| ollama | 15 | 1 | 22165ms | 2606 |

## Por Bairro
| Bairro | Total | Agendou | Clicou | Visualizou | Ignorou | Conv % |
|---|---|---|---|---|---|---|
| Renascenca | 2 | 0 | 1 | 1 | 0 | 0.0% |
| Turu | 2 | 0 | 1 | 1 | 0 | 0.0% |
| Centro | 1 | 0 | 0 | 1 | 0 | 0.0% |
| Joao Paulo | 1 | 0 | 0 | 1 | 0 | 0.0% |
| Vila Embratel | 1 | 0 | 1 | 0 | 0 | 0.0% |
| Calhau | 1 | 0 | 1 | 0 | 0 | 0.0% |

## Por Nicho
| Nicho | Total | Agendou | Clicou | Visualizou | Ignorou | Conv % |
|---|---|---|---|---|---|---|
| estudio_tatuagem | 3 | 0 | 1 | 2 | 0 | 0.0% |
| estacionamento | 1 | 0 | 1 | 0 | 0 | 0.0% |
| autopecas | 1 | 0 | 0 | 1 | 0 | 0.0% |
| barbearia | 1 | 0 | 1 | 0 | 0 | 0.0% |
| oficina | 1 | 0 | 1 | 0 | 0 | 0.0% |
| academia | 1 | 0 | 0 | 1 | 0 | 0.0% |

## Comparativo FASE 0 vs FASE 1
FASE 0 (modelo probabilistico): conversao ~16%, 275 combos bairro x nicho
FASE 1 (ensemble LLM): conversao 0.0%, 8 personas

Top 8 combos FASE 0 (mapa de prospeccao):
- Centro/mercearia: conv=100.0% pot=162
- Centro/oficina: conv=60.0% pot=97
- Renascenca/clinica: conv=50.0% pot=96
- Turu/fisioterapia: conv=40.0% pot=96
- Calhau/salao: conv=50.0% pot=94
- Calhau/mecanica_diesel: conv=50.0% pot=94
- Cohama/optica: conv=60.0% pot=84
- Centro/optica: conv=50.0% pot=81
