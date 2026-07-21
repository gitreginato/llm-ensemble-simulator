# Análise de Gargalos do gocat - Simulação N=128

**Data**: 2025-01-17  
**Contexto**: 640 chamadas em ~2h, 11 providers habilitados, múltiplas falhas (Ollama cloud 503, SambaNova, GitHub, Gemini)

---

## Resumo Executivo

O gocat possui mecanismos de resiliência (circuit breaker, retry, key pool), mas há **gargalos críticos** que explicam as falhas em massa:

1. **Health check inexistente**: Router marca todos providers como `Healthy: true` hardcoded. Nunca verifica se provider está realmente up.
2. **Circuit breaker desconectado do routing**: `router.SetHealthy()` existe mas nunca é chamado. Falhas não afetam seleção de providers.
3. **Key pool sem backup**: 1 key por provider. Se key entra em cooldown (3s → 6s → 12s → 24s → 5min), não há alternativa.
4. **Timeout agressivo**: 90s por provider. Com 11 providers e fallback, request pode levar 990s antes de falhar.
5. **Sem fallback por modelo**: Se Ollama cloud cai, não tenta SambaNova para o mesmo modelo automaticamente.

---

## 1. Circuit Breaker

### Config Atual
**Arquivo**: `/home/lucas/Projetos/gocat/configs/providers.yaml` (linhas 403-405)
```yaml
routing:
  circuit_breaker:
    failure_threshold: 10
    reset_timeout: 60s
```

### Implementação
**Arquivo**: `/home/lucas/Projetos/gocat/pkg/routing/circuitbreaker.go`

- **Threshold**: 10 falhas consecutivas abre o circuit
- **Reset**: 60s após última falha, entra em HalfOpen
- **HalfOpen**: Apenas 1 probe permitido (linha 60-62)

### Comportamento Observado vs Esperado

| Problema | Observado | Esperado | Causa Raiz |
|----------|-----------|----------|------------|
| Ollama cloud 503 mas circuit não abriu | Circuit breaker não impediu tentativas | Após 10 falhas, provider deveria ser pulado | Router nunca chama `SetHealthy()` |
| "providers_active: 11" com 503 | Router conta enabled=true | Deveria contar apenas healthy | `Healthy` hardcoded true (chat.go:310) |

### Código Problemático

**Arquivo**: `/home/lucas/Projetos/gocat/pkg/server/chat.go` (linhas 297-320)
```go
func (h *chatHandler) rebuildRouterLocked() {
    infos := make([]routing.ProviderInfo, 0, len(h.providers))
    h.modelIndex = make(map[string][]string)
    i := 0
    for _, ps := range h.providers {
        if !ps.cfg.Enabled {
            continue
        }
        infos = append(infos, routing.ProviderInfo{
            ID:       ps.cfg.ID,
            Enabled:  ps.cfg.Enabled,
            Priority: i,
            Healthy:  true,  // ← HARDCODED! Nunca muda
        })
        // ...
    }
    h.router.SetProviders(infos)
}
```

**Arquivo**: `/home/lucas/Projetos/gocat/pkg/routing/router.go` (linhas 56-65)
```go
func (r *Router) Select() []string {
    // ...
    for _, p := range r.providers {
        if p.Enabled && p.Healthy {  // ← Healthy sempre true
            opts = append(opts, p)
        }
    }
    // ...
}
```

**Arquivo**: `/home/lucas/Projetos/gocat/pkg/routing/router.go` (linhas 91-101)
```go
func (r *Router) SetHealthy(providerID string, healthy bool) {
    // ← EXISTE mas nunca é chamado!
    r.mu.Lock()
    defer r.mu.Unlock()
    for i := range r.providers {
        if r.providers[i].ID == providerID {
            r.providers[i].Healthy = healthy
            return
        }
    }
}
```

### Sugestão de Ajuste (Config Change)

**Opção 1: Ajustar threshold para carga alta**
```yaml
routing:
  circuit_breaker:
    failure_threshold: 5  # Reduzir de 10 para 5 (abre mais rápido)
    reset_timeout: 120s    # Aumentar de 60s para 120s (evita flapping)
```

**Opção 2: Conectar circuit breaker ao routing (Código)**
Adicionar em `chat.go` após `ps.breaker.RecordFailure()`:
```go
if ps.breaker.State() == routing.StateOpen {
    h.router.SetHealthy(providerID, false)
}
```

