# Limites de APIs e Plano de Rate Limiting

## Provedores disponiveis

| Provedor | Modelo testado | Limite | Observacao | Status atual |
|----------|---------------|--------|------------|--------------|
| Groq | meta-llama/llama-4-scout-17b-16e-instruct | 30k tokens/request, 30k TPM | **Intermitente**: erro 0 (connection) frequente mesmo respeitando 5s entre chamadas. Curls isolados funcionam, mas batches falham. | Instavel |
| NVIDIA | meta/llama-3.1-70b-instruct | ~40 RPM, quota esgota | 429 frequente apos uso | Indisponivel (quota) |
| Google | gemini-2.5-flash-lite / gemini-2.0-flash | 5 RPM free | 429 por quota/diaria | Indisponivel (quota) |
| OpenRouter | google/gemini-2.5-flash-lite | Key limit exceeded (sem credito) | Nao funciona sem credito | Indisponivel |
| Z.ai | GLM-4.7-Flash | 1 QPS, timeout frequente | Muito lento | Nao testado |

## Calculo de uso por chamada

Prompt medio: ~600-800 tokens
Resposta esperada: ~150-250 tokens
Total por chamada: ~750-1050 tokens

## Limites praticos

### Groq
- 30k TPM / ~1k tokens por chamada = ~30 chamadas/minuto maximo
- Recomendado: no maximo 10-12 chamadas/minuto para margem de seguranca
- Intervalo minimo entre chamadas: **5 segundos**
- Excecao: se houver 429, aplicar backoff exponencial ate 60s

### NVIDIA
- ~40 RPM = 1.5s entre chamadas
- Problema: quota diaria esgota rapido
- Usar apenas como fallback se Groq falhar

### Google
- 5 RPM = 12s entre chamadas
- Muito lento para volume, usar so em emergencia

## Plano de execucao responsavel

### Fase 1: Teste de conectividade (2-3 chamadas)
- 1 chamada Groq a cada 5s
- Verificar se retorna 200 e JSON valido
- Se Groq falhar, tentar NVIDIA com 2s de intervalo
- Se ambos falharem, parar e avisar usuario

### Fase 2: Simulacoes avancadas
- Total estimado: 6 cenarios x 30 agentes = 180 chamadas
- Plus 0 chamadas de word-of-mouth (regra local)
- Tempo estimado: 180 chamadas x 5s = 900s = 15 minutos
- Buffer para retries: +50% = ~23 minutos

### Fase 3: Reserva de quota
- Nao executar outras simulacoes simultaneas
- Monitorar rate limit a cada cenario
- Se atingir 429 3x seguidas, pausar e avisar usuario

## Configuracao do rate limiter

```python
MIN_DELAY_SECONDS = 5.0  # Groq safe margin
MAX_RETRIES = 5
BACKOFF_BASE = 2.0
BACKOFF_MAX = 60.0
```

## Regras

1. Nunca fazer chamadas em paralelo.
2. Sempre respeitar MIN_DELAY_SECONDS entre chamadas.
3. Em caso de 429, aguardar pelo menos 10s antes de retry.
4. Registrar todas as chamadas e respostas para auditoria.
5. Se qualquer provedor der 403/429 recorrente, parar imediatamente.
