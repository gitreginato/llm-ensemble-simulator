# Analise Consolidada FASE 1: Telemetria, Bugs e Plano de Correcao

**Data:** 2025-01-17
**Runs analisados:** N=4 (5 sources), N=8 fast (3 sources), N=128 fast (3 sources, caiu), N=128 alt (3 providers, final)
**Relatorios fonte:** analise_telemetria_n128.md, analise_codigo_bugs.md, analise_gocat_carga.md

---

## 1. Telemetria Quantificada

### 1.1 Cross-run: taxa de sucesso por source

| Run | Source | OK/Total | Taxa | Latencia avg |
|---|---|---|---|---|
| N=4 | gocat | 12/12 | 100% | 24.8s |
| N=4 | ollama | 8/8 | 100% | 20.0s |
| N=4 | cline | 6/8 | 75% | 23.3s |
| N=4 | kilocode | 7/8 | 88% | 41.7s |
| N=4 | devin | 5/8 | 62% | 25.0s |
| N=8 fast | gocat | 24/24 | 100% | 11.6s |
| N=8 fast | cline | 6/8 | 75% | 25.9s |
| N=8 fast | ollama | 15/16 | 94% | 22.2s |
| N=128 fast | gocat | 132/222 | 59% | - |
| N=128 alt | gocat | 271/640 | 42% | 23.6s |

**Padrao:** gocat HTTP cai de 100% (N=4) para 42% (N=128). Causa: rate limit + providers externos em outage.

### 1.2 N=128 alt: desempenho por modelo

| Modelo | OK/128 | Taxa | Latencia p50 | Latencia p90 | Falhas 503 | Falhas erro vazio |
|---|---|---|---|---|---|---|
| command-r-08-2024 (Cohere) | 109 | 85% | 5.1s | 25.6s | 19 | 0 |
| openai/gpt-oss-120b (Groq) | 62 | 48% | 3.6s | 64.3s | 35 | 31 |
| deepseek-v4-flash (NVIDIA) | 71 | 55% | 39.4s | 98.7s | 53 | 4 |
| deepseek-v4-pro (NVIDIA) | 16 | 12% | 11.7s | 91.3s | 83 | 29 |
| llama-3.3-70b (Groq) | 13 | 10% | 3.1s | 126.9s | 47 | 68 |

**Insight:** Cohere (85%) e o unico estavel. Groq e NVIDIA degradam severamente sob carga sustainada.

### 1.3 Outage windows (sequencias de falhas consecutivas)

| Modelo | Longest streak | Personas afetadas |
|---|---|---|
| deepseek-v4-pro | 102 consecutivas (persona 27-128) | 112/128 |
| llama-3.3-70b | 15 consecutivas (persona 114-128) | 115/128 |
| deepseek-v4-flash | 16 consecutivas (persona 75-90) | 57/128 |
| openai/gpt-oss-120b | 13 consecutivas (persona 113-125) | 66/128 |
| command-r-08-2024 | 19 consecutivas (persona 110-128) | 19/128 |

**Janela critica:** personas 109-128 (20 personas) = outage total de todos os modelos. 60 falhas consecutivas sem nenhuma resposta.

### 1.4 Correlacao de falhas entre modelos

| Par | Falharam juntos | % |
|---|---|---|
| deepseek-v4-pro + llama-3.3-70b | 101/128 | 79% |
| deepseek-v4-pro + gpt-oss-120b | 66/128 | 52% |
| llama-3.3-70b + gpt-oss-120b | 60/128 | 47% |
| deepseek-v4-flash + deepseek-v4-pro | 57/128 | 45% |

**Insight:** deepseek-v4-pro e llama-3.3-70b falham juntos em 79% das personas. Mesmo provider (NVIDIA/Groq) ou mesmo gocat backend.

### 1.5 Impacto no sintetizador

| Metrica | Valor |
|---|---|
| Sinteses OK | 108/128 (84%) |
| Sinteses SKIP (0 decisoes) | 20/128 (16%) |
| Conversao (agendaram) | 17/108 (15.7%) |
| Divergence score medio | 0.072 |
| Divergence score p90 | 0.351 |

**Distribuicao de decisoes por persona:**
- 0 decisoes: 11 personas (8.6%) = SKIP
- 1 decisao: 40 personas (31.3%)
- 2 decisoes: 22 personas (17.2%)
- 3 decisoes: 35 personas (27.3%)
- 4 decisoes: 18 personas (14.1%)
- 5 decisoes: 2 personas (1.6%)

