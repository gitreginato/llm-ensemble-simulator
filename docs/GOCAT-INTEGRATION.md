# Integracao com Gocat Existente

Data: 2026-07-19
Verificacao: leitura direta de `pkg/server/chat.go:119-162` nesta sessao (evidencia nivel S).

## 1. Estado atual do resolvedor simulation-army

Arquivo: `/home/lucas/Projetos/gocat/pkg/server/chat.go`, linhas 119-162.

```go
if model == "simulation-army" {
    // Curated list of known stable text models in production
    stableModels := map[string]string{
        "llama-3.3-70b-versatile":     "groq",
        "llama-3.1-8b-instant":        "groq",
        "Meta-Llama-3.3-70B-Instruct": "sambanova",
        "DeepSeek-V3.1":               "sambanova",
        "gpt-4o":                      "github",
        "gpt-4o-mini":                 "github",
    }
    // ... monta pool de candidatos ativos ...
    if len(pool) > 0 {
        rng := rand.New(rand.NewSource(time.Now().UnixNano()))
        chosen := pool[rng.Intn(len(pool))]
        return chosen.provider, chosen.model, true
    }
}
```

### Diagnostico (evidencia nivel S)
O resolvedor atual **escolhe 1 modelo aleatorio por chamada**. Isso e round-robin aleatorio, NAO ensemble. O relatorio `RELATORIO-SIMULACAO-EXERCITO-IA.md` descreve "distribuicao concorrente" que nao existe no codigo.

Consequencia:
- Cada persona e processada por 1 modelo so (sorteado).
- 30 personas podem ser processadas por 30 modelos diferentes (ou todos pelo mesmo, se o RNG sortear igual).
- Nao ha agregacao, nao ha consenso, nao ha medida de diversidade.
- O "exercito" nao existe: e 1 soldado por chamada.

## 2. Opcoes de integracao

### Opcao A: Ensemble no gocat (Go)
Estender `resolveAlias` para, ao receber `simulation-army`, disparar N goroutines em paralelo para N modelos, agregar via 1 modelo sintetizador, retornar 1 resposta.
- Pro: centralizado, reusavel por qualquer cliente OpenAI-compatible.
- Contra: gocat e gateway generico, nao simulador. Adicionar logica de agregacao de personas polui o core. Quebra separacao de concerns.
- Contra: agregacao depende do schema do simulador (decisao de funil AIDA), que e dominio do simulador, nao do gateway.

### Opcao B: Ensemble no simulador Python (recomendado)
Manter o gocat como gateway simples. O simulador Python (`simulation_army_v2.py`) faz N chamadas concorrentes ao gocat (uma por modelo, via `httpx` async), cada uma pedindo o modelo real (`gpt-4o`, `llama-3.3-70b-versatile`, `DeepSeek-V3.1`), e agrega localmente.
- Pro: separacao de concerns limpa. Gocat roteia 1 modelo por chamada (ja faz isso). Simulador orquestra o ensemble e agrega.
- Pro: agregacao fica em Python onde esta o schema do funil AIDA.
- Pro: reusa o aliasing existente do gocat (cliente pede `gpt-4o`, gocat roteia para github).
- Pro: ponytail. Nao muda o gocat (395 testes estaveis). Adiciona 1 modulo Python.
- Contra: cliente faz N chamadas em vez de 1. Mas e paralelo (async), latencia ~= 1 chamada.

### Decisao: Opcao B
Razao: ponytail + separacao de concerns + nao mexer no gocat estavel.

## 3. Como o gocat e usado na Opcao B

### 3.1 Roteamento por modelo real
O simulador pede modelos reais diretamente:
- `gpt-4o` -> gocat roteia para `github` (via alias ou model index HPA*)
- `llama-3.3-70b-versatile` -> gocat roteia para `groq`
- `DeepSeek-V3.1` -> gocat roteia para `sambanova` (quando ativo) ou fallback

### 3.2 Fallback automatico
Se `sambanova` estiver desativado (categoria A, placeholder vazio), gocat faz fallback para outro provider que tenha o modelo. Se nenhum tiver, retorna 503 e o simulador trata como falha de 1 dos N modelos (nao derruba o ensemble).

