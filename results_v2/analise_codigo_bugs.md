# Relatório de Análise de Bugs - Simulation Army v2

**Data:** 2025-01-XX  
**Arquivos analisados:** ensemble.py, baseline.py, cline_adapter.py, ollama_adapter.py, kilocode_adapter.py, devin_adapter.py, schema.py, config.py  
**Severidade:** CRÍTICO = sistema quebrado, ALTO = degradação significativa, MÉDIO = workaround possível, BAIXO = inconveniente

---

## BUG #1: Backoff por source escala até 8x sem mecanismo de recovery temporal

**Arquivo:** `ensemble.py`  
**Linhas:** 345, 367-369, 389, 400

**Código:**
```python
# Linha 345
source_backoff: dict[str, float] = {}

# Linhas 367-369
adaptive_delay = base_delay * source_backoff.get(source, 1.0)
if adaptive_delay > base_delay:
    await asyncio.sleep(adaptive_delay - base_delay)

# Linha 389 (reset em sucesso)
source_backoff[source] = 1.0

# Linha 400 (aumento em falha)
source_backoff[source] = min(source_backoff.get(source, 1.0) * 2.0, 8.0)
```

**Causa Raiz:**
- O backoff reseta para 1.0 apenas em sucesso (linha 389)
- Se um source está consistentemente falhando (ex: provider morto), ele nunca atinge sucesso para resetar
- Não há decay temporal (ex: reduzir backoff após X segundos sem tentativas)
- Não há limite de tentativas consecutivas antes de marcar source como "morto"

**Severidade:** ALTO  
**Impacto:** Provider com problemas intermitentes fica penalizado indefinidamente, reduzindo throughput do ensemble

**Sugestão de Fix (ponytail):**
```python
# Adicionar timestamp da última falha e decay temporal
source_backoff: dict[str, float] = {}
source_last_fail: dict[str, float] = {}  # timestamp monotonic
SOURCE_BACKOFF_DECAY_SECONDS = 300  # 5 minutos sem falha = reset

# No loop de processamento (após linha 363):
now = time.monotonic()
last_fail = source_last_fail.get(source, 0)
if now - last_fail > SOURCE_BACKOFF_DECAY_SECONDS:
    source_backoff[source] = 1.0  # decay temporal

# Na falha (linha 400):
source_backoff[source] = min(source_backoff.get(source, 1.0) * 2.0, 8.0)
source_last_fail[source] = time.monotonic()
```

---

## BUG #2: Sintetizador lança erro sem tentar fallback quando reasoning_content está vazio

**Arquivo:** `ensemble.py`  
**Linhas:** 178-183

**Código:**
```python
msg = data["choices"][0].get("message", {})
content = msg.get("content") or ""
if not content and msg.get("reasoning_content"):
    content = msg["reasoning_content"]
if not content:
    raise ValueError("synthesizer: content and reasoning_content empty")
```

**Causa Raiz:**
- Modelos de raciocínio (gpt-oss:120b, GLM, Qwen) podem colocar conteúdo em campos não previstos
- Não há tentativa de extrair JSON de campos alternativos (ex: `text`, `output`)
- Não há fallback para usar decisão mais conservadora das 3 decisões quando sintetizador falha

**Severidade:** ALTO  
**Impacto:** Persona inteira é descartada quando sintetizador falha, mesmo com 3 decisões válidas

**Sugestão de Fix (ponytail):**
```python
# Adicionar fallback para campos alternativos
msg = data["choices"][0].get("message", {})
content = msg.get("content") or ""
if not content:
    content = msg.get("reasoning_content") or ""
if not content:
    content = msg.get("text") or ""
if not content:
    # Fallback: usar decisão mais conservadora das decisões
    rank = {"ignorou": 0, "visualizou": 1, "clicou": 2, "agendou": 3}
    decisao_final = min((d.decisao for d in decisoes), key=lambda x: rank.get(x, 0))
    return DecisaoAggregada(
        decisao_final=decisao_final,
        wtp_medio=sum(d.wtp for d in decisoes) / len(decisoes),
        sentimento_medio=sum(d.sentimento for d in decisoes) / len(decisoes),
        objecoes_consolidadas=list({o for d in decisoes for o in d.objecoes}),
        divergence_score=divergence_score_from_decisoes(decisoes),
        concordancia=[{"modelo_a": p.modelo_a, "modelo_b": p.modelo_b, "concordam": p.concordam} 
                      for p in _compute_concordancia(decisoes)],
        confianca_agregada=sum(d.confianca for d in decisoes) / len(decisoes),
        raciocinio_sintese="Sintese automatica (sintetizador falhou)"
    )
```

**Mesmo problema em:**
- `baseline.py` linhas 344-349
- `ollama_adapter.py` linhas 77-82

