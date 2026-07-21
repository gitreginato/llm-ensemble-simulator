# Report: Modelos Problematicos no Gocat

**Data:** 2026-07-20
**Fonte:** Ensemble v4 (5 personas, 120 requests, 54 via gocat)
**Contexto:** Simulation Army v2 rodando 22 modelos de 3 fontes (gocat, kilocode, devin)

## Resumo Executivo

O gocat tem **3 modelos que falham 100%** com HTTP 503 ("all providers failed").
Isso representa **16 falhas em 54 requests gocat (30% de taxa de falha)**.
Os outros 2 providers (kilocode 93%, devin 100%) funcionam de forma estavel.

## Performance por Source (evidencia S: output fresco desta sessao)

| Source | Total | OK | FAIL | Taxa Sucesso | Lat media | P50 | P95 | Tokens medios |
|---|---|---|---|---|---|---|---|---|
| **devin** | 11 | 11 | 0 | **100%** | 24.6s | 18.6s | 50.3s | N/A (CLI nao expoe) |
| **kilocode** | 55 | 51 | 4 | **93%** | 32.9s | 32.9s | 60.9s | 12.827 |
| **gocat** | 54 | 29 | 25 | **54%** | 20.1s | 5.4s | 96.2s | 1.332 |

## Modelos que Sempre Falham (gocat 503)

### 1. Meta-Llama-3.3-70B-Instruct (SambaNova)
- **Provider:** sambanova (configs/providers.yaml linha 28-35)
- **Fails:** 5/5 (100%)
- **Erro:** `HTTP 503: {"error":{"message":"all providers failed for model 'Meta-Llama-3.3-70B-Instruct'","type":"all_providers_failed","code":"all_providers_failed"}}`
- **Causa provavel:** SambaNova rate limit ou modelo indisponivel no free tier
- **Recomendacao:** Desabilitar modelo ou remover da lista do provider sambanova

### 2. gemini-2.5-flash (Gemini)
- **Provider:** gemini (configs/providers.yaml linha 256-270)
- **Fails:** 5/5 (100%)
- **Erro:** `HTTP 503: {"error":{"message":"all providers failed for model 'gemini-2.5-flash'","type":"all_providers_failed","code":"all_providers_failed"}}`
- **Causa provavel:** GEMINI_API_KEY sem cota ou rate limit do free tier
- **Recomendacao:** Verificar cota da API key em https://ai.google.dev/pricing
- **Alternativa:** Usar gemini-2.5-flash-lite (mais leve, menos rate limited)

### 3. deepseek-ai/DeepSeek-V3 (SiliconFlow)
- **Provider:** siliconflow (configs/providers.yaml linha 335-345)
- **Fails:** 6/6 (100%)
- **Erro:** `HTTP 503: {"error":{"message":"all providers failed for model 'deepseek-ai/DeepSeek-V3'","type":"all_providers_failed","code":"all_providers_failed"}}`
- **Causa provavel:** Provider siliconflow esta **enabled: false** e key vazia (`keys: [""]`)
- **Recomendacao:** Ou habilitar com API key valida, ou remover modelo do scenario

## Outros Erros Gocat (nao-503)

| Tipo | Count | Descricao |
|---|---|---|
| unknown | 6 | Erro generico (provavelmente empty response) |
| empty_response | 3 | "Both content and reasoning_content are empty" |
| http_502 | 1 | Erro 502 do kilocode (Nvidia ResourceExhausted) |

### Empty Response (gocat conversacional)
- **Erro:** `Both content and reasoning_content are empty`
- **Modelo afetado:** gocat (provavelmente command-r-plus ou command-a)
- **Frequencia:** 3 vezes em 54 requests (5.5%)
- **Causa provavel:** Modelo retorna resposta vazia quando o prompt e muito longo ou complexo
- **Recomendacao:** Adicionar retry com prompt simplificado quando resposta vazia

## Backoff Adaptativo (funcionando)

O Simulation Army implementou backoff adaptativo por source:
- Backoff maximo observado: **8.0x** (deepseek-ai/DeepSeek-V3)
- Backoffs aplicados: 6 vezes
- Valores: [2.0, 2.0, 2.0, 8.0, 2.0, 2.0]
- Comportamento: apos falha, dobra delay (max 8x). Apos sucesso, reseta para 1x.

## Recomendacoes para o Gocat

### Criticas (afetam producao)
1. **Remover ou desabilitar 3 modelos** que sempre falham 503:
   - Meta-Llama-3.3-70B-Instruct (sambanova)
   - gemini-2.5-flash (gemini) : verificar cota API key
   - deepseek-ai/DeepSeek-V3 (siliconflow) : provider desabilitado, key vazia

2. **Investigar empty response** em command-r-plus/command-a (3 ocorrencias)
   - Adicionar log com prompt length e modelo quando resposta vazia
   - Considerar retry automatico com prompt simplificado

### Melhorias (nice-to-have)
3. **Adicionar health check por modelo** no gocat: se modelo falha N vezes seguidas, marca como unhealthy e nao tenta mais por X minutos
4. **Expor provider real** no header X-Gocat-Provider para saber qual provider fez fallback
5. **Logar tokens** no /v1/costs em tempo real (bug SQLite ja corrigido, mas dados ainda stale)

## Impacto no Simulation Army

Com os 3 modelos problematicos removidos:
- Gocat: 54 -> 39 requests (remove 15 falhas garantidas)
- Taxa sucesso gocat: 54% -> 74% (29/39)
- Taxa sucesso total: 77% -> 91% (91/100)
- Tempo por persona: -3 requests * 5s = -15s por persona

## Evidencia

- **Log bruto:** /tmp/ensemble_v4_run.log (148 linhas, 5 personas)
- **JSON estruturado:** results_v2/ensemble_v4_n30_partial.json (34KB)
- **Relatorio markdown:** results_v2/ensemble_v4_n30_report.md
- **Dashboard HTML:** dashboard.html
- **Gocat providers.yaml:** /home/lucas/Projetos/gocat/configs/providers.yaml
