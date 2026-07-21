# Análise de Telemetria - Ensemble V5 ALT (N=128, Seed=42)

**Data/Hora:** 2026-07-21 03:52:13
**Cenário:** SLZ-C-ARMY-V5-ALT
**Modelos:** llama-3.3-70b-versatile, openai/gpt-oss-120b, command-r-08-2024, deepseek-ai/deepseek-v4-flash, deepseek-ai/deepseek-v4-pro
**Sintetizador:** command-r-08-2024
**Total Personas:** 128
**Taxa de Conversão:** 15.74%
**Agendaram:** 17
**Sucessos:** 108
**Falhas:** 378
**Divergence Score Médio:** 0.0723
**Custo Total USD:** $0.036061

---

## 1. Estatísticas por Modelo


### llama-3.3-70b-versatile

- **Chamadas totais:** 128
- **OK:** 13 (10.16%)
- **FAIL:** 115 (89.84%)
- **Latência média:** 43327ms
- **Latência p50:** 3074ms
- **Latência p90:** 126939ms
- **Latência p99:** 131111ms
- **Latência min:** 1134ms
- **Latência max:** 131311ms
- **Prompt tokens médio:** 1019
- **Completion tokens médio:** 134
- **Total tokens médio:** 1152
- **Tipos de falha:**
  - empty_error: 68 (53.12%)
  - HTTP 503: {"error":{"message":"all providers failed for model 'llama-3.3-70b-versatile'","type":"all_providers_failed","code":"all_providers_failed"}}
: 47 (36.72%)
- **HTTP Status Codes:**
  - 200: 13

### openai/gpt-oss-120b

- **Chamadas totais:** 128
- **OK:** 62 (48.44%)
- **FAIL:** 66 (51.56%)
- **Latência média:** 13279ms
- **Latência p50:** 3559ms
- **Latência p90:** 64328ms
- **Latência p99:** 94775ms
- **Latência min:** 2100ms
- **Latência max:** 127516ms
- **Prompt tokens médio:** 994
- **Completion tokens médio:** 831
- **Total tokens médio:** 1825
- **Tipos de falha:**
  - HTTP 503: {"error":{"message":"all providers failed for model 'openai/gpt-oss-120b'","type":"all_providers_failed","code":"all_providers_failed"}}
: 35 (27.34%)
  - empty_error: 31 (24.22%)
- **HTTP Status Codes:**
  - 200: 62

### command-r-08-2024

- **Chamadas totais:** 128
- **OK:** 109 (85.16%)
- **FAIL:** 19 (14.84%)
- **Latência média:** 9674ms
- **Latência p50:** 5100ms
- **Latência p90:** 25579ms
- **Latência p99:** 62135ms
- **Latência min:** 2478ms
- **Latência max:** 64526ms
- **Prompt tokens médio:** 1013
- **Completion tokens médio:** 144
- **Total tokens médio:** 1157
- **Tipos de falha:**
  - HTTP 503: {"error":{"message":"all providers failed for model 'command-r-08-2024'","type":"all_providers_failed","code":"all_providers_failed"}}
: 19 (14.84%)
- **HTTP Status Codes:**
  - 200: 109

### deepseek-ai/deepseek-v4-flash

- **Chamadas totais:** 128
- **OK:** 71 (55.47%)
- **FAIL:** 57 (44.53%)
- **Latência média:** 48197ms
- **Latência p50:** 39367ms
- **Latência p90:** 98714ms
- **Latência p99:** 175214ms
- **Latência min:** 8551ms
- **Latência max:** 178004ms
- **Prompt tokens médio:** 996
- **Completion tokens médio:** 830
- **Total tokens médio:** 1826
- **Tipos de falha:**
  - HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deepseek-v4-flash'","type":"all_providers_failed","code":"all_providers_failed"}}
: 53 (41.41%)
  - empty_error: 4 (3.12%)
- **HTTP Status Codes:**
  - 200: 71

### deepseek-ai/deepseek-v4-pro