---

## BUG #3: Timeout hardcoded no devin_adapter (90s)

**Arquivo:** `devin_adapter.py`  
**Linhas:** 22, 40

**Código:**
```python
async def call_devin(
    model: str,
    user_prompt: str,
    timeout: int = 90,  # <-- HARDCODED
) -> tuple[DecisaoPersona, dict[str, Any]]:
    ...
    stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
```

**Causa Raiz:**
- Timeout não é configurável via config.yaml
- Modelo swe-1-7 pode precisar de mais tempo para processar prompts complexos
- Não há retry com timeout maior após primeiro timeout

**Severidade:** MÉDIO  
**Impacto:** Modelos mais lentos sempre falham, mesmo que poderiam responder com mais tempo

**Sugestão de Fix (ponytail):**
```python
# 1. Adicionar campo em config.py
class ExecutionConfig(BaseModel):
    ...
    devin_timeout_seconds: int = Field(90, ge=10, le=600)
    cline_timeout_seconds: int = Field(120, ge=10, le=600)
    kilocode_timeout_seconds: int = Field(90, ge=10, le=600)

# 2. Passar timeout do config para adapters
# No ensemble.py, chamar:
d, meta = await call_devin(model_name, user_prompt, timeout=cfg.execution.devin_timeout_seconds)
```

---

## BUG #4: Timeout hardcoded no cline_adapter (120s)

**Arquivo:** `cline_adapter.py`  
**Linhas:** 80, 120

**Código:**
```python
async def call_cline(
    ...
    timeout: int = 120,  # <-- HARDCODED
) -> tuple[DecisaoPersona, dict[str, Any]]:
    ...
    stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
```

**Causa Raiz:** Mesmo do BUG #3  
**Severidade:** MÉDIO  
**Sugestão de Fix:** Mesmo do BUG #3 (usar `cfg.execution.cline_timeout_seconds`)

---

## BUG #5: JSON parsing falha com JSON truncado ou texto antes/depois

**Arquivo:** `baseline.py`  
**Linhas:** 239-271

**Código:**
```python
start = text.find("{")
end = text.rfind("}")
if start == -1 or end == -1 or end < start:
    raise ValueError(f"JSON nao encontrado em: {content[:200]}")
json_str = text[start : end + 1]
```

**Causa Raiz:**
- Se houver múltiplos `{` e `}` no texto (ex: em raciocínio), `find/rfind` pode pegar o par errado
- O fallback regex (linha 262) usa pattern `["\[]?([^",\]}}]+)` que não captura valores com espaços ou vírgulas
- Não há tentativa de limpar caracteres de escape antes do parse

**Severidade:** MÉDIO  
**Impacto:** Respostas válidas com texto extra são rejeitadas

**Sugestão de Fix (ponytail):**
```python
# Melhorar extração do JSON: encontrar o JSON mais completo
import re

# Tentar encontrar JSON completo com regex mais robusto
json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
if json_match:
    json_str = json_match.group(0)
else:
    # Fallback original
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"JSON nao encontrado em: {content[:200]}")
    json_str = text[start : end + 1]

# Melhorar regex de fallback para capturar valores com espaços
for field in ["decisao", "wtp", "sentimento", "confianca", "raciocinio"]:
    # Pattern captura até o próximo campo ou final do objeto
    m = re.search(rf'"{field}"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', json_str)
    if not m:
        m = re.search(rf'"{field}"\s*:\s*([0-9.]+)', json_str)
    if m:
        val = m.group(1).strip()
        try:
            fields[field] = float(val) if field in ("wtp", "sentimento", "confianca") else val
        except ValueError:
            fields[field] = val
```

---

## BUG #6: Sem circuit breaker por provider/modelo

**Arquivo:** `ensemble.py`  
**Linhas:** 363-403

**Causa Raiz:**
- O código tem backoff (até 8x), mas não circuit breaker
- Se um provider está morto (ex: Groq com 90% falha), ele continua sendo tentado em cada persona
- Não há contador de falhas consecutivas por source/modelo
- Não há "cooldown" onde source é temporariamente desabilitado

**Severidade:** CRÍTICO  
**Impacto:** 
- deepseek-v4-pro (NVIDIA): 88% falha no N=128
- llama-3.3-70b-versatile (Groq): 90% falha no N=128
- Continua batendo em provider morto, desperdiçando tempo e quota