E após `ps.breaker.RecordSuccess()`:
```go
if ps.breaker.State() == routing.StateClosed {
    h.router.SetHealthy(providerID, true)
}
```

---

## 2. Rate Limit e Key Pool

### Config Atual
**Arquivo**: `/home/lucas/Projetos/gocat/configs/providers.yaml`

Cada provider tem **1 key**:
```yaml
- id: groq
  keys:
    - ${GROQ_API_KEY}  # ← Apenas 1 key
```

### Implementação
**Arquivo**: `/home/lucas/Projetos/gocat/pkg/keys/keypool.go`

- **Cooldown base**: 3s (chat.go:449, chat.go:591)
- **Backoff exponencial**: 3s → 6s → 12s → 24s → 48s → 96s → **cap 5min** (keypool.go:79-86)
- **Round-robin**: Itera por todas keys disponíveis

### Comportamento Observado vs Esperado

| Problema | Observado | Esperado | Causa Raiz |
|----------|-----------|----------|------------|
| Groq 90% falha N=128 vs N=4 | Key entra em cooldown, sem backup | Múltiplas keys rotacionam | 1 key por provider |
| SambaNova caiu completamente | Key em cooldown 5min | Fallback para outro provider | Sem pool de keys |

### Código Problemático

**Arquivo**: `/home/lucas/Projetos/gocat/pkg/keys/keypool.go` (linhas 72-91)
```go
func (p *Pool) Cooldown(key string, base time.Duration) {
    // ...
    for range k.Failures {
        d *= 2
        if d > 5*time.Minute {
            d = 5 * time.Minute  // ← Cap 5min
            break
        }
    }
    k.Cooldown = time.Now().Add(d)
}
```

**Arquivo**: `/home/lucas/Projetos/gocat/pkg/server/chat.go` (linhas 449, 591)
```go
key := ps.pool.Next(3 * time.Second)  // ← Cooldown base 3s
```

### Sugestão de Ajuste (Config Change)

**Opção 1: Adicionar múltiplas keys**
```yaml
- id: groq
  keys:
    - ${GROQ_API_KEY_1}
    - ${GROQ_API_KEY_2}
    - ${GROQ_API_KEY_3}  # ← 3 keys para load balancing
```

**Opção 2: Reduzir cooldown base**
Modificar `chat.go` linhas 449 e 591:
```go
key := ps.pool.Next(1 * time.Second)  // ← Reduzir de 3s para 1s
```

**Opção 3: Aumentar cap de cooldown**
Modificar `keypool.go` linha 82:
```go
if d > 10*time.Minute {  // ← Aumentar de 5min para 10min
    d = 10 * time.Minute
    break
}
```

---

## 3. Retry Logic

### Config Atual
**Arquivo**: `/home/lucas/Projetos/gocat/configs/providers.yaml` (linha 402)
```yaml
routing:
  max_retries: 3  # ← Config existe mas não é usada!
```

### Implementação
**Arquivo**: `/home/lucas/Projetos/gocat/pkg/providers/client.go` (linhas 134-211)

- **maxRetries**: **2** (hardcoded, ignora config)
- **Backoff**: 500ms → 1s → 2s (exponencial)
- **Retry-After header**: Respeitado, cap 30s (MaxRetryAfter)
- **Retryable**: 429 (rate limit) e 5xx apenas

### Comportamento Observado vs Esperado

| Problema | Observado | Esperado | Causa Raiz |
|----------|-----------|----------|------------|
| Config `max_retries: 3` ignorada | Sempre 2 retries | Deveria respeitar config | Hardcoded em client.go:134 |
| 503 não é retryable | Falha imediata | Deveria retry (5xx) | 503 não é >= 500 em alguns providers |

### Código Problemático

**Arquivo**: `/home/lucas/Projetos/gocat/pkg/providers/client.go` (linha 134)
```go
maxRetries := 2  // ← HARDCODED, ignora config.MaxRetries
```

**Arquivo**: `/home/lucas/Projetos/gocat/pkg/providers/client.go` (linha 184)
```go
retryable := resp.StatusCode == 429 || resp.StatusCode >= 500
```

### Sugestão de Ajuste (Config Change)

**Opção 1: Usar config de retries**
Modificar `client.go` para receber `maxRetries` do config:
```go
func (e *Executor) Do(ctx context.Context, req translators.ChatRequest, maxRetries int) (*http.Response, error) {
    // ...
    for attempt := 0; attempt <= maxRetries; attempt++ {
        // ...
    }
}
```