- **Chamadas totais:** 128
- **OK:** 16 (12.50%)
- **FAIL:** 112 (87.50%)
- **Latência média:** 33350ms
- **Latência p50:** 11676ms
- **Latência p90:** 91290ms
- **Latência p99:** 161798ms
- **Latência min:** 2874ms
- **Latência max:** 172665ms
- **Prompt tokens médio:** 1002
- **Completion tokens médio:** 144
- **Total tokens médio:** 1146
- **Tipos de falha:**
  - HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deepseek-v4-pro'","type":"all_providers_failed","code":"all_providers_failed"}}
: 83 (64.84%)
  - empty_error: 29 (22.66%)
- **HTTP Status Codes:**
  - 200: 16

---

## 2. Estatísticas por Persona


### Distribuição de Decisões por Persona

- **0 decisões:** 11 personas (8.59%)
- **1 decisões:** 40 personas (31.25%)
- **2 decisões:** 22 personas (17.19%)
- **3 decisões:** 35 personas (27.34%)
- **4 decisões:** 18 personas (14.06%)
- **5 decisões:** 2 personas (1.56%)

### Personas com Síntese SKIP

- **Total:** 20 (15.62%)
- **IDs:** 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128

### Personas por Faixa de Decisões

- **1-2 decisões:** 62 (48.44%)
- **3-5 decisões:** 55 (42.97%)

### Correlação: Nº Decisões → Decisão Final


**0 decisões:**
  - SKIP: 11 (100.00%)

**1 decisões:**
  - visualizou: 16 (40.00%)
  - clicou: 11 (27.50%)
  - agendou: 6 (15.00%)
  - SKIP: 6 (15.00%)
  - ignorou: 1 (2.50%)

**2 decisões:**
  - visualizou: 13 (59.09%)
  - agendou: 3 (13.64%)
  - SKIP: 3 (13.64%)
  - clicou: 2 (9.09%)
  - ignorou: 1 (4.55%)

**3 decisões:**
  - visualizou: 29 (82.86%)
  - agendou: 4 (11.43%)
  - clicou: 2 (5.71%)

**4 decisões:**
  - visualizou: 11 (61.11%)
  - agendou: 4 (22.22%)
  - clicou: 3 (16.67%)

**5 decisões:**
  - visualizou: 2 (100.00%)

---

## 3. Padrões de Falha


### Sequências de Falhas Consecutivas

- **Máximo de falhas consecutivas:** 60
- **Total de janelas de falha:** 134

### Maior Janela de Falha (Posição 564-623, 60 falhas)