**Sugestão de Fix (ponytail):**
```python
# Adicionar circuit breaker simples
source_fail_count: dict[str, int] = {}
source_circuit_open_until: dict[str, float] = {}
CIRCUIT_THRESHOLD = 5  # 5 falhas consecutivas = abre circuito
CIRCUIT_COOLDOWN = 300  # 5 minutos cooldown

# No loop de processamento (antes de chamar modelo):
now = time.monotonic()
circuit_until = source_circuit_open_until.get(source, 0)
if now < circuit_until:
    print(f"  [{i}/{n}] {p.owner_name} [{role}] ({source}): SKIP (circuit open, {circuit_until - now:.0f}s remaining)")
    metadados_modelos.append({
        "modelo": model_name,
        "role": role,
        "source": source,
        "erro": "circuit breaker open",
        "skipped": True,
    })
    falhas += 1
    continue

# No except (após linha 391):
source_fail_count[source] = source_fail_count.get(source, 0) + 1
if source_fail_count[source] >= CIRCUIT_THRESHOLD:
    source_circuit_open_until[source] = time.monotonic() + CIRCUIT_COOLDOWN
    source_fail_count[source] = 0  # reset contador
    print(f"  [{i}/{n}] {p.owner_name} [{role}] ({source}): CIRCUIT OPEN (cooldown {CIRCUIT_COOLDOWN}s)")

# No sucesso (linha 389):
source_fail_count[source] = 0  # reset contador em sucesso
```

---

## BUG #7: Sem retry com modelo alternativo (fallback)

**Arquivo:** `ensemble.py`  
**Linhas:** 371-403

**Causa Raiz:**
- Se um modelo falha, o código marca como falha e continua para o próximo modelo
- Não há lista de "modelos alternativos" por modelo principal
- Não há tentativa de chamar outro modelo do mesmo provider ou de outro provider
- Persona pode ter menos de 3 decisões se múltiplos modelos falharem

**Severidade:** ALTO  
**Impacto:** Reduz robustez do ensemble - uma falha de modelo não é compensada

**Sugestão de Fix (ponytail):**
```python
# Adicionar mapeamento de fallbacks em config.py
class ModelRole(BaseModel):
    model: str
    provider: str
    role: str
    role_description: str = ""
    source: str = "gocat"
    fallback_models: list[str] = Field(default_factory=list)  # <-- NOVO

# No ensemble.py, no except (após linha 391):
fallbacks = [m for m in cfg.ensemble.models if m.model == model_name][0].fallback_models
for fallback_model in fallbacks:
    try:
        print(f"  [{i}/{n}] {p.owner_name} [{role}] ({source}): RETRY with {fallback_model}")
        d, meta = await _call_model(client, fallback_model, user_prompt)
        decisoes_persona.append(d)
        metadados_modelos.append({
            "modelo": fallback_model,
            "role": role,
            "source": source,
            "fallback_for": model_name,
            **meta,
        })
        source_backoff[source] = 1.0
        break  # sucesso, sair do loop de fallback
    except Exception as e2:
        print(f"  [{i}/{n}] {p.owner_name} [{role}] ({source}): FALLBACK {fallback_model} FAIL {e2}")
        continue
```

---

## BUG #8: Shuffle de modelos não distribui carga adequadamente

**Arquivo:** `ensemble.py`  
**Linhas:** 354-355

**Código:**
```python
models_this_persona = ensemble_models[:]
random.shuffle(models_this_persona)
```

**Causa Raiz:**
- Shuffle é aleatório, não garante distribuição uniforme
- Se ensemble tem 3 modelos e 1 deles é de source "kilocode" (subprocess lento), ele pode ser processado primeiro em muitas personas
- Não há round-robin ou scheduling baseado em latência anterior

**Severidade:** BAIXO  
**Impacto:** Distribuição subótima de carga, pode causar hotspots

**Sugestão de Fix (ponytail):**
```python
# Usar round-robin em vez de shuffle puro
if not hasattr(run_ensemble, "_model_rr_index"):
    run_ensemble._model_rr_index = 0

# Rotacionar modelos em vez de shuffle
rr_index = run_ensemble._model_rr_index % len(ensemble_models)
models_this_persona = ensemble_models[rr_index:] + ensemble_models[:rr_index]
run_ensemble._model_rr_index += 1
```

---

## BUG #9: Sintetizador não valida se todas as decisões são do mesmo modelo

**Arquivo:** `ensemble.py`  
**Linhas:** 105-117, 220-223

**Causa Raiz:**
- `_compute_concordancia` assume que decisões são de modelos diferentes
- Se houver duplicação de modelo na config (mesmo modelo com roles diferentes), a concordância pode ser calculada incorretamente
- O validator em `config.py` (linha 22-29) valida duplicatas por (model, provider), mas não por model apenas

**Severidade:** BAIXO  
**Impacto:** Métricas de concordância podem ser enganosas

