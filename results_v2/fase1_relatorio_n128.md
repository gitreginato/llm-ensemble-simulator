# Relatorio FASE 1: Ensemble LLM vs Modelo Probabilistico FASE 0
Cenario: SLZ-C-ARMY-V5-ALT
N: 128 personas
Sinteses OK: 108
Custo: $0.0361

## Resultados Gerais
- Taxa de conversao (sintetizador): 15.7%
- Agendaram: 17/108
- Divergence score medio: 0.072

## Distribuicao de Decisoes
### Sintetizador
- visualizou: 71 (65.7%)
- clicou: 18 (16.7%)
- agendou: 17 (15.7%)
- ignorou: 2 (1.9%)

### Modelos individuais
- visualizou: 144 (53.1%)
- clicou: 72 (26.6%)
- agendou: 45 (16.6%)
- ignorou: 10 (3.7%)

## Objecoes Consolidadas
- area_externa: 92
- budget: 73
- concorrencia_local: 63
- existing_solution: 61
- ticket_alto: 61
- contract_fear: 28
- skepticism: 22
- complexity: 13
- need_lack: 10
- timing: 7

## Por Source
| Source | OK | Fail | Avg Latency | Avg Tokens |
|---|---|---|---|---|
| gocat | 271 | 369 | 23604ms | 1484 |

## Por Bairro
| Bairro | Total | Agendou | Clicou | Visualizou | Ignorou | Conv % |
|---|---|---|---|---|---|---|
| Turu | 20 | 2 | 4 | 14 | 0 | 10.0% |
| Renascenca | 16 | 0 | 3 | 12 | 1 | 0.0% |
| Calhau | 15 | 3 | 2 | 10 | 0 | 20.0% |
| Centro | 12 | 1 | 1 | 10 | 0 | 8.3% |
| Cohama | 10 | 1 | 1 | 7 | 1 | 10.0% |
| Joao Paulo | 8 | 4 | 0 | 4 | 0 | 50.0% |
| Olho DAgua | 6 | 2 | 0 | 4 | 0 | 33.3% |
| Vila Embratel | 4 | 2 | 2 | 0 | 0 | 50.0% |
| Cidade Operaria | 4 | 0 | 2 | 2 | 0 | 0.0% |
| Vinhais | 4 | 2 | 1 | 1 | 0 | 50.0% |
| Coroadinho | 3 | 0 | 1 | 2 | 0 | 0.0% |
| Ponta do Farol | 3 | 0 | 1 | 2 | 0 | 0.0% |
| Sao Cristovao | 3 | 0 | 0 | 3 | 0 | 0.0% |

## Por Nicho
| Nicho | Total | Agendou | Clicou | Visualizou | Ignorou | Conv % |
|---|---|---|---|---|---|---|
| autopecas | 9 | 1 | 3 | 5 | 0 | 11.1% |
| mercadinho | 8 | 3 | 0 | 4 | 1 | 37.5% |
| barbearia | 6 | 0 | 2 | 4 | 0 | 0.0% |
| borracharia | 6 | 0 | 1 | 5 | 0 | 0.0% |
| clinica_veterinaria | 6 | 1 | 1 | 4 | 0 | 16.7% |
| estudio_tatuagem | 5 | 0 | 1 | 4 | 0 | 0.0% |
| oficina | 5 | 2 | 2 | 1 | 0 | 40.0% |
| fisioterapia | 5 | 1 | 1 | 3 | 0 | 20.0% |
| mecanica_diesel | 5 | 1 | 0 | 3 | 1 | 20.0% |
| salao | 5 | 1 | 1 | 3 | 0 | 20.0% |
| loja_roupas | 4 | 0 | 1 | 3 | 0 | 0.0% |
| restaurante | 4 | 1 | 1 | 2 | 0 | 25.0% |
| optica | 4 | 0 | 0 | 4 | 0 | 0.0% |
| loja_calcados | 4 | 0 | 0 | 4 | 0 | 0.0% |
| clinica | 4 | 1 | 0 | 3 | 0 | 25.0% |
| estacionamento | 3 | 1 | 0 | 2 | 0 | 33.3% |
| academia | 3 | 0 | 1 | 2 | 0 | 0.0% |
| consultorio_odonto | 3 | 0 | 1 | 2 | 0 | 0.0% |
| bar | 3 | 1 | 0 | 2 | 0 | 33.3% |
| pet_shop | 3 | 1 | 0 | 2 | 0 | 33.3% |
| hamburgueria | 3 | 1 | 0 | 2 | 0 | 33.3% |
| lava_jato | 3 | 0 | 1 | 2 | 0 | 0.0% |
| farmacia | 2 | 0 | 0 | 2 | 0 | 0.0% |
| laboratorio | 2 | 0 | 1 | 1 | 0 | 0.0% |
| mercearia | 2 | 1 | 0 | 1 | 0 | 50.0% |
| estetica | 1 | 0 | 0 | 1 | 0 | 0.0% |

## Comparativo FASE 0 vs FASE 1
FASE 0 (modelo probabilistico): conversao ~16%, 275 combos bairro x nicho
FASE 1 (ensemble LLM): conversao 15.7%, 108 personas

Top 8 combos FASE 0 (mapa de prospeccao):
- Centro/mercearia: conv=100.0% pot=162
- Centro/oficina: conv=60.0% pot=97
- Renascenca/clinica: conv=50.0% pot=96
- Turu/fisioterapia: conv=40.0% pot=96
- Calhau/salao: conv=50.0% pot=94
- Calhau/mecanica_diesel: conv=50.0% pot=94
- Cohama/optica: conv=60.0% pot=84
- Centro/optica: conv=50.0% pot=81
