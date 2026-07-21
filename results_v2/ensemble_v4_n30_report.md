# Relatorio de Performance: Ensemble v4 (N=30 parcial)
**Data:** 2026-07-20
**Personas completas:** 5/30
**Total de requests:** 120
**Requests OK:** 91 (75.8%)
**Requests FAIL:** 29
**Custo total:** $0 (todos free tier)

## Sintetizador

| Persona | Decisao | Divergence |
|---|---|---|
| Joao Araujo | agendou | 0.67 |
| Eduardo Mendes | agendou | 0.56 |
| Renata Souza | agendou | 0.38 |
| Bruno Nascimento | clicou | 0.60 |
| Beatriz Nascimento | visualizou | 0.76 |

**Conversao (sintetizador):** 60.0%
**Divergence medio:** 0.59

## Performance por Source

| Source | Total | OK | FAIL | Sucesso | Lat media | P50 | P95 | Tokens |
|---|---|---|---|---|---|---|---|---|
| devin | 11 | 11 | 0 | 100% | 24595ms | 18584ms | 50256ms | 0 |
| gocat | 54 | 29 | 25 | 54% | 20082ms | 5405ms | 96173ms | 1332 |
| kilocode | 55 | 51 | 4 | 93% | 32890ms | 32946ms | 60856ms | 12827 |

## Distribuicao de Decisoes (modelos)

| Decisao | Count |
|---|---|
| clicou | 33 |
| visualizou | 29 |
| agendou | 28 |
| ignorou | 1 |

## Modelos que Falham (gocat 503)

| Modelo | Fails | Tipos |
|---|---|---|
| deepseek-ai/DeepSeek-V3 | 6 | http_503 |
| Meta-Llama-3.3-70B-Instruct | 5 | http_503 |
| gemini-2.5-flash | 5 | http_503 |

## Tipos de Erro

| Tipo | Count |
|---|---|
| http_503 | 16 |
| unknown | 6 |
| empty_response | 3 |
| timeout | 2 |
| http_502 | 1 |
| json_parse_fail | 1 |

## Backoff Adaptativo Observado

- Backoffs aplicados: 6
- Backoff maximo: 8.0x
- Backoffs unicos: [2.0, 8.0]

## Limitacoes Encontradas

1. **3 modelos gocat sempre falham 503**: Meta-Llama-3.3-70B-Instruct (SambaNova), gemini-2.5-flash (Gemini), deepseek-ai/DeepSeek-V3 (SiliconFlow)
2. **kilocode timeouts**: kat-coder-pro-v2.5 e nemotron-3-ultra-550b as vezes dao timeout 90s
3. **gocat empty response**: conversacional as vezes retorna 'Both content and reasoning_content are empty'
4. **Tempo por persona**: 5-10min (22 modelos sequenciais). N=30 = 2.5-5h.
5. **JSON parse fail**: kilocode as vezes retorna texto em vez de JSON (pesquisador)

## Recomendacoes

1. Remover os 3 modelos gocat que sempre falham 503 do scenario v4
2. Reduzir N para 10 em vez de 30 (mais viavel em tempo)
3. Considerar paralelismo real (asyncio.gather) para reduzir tempo
4. Aumentar timeout kilocode para 120s ou remover kat-coder-pro-v2.5