**Sugestão de Fix (ponytail):**
```python
# Em config.py, mudar validação para verificar model apenas
@model_validator(mode="after")
def _modelos_unicos(self) -> "EnsembleConfig":
    seen = set()
    for m in self.models:
        if m.model in seen:
            raise ValueError(f"ensemble: modelo duplicado {m.model}")
        seen.add(m.model)
    return self
```

---

## BUG #10: Não há retry de sintetizador com modelo alternativo

**Arquivo:** `ensemble.py`  
**Linhas:** 410-417

**Código:**
```python
try:
    agregada = await _call_synthesizer(...)
except Exception as e:
    print(f"  [{i}/{n}] {p.owner_name} [SYNTH]: FAIL {e}")
    falhas += 1
```

**Causa Raiz:**
- Se sintetizador falha, não há retry com modelo alternativo
- Persona inteira é descartada mesmo com 3 decisões válidas
- Não há fallback para agregação simples (média das decisões)

**Severidade:** ALTO  
**Impacto:** Perda de dados quando sintetizador falha

**Sugestão de Fix (ponytail):**
```python
# Adicionar fallback para agregação simples
try:
    agregada = await _call_synthesizer(...)
except Exception as e:
    print(f"  [{i}/{n}] {p.owner_name} [SYNTH]: FAIL {e}, usando agregação simples")
    falhas += 1
    # Agregação simples como fallback
    rank = {"ignorou": 0, "visualizou": 1, "clicou": 2, "agendou": 3}
    agregada = DecisaoAggregada(
        decisao_final=min((d.decisao for d in decisoes_persona), key=lambda x: rank.get(x, 0)),
        wtp_medio=sum(d.wtp for d in decisoes_persona) / len(decisoes_persona),
        sentimento_medio=sum(d.sentimento for d in decisoes_persona) / len(decisoes_persona),
        objecoes_consolidadas=list({o for d in decisoes_persona for o in d.objecoes}),
        divergence_score=divergence_score_from_decisoes(decisoes_persona),
        concordancia=[{"modelo_a": p.modelo_a, "modelo_b": p.modelo_b, "concordam": p.concordam} 
                      for p in _compute_concordancia(decisoes_persona)],
        confianca_agregada=sum(d.confianca for d in decisoes_persona) / len(decisoes_persona),
        raciocinio_sintese="Sintese automatica (sintetizador falhou)"
    )
```

---

## RESUMO POR SEVERIDADE

### CRÍTICO (1)
- BUG #6: Sem circuit breaker por provider/modelo

### ALTO (4)
- BUG #1: Backoff sem recovery temporal
- BUG #2: Sintetizador sem fallback
- BUG #7: Sem retry com modelo alternativo
- BUG #10: Sintetizador sem fallback em falha

### MÉDIO (3)
- BUG #3: Timeout hardcoded devin
- BUG #4: Timeout hardcoded cline
- BUG #5: JSON parsing frágil

### BAIXO (2)
- BUG #8: Shuffle não ótimo
- BUG #9: Validação de duplicatas

---

## PRIORIDADE DE FIX

1. **BUG #6 (Circuit breaker)** - Crítico, causa 88-90% falha em alguns modelos
2. **BUG #2 (Sintetizador fallback)** - Alto, descarta personas inteiras
3. **BUG #7 (Modelo alternativo)** - Alto, reduz robustez
4. **BUG #1 (Backoff decay)** - Alto, penaliza providers intermitentes
5. **BUG #3, #4 (Timeouts configuráveis)** - Médio, fácil de implementar
6. **BUG #5 (JSON parsing)** - Médio, melhora taxa de sucesso
7. **BUG #10 (Sintetizador fallback)** - Alto, similar ao #2
8. **BUG #8, #9** - Baixo, otimização

---

## NOTAS ADICIONAIS

### Problemas de Design Identificados

1. **Acoplamento forte com gocat:** Todos os adapters assumem gocat como backend central. Se gocat cair, todo sistema para.
   
2. **Não há telemetria por modelo:** Não há métricas de latência, taxa de erro, custo por modelo em tempo real.

3. **Não há rate limiting por modelo:** Se um modelo tem quota limitada, não há proteção contra esgotamento.

4. **Schema não versionado:** Se o schema de DecisaoPersona mudar, JSONs antigos podem quebrar.

5. **Não há validação de consistência:** Não há verificação se wtp, sentimento e decisao são consistentes (ex: decisao="agendou" mas sentimento=-0.9).

### Sugestões Futuras

1. Adicionar Prometheus/metrics para telemetria em tempo real
2. Implementar rate limiting por modelo com token bucket
3. Adicionar versionamento no schema (ex: DecisaoPersonaV1, DecisaoPersonaV2)
4. Implementar validação de consistência cruzada entre campos
5. Adicionar cache de respostas por (persona, modelo) para evitar chamadas duplicadas