### 3.3 Circuit breaker e retry
O gocat ja tem circuit breaker por provider e retry 429/5xx. O simulador nao precisa reimplementar. Se 1 dos 3 modelos falhar apos retries, o ensemble prossegue com 2 (declarar `divergence_score` alto).

### 4.4 Metricas
O gocat ja expoe `/metrics` em formato Prometheus. O simulador pode ler `gocat_provider_requests_total{provider}` e `gocat_provider_errors_total{provider}` para reportar quais modelos falharam no ensemble.

## 4. Mudancas no gocat (minimas, opcionais)

### 4.1 Opcional: alias `simulation-army-v2`
Se quisermos que o simulador peça 1 modelo virtual e o gocat faça o fan-out, podemos adicionar um alias especial. Mas isso viola a separacao de concerns (Opcao A). **Nao fazer.**

### 4.2 Opcional: endpoint `/v1/ensemble`
Adicionar endpoint que recebe 1 request e retorna N respostas (uma por modelo do pool). Mais limpo que o cliente fazer N chamadas, mas adiciona superficie de API ao gocat. **Avaliar na Fase 1 se a latencia de N chamadas paralelas for problema.**

### 4.3 Nao mudar nada (default)
O gocat fica como esta. O simulador faz N chamadas concorrentes via `httpx` async. Simples, funciona, nao quebra testes.

## 5. Providers a ativar no gocat

Para o ensemble SLZ-C, precisamos de 3 modelos heterogeneos de vendors distintos:

| Papel cognitivo | Modelo | Provider gocat | Status | Acao |
|------------------|--------|----------------|--------|------|
| Pragmatico/orcamento | `gpt-4o` | `github` | Desativado (cat A) | Setar `GITHUB_API_KEY` + `enabled: true` |
| Conservador/risco tecnico | `DeepSeek-V3.1` | `sambanova` | Desativado (cat A) | Setar `SAMBANOVA_API_KEY` + `enabled: true` |
| Conversacional/prova social | `llama-3.3-70b-versatile` | `groq` | Ativo | Ja funciona |

Alternativas se github/sambanova nao tiverem key:
- `gpt-4o` via `openrouter` (ativo): `openai/gpt-4o`
- `DeepSeek-V3.1` via `openrouter` (ativo): `deepseek/deepseek-chat-v3.1`
- `llama-3.3-70b-versatile` via `groq` (ativo): ja funciona

Ponytail: usar openrouter para os 3 se github/sambanova nao tiverem key. 1 provider, 3 modelos. Menos configuracao.

## 6. Validacao da integracao (antes de implementar)

```bash
# 1. Gocat no ar
cd /home/lucas/Projetos/gocat && ./gocat &

# 2. Testar 1 chamada por modelo
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Authorization: Bearer $GOCAT_API_KEY" \
  -d '{"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":"ping"}]}' | jq .choices[0].message.content

curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Authorization: Bearer $GOCAT_API_KEY" \
  -d '{"model":"openai/gpt-4o","messages":[{"role":"user","content":"ping"}]}' | jq .choices[0].message.content

curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Authorization: Bearer $GOCAT_API_KEY" \
  -d '{"model":"deepseek/deepseek-chat-v3.1","messages":[{"role":"user","content":"ping"}]}' | jq .choices[0].message.content

# 3. Se os 3 retornarem 200, a integracao funciona.
```

## 7. Risco e mitigacao

| Risco | Mitigacao |
|-------|-----------|
| Gocat nao esta rodando | Simulador verifica `/health` antes de iniciar ensemble |
| 1 dos 3 modelos falha | Ensemble prossegue com 2, `divergence_score` alto, logar |
| Rate limit do openrouter | Gocat ja tem retry 429 + backoff. Simulador adiciona delay entre personas |
| Custo 3x tokens (Council Mode reporta 4.2x) | Estimar custo antes de N=300. Piloto N=30 primeiro |
| Latencia N chamadas paralelas | `httpx` async + `asyncio.gather`, latencia ~= chamada mais lenta |