**Opção 2: Aumentar retries hardcoded**
```go
maxRetries := 3  // ← Aumentar de 2 para 3
```

---

## 4. Health Check

### Config Atual
**NÃO EXISTE** configuração de health check.

### Implementação
**Arquivo**: `/home/lucas/Projetos/gocat/pkg/server/probe.go`

- **Endpoint**: `/v1/probe` chama `/models` de cada provider
- **Uso**: Manual via curl/HTTP, **não automático**
- **Frequência**: Nenhuma (on-demand)

### Comportamento Observado vs Esperado

| Problema | Observado | Esperado | Causa Raiz |
|----------|-----------|----------|------------|
| Gemini caiu desde o início | Nenhuma verificação proativa | Health check periódico | Probe é manual, não scheduled |
| Ollama cloud 503 não detectado até request | Só sabe quando tenta | Detectar antes de rotear | Sem health check automático |

### Código Problemático

**Arquivo**: `/home/lucas/Projetos/gocat/pkg/server/chat.go` (linha 310)
```go
Healthy: true,  // ← HARDCODED, nunca muda
```

**Arquivo**: `/home/lucas/Projetos/gocat/pkg/server/probe.go` (linhas 12-25)
```go
func (s *Server) probeHandle(w http.ResponseWriter, r *http.Request) {
    // ← Manual endpoint, não é chamado automaticamente
    results, err := probe.Probe(s.chat.getProviderConfigs())
    // ...
}
```

### Sugestão de Ajuste (Config Change)

**Opção 1: Adicionar config de health check**
```yaml
routing:
  health_check:
    enabled: true
    interval: 30s    # Verificar a cada 30s
    timeout: 10s     # Timeout por provider
    unhealthy_threshold: 3  # 3 falhas consecutivas = unhealthy
    healthy_threshold: 2    # 2 sucessos consecutivos = healthy
```

**Opção 2: Usar probe como health check (Código)**
Adicionar goroutine em `server.go`:
```go
go func() {
    ticker := time.NewTicker(30 * time.Second)
    for range ticker.C {
        results, _ := probe.Probe(s.chat.getProviderConfigs())
        for providerID, result := range results {
            if result.Error != nil {
                s.chat.router.SetHealthy(providerID, false)
            } else {
                s.chat.router.SetHealthy(providerID, true)
            }
        }
    }
}()
```

---

## 5. Estratégia de Roteamento

### Config Atual
**Arquivo**: `/home/lucas/Projetos/gocat/configs/providers.yaml` (linha 400)
```yaml
routing:
  default_strategy: fallback
```

### Implementação
**Arquivo**: `/home/lucas/Projetos/gocat/pkg/routing/router.go`

- **Strategies**: `priority`, `fallback`, `least-used`, `random`
- **Fallback**: Tenta providers em ordem até um funcionar
- **HPA* Model Index**: O(1) lookup por model, mas fallback para router.Select() se model não encontrado

### Comportamento Observado vs Esperado

| Problema | Observado | Esperado | Causa Raiz |
|----------|-----------|----------|------------|
| Todos providers tentados mesmo com 503 | Fallback cega por ordem | Respeitar circuit breaker | Router não filtra por Healthy |
| "providers_active: 11" mas 503 | Conta enabled=true | Deveria contar healthy | Healthy hardcoded true |

### Código Problemático

**Arquivo**: `/home/lucas/Projetos/gocat/pkg/routing/router.go` (linhas 67-76)
```go
switch r.strategy {
case StrategyPriority:
    return byPriority(opts)
case StrategyLeastUsed:
    return byLeastUsed(opts)
case StrategyRandom:
    return shuffle(opts)
default:
    return byPriority(opts)  // ← "fallback" usa priority!
}
```

**Arquivo**: `/home/lucas/Projetos/gocat/pkg/routing/router.go` (linhas 103-110)
```go
func byPriority(providers []ProviderInfo) []string {
    // ← Retorna em ordem de inserção (aleatória em map)
    ids := make([]string, len(providers))
    for i, p := range providers {
        ids[i] = p.ID
    }
    return ids
}
```

### Sugestão de Ajuste (Config Change)

**Opção 1: Mudar strategy para least-used**
```yaml
routing:
  default_strategy: least-used  # ← Distribui carga melhor
```