Modelos que falharam nesta janela:
  - Posição 564: Persona 113, command-r-08-2024, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'command-r-08-2024
  - Posição 565: Persona 114, command-r-08-2024, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'command-r-08-2024
  - Posição 566: Persona 114, deepseek-ai/deepseek-v4-flash, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 567: Persona 114, llama-3.3-70b-versatile, Erro: empty_error
  - Posição 568: Persona 114, openai/gpt-oss-120b, Erro: empty_error
  - Posição 569: Persona 114, deepseek-ai/deepseek-v4-pro, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 570: Persona 115, llama-3.3-70b-versatile, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'llama-3.3-70b-ver
  - Posição 571: Persona 115, deepseek-ai/deepseek-v4-pro, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 572: Persona 115, command-r-08-2024, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'command-r-08-2024
  - Posição 573: Persona 115, openai/gpt-oss-120b, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'openai/gpt-oss-12
  - Posição 574: Persona 115, deepseek-ai/deepseek-v4-flash, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 575: Persona 116, deepseek-ai/deepseek-v4-pro, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 576: Persona 116, command-r-08-2024, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'command-r-08-2024
  - Posição 577: Persona 116, openai/gpt-oss-120b, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'openai/gpt-oss-12
  - Posição 578: Persona 116, llama-3.3-70b-versatile, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'llama-3.3-70b-ver
  - Posição 579: Persona 116, deepseek-ai/deepseek-v4-flash, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 580: Persona 117, llama-3.3-70b-versatile, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'llama-3.3-70b-ver
  - Posição 581: Persona 117, deepseek-ai/deepseek-v4-pro, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 582: Persona 117, command-r-08-2024, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'command-r-08-2024
  - Posição 583: Persona 117, deepseek-ai/deepseek-v4-flash, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 584: Persona 117, openai/gpt-oss-120b, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'openai/gpt-oss-12
  - Posição 585: Persona 118, command-r-08-2024, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'command-r-08-2024
  - Posição 586: Persona 118, llama-3.3-70b-versatile, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'llama-3.3-70b-ver
  - Posição 587: Persona 118, openai/gpt-oss-120b, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'openai/gpt-oss-12
  - Posição 588: Persona 118, deepseek-ai/deepseek-v4-pro, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 589: Persona 118, deepseek-ai/deepseek-v4-flash, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 590: Persona 119, openai/gpt-oss-120b, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'openai/gpt-oss-12
  - Posição 591: Persona 119, llama-3.3-70b-versatile, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'llama-3.3-70b-ver
  - Posição 592: Persona 119, command-r-08-2024, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'command-r-08-2024
  - Posição 593: Persona 119, deepseek-ai/deepseek-v4-flash, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 594: Persona 119, deepseek-ai/deepseek-v4-pro, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 595: Persona 120, deepseek-ai/deepseek-v4-pro, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 596: Persona 120, openai/gpt-oss-120b, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'openai/gpt-oss-12
  - Posição 597: Persona 120, deepseek-ai/deepseek-v4-flash, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 598: Persona 120, command-r-08-2024, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'command-r-08-2024
  - Posição 599: Persona 120, llama-3.3-70b-versatile, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'llama-3.3-70b-ver
  - Posição 600: Persona 121, deepseek-ai/deepseek-v4-pro, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 601: Persona 121, deepseek-ai/deepseek-v4-flash, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 602: Persona 121, command-r-08-2024, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'command-r-08-2024
  - Posição 603: Persona 121, openai/gpt-oss-120b, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'openai/gpt-oss-12
  - Posição 604: Persona 121, llama-3.3-70b-versatile, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'llama-3.3-70b-ver
  - Posição 605: Persona 122, deepseek-ai/deepseek-v4-flash, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 606: Persona 122, command-r-08-2024, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'command-r-08-2024
  - Posição 607: Persona 122, llama-3.3-70b-versatile, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'llama-3.3-70b-ver
  - Posição 608: Persona 122, deepseek-ai/deepseek-v4-pro, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 609: Persona 122, openai/gpt-oss-120b, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'openai/gpt-oss-12
  - Posição 610: Persona 123, command-r-08-2024, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'command-r-08-2024
  - Posição 611: Persona 123, deepseek-ai/deepseek-v4-pro, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 612: Persona 123, deepseek-ai/deepseek-v4-flash, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 613: Persona 123, openai/gpt-oss-120b, Erro: empty_error
  - Posição 614: Persona 123, llama-3.3-70b-versatile, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'llama-3.3-70b-ver
  - Posição 615: Persona 124, openai/gpt-oss-120b, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'openai/gpt-oss-12
  - Posição 616: Persona 124, llama-3.3-70b-versatile, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'llama-3.3-70b-ver
  - Posição 617: Persona 124, command-r-08-2024, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'command-r-08-2024
  - Posição 618: Persona 124, deepseek-ai/deepseek-v4-pro, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 619: Persona 124, deepseek-ai/deepseek-v4-flash, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps
  - Posição 620: Persona 125, command-r-08-2024, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'command-r-08-2024
  - Posição 621: Persona 125, llama-3.3-70b-versatile, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'llama-3.3-70b-ver
  - Posição 622: Persona 125, openai/gpt-oss-120b, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'openai/gpt-oss-12
  - Posição 623: Persona 125, deepseek-ai/deepseek-v4-pro, Erro: HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/deeps

**Todas as janelas com 5+ falhas:**
  - Posição 256-260: 5 falhas consecutivas
  - Posição 262-267: 6 falhas consecutivas
  - Posição 286-292: 7 falhas consecutivas
  - Posição 317-322: 6 falhas consecutivas
  - Posição 342-346: 5 falhas consecutivas
  - Posição 352-356: 5 falhas consecutivas
  - Posição 358-362: 5 falhas consecutivas
  - Posição 383-387: 5 falhas consecutivas
  - Posição 412-416: 5 falhas consecutivas
  - Posição 418-422: 5 falhas consecutivas
  - Posição 424-428: 5 falhas consecutivas
  - Posição 456-463: 8 falhas consecutivas
  - Posição 502-507: 6 falhas consecutivas
  - Posição 509-513: 5 falhas consecutivas
  - Posição 536-541: 6 falhas consecutivas
  - Posição 543-547: 5 falhas consecutivas
  - Posição 564-623: 60 falhas consecutivas