**Correlacao num decisoes -> agendou:**
- 1 decisao: 15% agendou
- 2 decisoes: 14% agendou
- 3 decisoes: 11% agendou
- 4 decisoes: 22% agendou
- 5 decisoes: 0% agendou

### 1.6 Latencia ao longo do tempo (degradacao)

| Quartil | Personas | p50 | p90 | n chamadas OK |
|---|---|---|---|---|
| Q1 (1-29) | 29 | 7.7s | 63.3s | 107 |
| Q2 (30-58) | 29 | 5.5s | 64.5s | 74 |
| Q3 (59-87) | 29 | 8.0s | 52.3s | 42 |
| Q4 (88-117) | 30 | 12.9s | 63.9s | 43 |

**Tendencia:** p50 cresce 68% do Q1 para Q4 (7.7s -> 12.9s). Numero de chamadas OK cai 60% (107 -> 43).

### 1.7 Tipos de falha consolidados (cross-run)

| Tipo | N=4 | N=8 | N=128 fast | N=128 alt | Causa raiz |
|---|---|---|---|---|---|
| timeout | 5 | 0 | 0 | 0 | devin 90s, cline 120s |
| validation | 1 | 0 | 0 | 0 | schema faltando campo |
| content_vazio | 0 | 3 | 5 | 0 | reasoning model sem content |
| provider_503 | 0 | 0 | 84 | 237 | provider externo em outage |
| erro_vazio | 0 | 0 | 0 | 132 | ensemble nao capturando erro |
| json_parse | 0 | 0 | 1 | 0 | JSON truncado |

---

## 2. Bugs Identificados e Priorizados

### GOCAT (Go) - 3 bugs

| # | Severidade | Bug | Arquivo | Impacto |
|---|---|---|---|---|
| G1 | CRITICO | Circuit breaker desconectado do routing | chat.go:310 | Provider morto continua sendo tentado |
| G2 | IMPORTANTE | max_retries hardcoded (2), ignora config | client.go:134 | Config max_retries:3 sem efeito |
| G3 | CONFIG | timeout 90s, threshold 10 | providers.yaml | Timeout longo, circuito abre tarde |

### ENSEMBLE (Python) - 6 bugs

| # | Severidade | Bug | Arquivo | Impacto |
|---|---|---|---|---|
| E1 | CRITICO | Sem circuit breaker por source | ensemble.py:363 | 102 falhas consecutivas sem SKIP |
| E2 | ALTO | Backoff sem decay temporal | ensemble.py:345 | Provider morto penalizado indefinidamente |
| E3 | ALTO | Sintetizador sem fallback | ensemble.py:410 | Persona descartada com decisoes validas |
| E4 | ALTO | Sintetizador content vazio sem fallback | ensemble.py:178 | Reasoning models descartados |
| E5 | MEDIO | Timeouts hardcoded | devin_adapter.py:22, cline_adapter.py:80 | Nao configuravel |
| E6 | MEDIO | JSON parsing fragil | baseline.py:239 | JSON aninhado/truncado rejeitado |

---

## 3. Plano de Correcao (executando agora)

### Fase 1: Gocat (Go)
- G1: Conectar SetHealthy apos RecordFailure/RecordSuccess
- G2: Usar config max_retries em vez de hardcoded 2
- G3: Reduzir timeout 90s->30s, threshold 10->5, reset 60s->120s

### Fase 2: Ensemble (Python)
- E1: Circuit breaker por source (5 falhas = SKIP 300s)
- E2: Backoff com decay temporal (5min sem falha = reset)
- E3: Fallback do sintetizador (agregacao simples)
- E4: Fallback de content vazio (campos alternativos + agregacao)
- E5: Timeouts configuraveis via ExecutionConfig
- E6: JSON parsing com regex para JSON aninhado

### Fase 3: Validacao
- Rodar 316 testes existentes
- Rodar N=32 com 5 sources para validar
- Comparar telemetria antes/depois

---

## 4. Metricas-alvo pos-correcao

| Metrica | Antes | Alvo |
|---|---|---|
| Taxa sucesso chamadas | 42% | >70% |
| Sinteses SKIP | 16% | <5% |
| Falhas erro_vazio | 132 | 0 |
| Longest fail streak | 102 | <10 |
| Latencia p50 Q4 | 12.9s | <10s |
| Tempo total N=128 | ~2h | <1.5h |