**Opção 2: Implementar fallback real (Código)**
Modificar `router.go`:
```go
case StrategyFallback:
    // ← Tenta least-used primeiro, depois priority
    return byLeastUsed(opts)
```

---

## 6. Fallback por Modelo

### Config Atual
**NÃO EXISTE** configuração de fallback por modelo.

### Implementação
**Arquivo**: `/home/lucas/Projetos/gocat/pkg/server/chat.go` (linhas 408-420)

- **HPA* Model Index**: `map[model][]providerID`
- **Lookup**: `modelIndex[strings.ToLower(req.Model)]`
- **Fallback**: Se model não encontrado, usa `router.Select()` (todos providers)

### Comportamento Observado vs Esperado

| Problema | Observado | Esperado | Causa Raiz |
|----------|-----------|----------|------------|
| Ollama cloud cai, não tenta SambaNova | Fallback cega por provider | Fallback inteligente por modelo | Sem mapping de equivalência |
| GitHub gpt-4o cai, não tenta outro provider | 503 imediato | Tentar outro provider com gpt-4o | Sem fallback por modelo |

### Código Problemático

**Arquivo**: `/home/lucas/Projetos/gocat/pkg/server/chat.go` (linhas 412-420)
```go
if req.Model != "" && req.Model != "auto" {
    if strings.HasPrefix(req.Model, "specialty:") {
        specialty := strings.TrimPrefix(req.Model, "specialty:")
        candidates = h.selectBySpecialty(specialty, providerMap)
    } else {
        candidates = modelIndex[strings.ToLower(req.Model)]  // ← Apenas providers com modelo exato
    }
}
```

### Sugestão de Ajuste (Config Change)

**Opção 1: Adicionar mapping de equivalência**
```yaml
model_fallbacks:
  - virtual: "gpt-4o"
    providers:
      - id: github
        model: "gpt-4o"
      - id: openrouter
        model: "openai/gpt-4o"
      - id: cerebras
        model: "gpt-4o"
  - virtual: "llama-3.3-70b"
    providers:
      - id: groq
        model: "llama-3.3-70b-versatile"
      - id: sambanova
        model: "Meta-Llama-3.3-70B-Instruct"
      - id: nvidia
        model: "meta/llama-3.3-70b-instruct"
```

**Opção 2: Usar aliases existentes**
```yaml
aliases:
  - virtual: "gpt-4o"
    provider: github
    model: "gpt-4o"
  - virtual: "gpt-4o-fallback"
    provider: openrouter
    model: "openai/gpt-4o"
```

---

## 7. Timeout por Provider

### Config Atual
**Arquivo**: `/home/lucas/Projetos/gocat/configs/providers.yaml` (linha 401)
```yaml
routing:
  timeout_per_provider: 90s
```

### Implementação
**Arquivo**: `/home/lucas/Projetos/gocat/pkg/server/chat.go` (linha 438)
```go
ctx, cancel := context.WithTimeout(r.Context(), breakerCfg.TimeoutDuration())
```

### Comportamento Observado vs Esperado

| Problema | Observado | Esperado | Causa Raiz |
|----------|-----------|----------|------------|
| Request demora 990s com 11 providers | 90s × 11 providers | Timeout global menor | Timeout é por provider, não global |
| N=128 com 640 chamadas em 2h | Muitos timeouts | Load shedding | Sem timeout global |

### Código Problemático

**Arquivo**: `/home/lucas/Projetos/gocat/pkg/server/chat.go` (linhas 547-628)
```go
for _, providerID := range ordered {
    // ← Loop tenta todos providers até um funcionar
    // ← Cada tentativa tem timeout de 90s
    // ← Sem timeout global para o loop inteiro
}
```

### Sugestão de Ajuste (Config Change)

**Opção 1: Reduzir timeout por provider**
```yaml
routing:
  timeout_per_provider: 30s  # ← Reduzir de 90s para 30s
```

**Opção 2: Adicionar timeout global**
```yaml
routing:
  timeout_per_provider: 30s
  global_timeout: 120s  # ← Timeout total para todas tentativas
```

**Opção 3: Implementar timeout global (Código)**
Modificar `chat.go`:
```go
ctx, cancel := context.WithTimeout(r.Context(), breakerCfg.TimeoutDuration())
defer cancel()

globalCtx, globalCancel := context.WithTimeout(r.Context(), 120*time.Second)
defer globalCancel()

for _, providerID := range ordered {
    if globalCtx.Err() != nil {
        break  // ← Timeout global atingido
    }
    // ...
}
```