### Correlação de Falha entre Modelos


**Pares de modelos que falharam juntos (ordenado por frequência):**
  - deepseek-ai/deepseek-v4-pro + llama-3.3-70b-versatile: 101 personas (78.91%)
  - deepseek-ai/deepseek-v4-pro + openai/gpt-oss-120b: 66 personas (51.56%)
  - llama-3.3-70b-versatile + openai/gpt-oss-120b: 60 personas (46.88%)
  - deepseek-ai/deepseek-v4-flash + deepseek-ai/deepseek-v4-pro: 57 personas (44.53%)
  - deepseek-ai/deepseek-v4-flash + llama-3.3-70b-versatile: 52 personas (40.62%)
  - deepseek-ai/deepseek-v4-flash + openai/gpt-oss-120b: 50 personas (39.06%)
  - command-r-08-2024 + deepseek-ai/deepseek-v4-pro: 19 personas (14.84%)
  - command-r-08-2024 + llama-3.3-70b-versatile: 18 personas (14.06%)
  - command-r-08-2024 + openai/gpt-oss-120b: 17 personas (13.28%)
  - command-r-08-2024 + deepseek-ai/deepseek-v4-flash: 11 personas (8.59%)

### Degradação de Latência ao Longo do Tempo

- **Q1 (primeiro 25%):** 27157ms média (67 chamadas)
- **Q2 (25-50%):** 21982ms média (68 chamadas)
- **Q3 (50-75%):** 24458ms média (68 chamadas)
- **Q4 (último 25%):** 20871ms média (68 chamadas)
- **Tendência global:** -23.1% de Q1 para Q4

### Latência por Modelo ao Longo do Tempo


**llama-3.3-70b-versatile** (13 chamadas OK):
  - Q1: 49070ms
  - Q4: 1615ms
  - Tendência: -96.7%

**openai/gpt-oss-120b** (62 chamadas OK):
  - Q1: 3497ms
  - Q4: 41066ms
  - Tendência: +1074.3%

**command-r-08-2024** (109 chamadas OK):
  - Q1: 10036ms
  - Q4: 7392ms
  - Tendência: -26.3%

**deepseek-ai/deepseek-v4-flash** (71 chamadas OK):
  - Q1: 62464ms
  - Q4: 27512ms
  - Tendência: -56.0%

**deepseek-ai/deepseek-v4-pro** (16 chamadas OK):
  - Q1: 9172ms
  - Q4: 73455ms
  - Tendência: +700.9%

---

## 4. Estatísticas do Sintetizador


### Distribuição de Decisões Finais

- **SKIP:** 20 (15.62%)
- **agendou:** 17 (13.28%)
- **clicou:** 18 (14.06%)
- **ignorou:** 2 (1.56%)
- **visualizou:** 71 (55.47%)

### Divergence Scores

- **Média:** 0.0723
- **Mediana:** 0.0000
- **Mínimo:** 0.0000
- **Máximo:** 1.0000
- **p50:** 0.0000
- **p90:** 0.3510
- **p99:** 0.6600

### Sínteses SKIP

- **Total:** 20 (15.62%)

---

## 5. Resumo Executivo


### Métricas Globais

- **Total de chamadas de modelo:** 640
- **Taxa de sucesso global:** 42.34%
- **Total de falhas:** 369
- **Modelo mais confiável:** command-r-08-2024 (85.16%)
- **Modelo mais rápido (p50, com 10+ chamadas OK):** llama-3.3-70b-versatile (3074ms)
- **Modelo menos confiável:** llama-3.3-70b-versatile (10.16%)

### ⚠️ Outage Detectado

- **Janela máxima de falhas consecutivas:** 60
- Isso indica um outage prolongado dos providers durante o experimento.