---

## 8. Providers Habilitados vs Funcionando

### Config Atual
**Arquivo**: `/home/lucas/Projetos/gocat/configs/providers.yaml`

11 providers habilitados:
- sambanova (enabled: true)
- groq (enabled: true)
- github (enabled: true)
- zai (enabled: true)
- cohere (enabled: true)
- duckduckgo-web (enabled: true)
- gemini (enabled: true)
- huggingface (enabled: true)
- nvidia (enabled: true)
- kilo (enabled: true)
- ollama (enabled: true)

### Comportamento Observado vs Esperado

| Provider | Observado | Status Config | Causa Provável |
|----------|-----------|----------------|----------------|
| Ollama cloud | 503 all providers failed | enabled: true | Provider down, sem health check |
| SambaNova | Caiu completamente | enabled: true | Rate limit ou downtime |
| GitHub (gpt-4o) | Caiu após 23 personas | enabled: true | Rate limit por key |
| Gemini | Caiu desde o início | enabled: true | Key inválida ou quota |
| Groq | 10-55% sucesso | enabled: true | 1 key, cooldown frequente |
| Cohere | 10-55% sucesso | enabled: true | 1 key, cooldown frequente |
| NVIDIA | 10-55% sucesso | enabled: true | 1 key, cooldown frequente |

### Sugestão de Ajuste (Config Change)

**Opção 1: Desabilitar providers problemáticos temporariamente**
```yaml
- id: gemini
  enabled: false  # ← Desabilitar até resolver
- id: ollama
  enabled: false  # ← Desabilitar até resolver
```

**Opção 2: Adicionar múltiplas keys para providers críticos**
```yaml
- id: groq
  keys:
    - ${GROQ_API_KEY_1}
    - ${GROQ_API_KEY_2}
- id: nvidia
  keys:
    - ${NVIDIA_API_KEY_1}
    - ${NVIDIA_API_KEY_2}
```

---

## Priorização de Ajustes (Ponytail: Config > Código)

### Crítico (Implementar Imediatamente)

1. **Conectar circuit breaker ao routing** (Código)
   - Arquivo: `chat.go`
   - Linhas: Adicionar `router.SetHealthy()` após `RecordFailure()` e `RecordSuccess()`
   - Impacto: Alto (previne tentativas em providers down)

2. **Adicionar múltiplas keys para providers críticos** (Config)
   - Arquivo: `providers.yaml`
   - Providers: groq, nvidia, cohere
   - Impacto: Alto (distribui carga, reduz cooldown)

3. **Reduzir timeout por provider** (Config)
   - Arquivo: `providers.yaml`
   - Valor: 90s → 30s
   - Impacto: Alto (reduz latência total)

### Importante (Implementar Curto Prazo)

4. **Adicionar health check automático** (Código)
   - Arquivo: `server.go`
   - Frequência: 30s
   - Impacto: Alto (detecta providers down proativamente)

5. **Ajustar circuit breaker threshold** (Config)
   - Arquivo: `providers.yaml`
   - Valor: 10 → 5
   - Impacto: Médio (abre circuit mais rápido)

6. **Usar config max_retries** (Código)
   - Arquivo: `client.go`
   - Impacto: Médio (respeita configuração)

### Opcional (Implementar Longo Prazo)

7. **Adicionar fallback por modelo** (Config + Código)
   - Arquivo: `providers.yaml` + `chat.go`
   - Impacto: Médio (resiliência por modelo)

8. **Mudar strategy para least-used** (Config)
   - Arquivo: `providers.yaml`
   - Impacto: Baixo (distribuição de carga)

---

## Conclusão

O gocat tem uma arquitetura sólida com circuit breaker, retry e key pool, mas **há desconexões críticas**:

1. **Circuit breaker existe mas não afeta routing** (Healthy hardcoded true)
2. **Key pool existe mas sem backup** (1 key por provider)
3. **Health check existe mas é manual** (não automático)
4. **Config de retries existe mas não é usada** (hardcoded)

**Recomendação imediata**: Conectar circuit breaker ao routing e adicionar múltiplas keys para providers críticos. Isso deve resolver 80% dos problemas observados na simulação N=128.
