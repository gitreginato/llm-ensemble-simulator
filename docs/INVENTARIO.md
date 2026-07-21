# Inventario: o que temos vs o que precisamos

Data: 2026-07-19
Verificacao: leitura direta do filesystem nesta sessao (evidencia nivel S).

## 1. O que JA TEMOS (ativo, verificavel)

### 1.1 Gocat (gateway LLM)
Caminho: `/home/lucas/Projetos/gocat`
Binario: `gocat` (12 MB, Go, 395 testes passando com `-race`)

- `/v1/chat/completions` (streaming SSE + nao-streaming), compativel OpenAI
- `/v1/models` dinamico (lista dos providers ativos)
- `/v1/probe` (descoberta de modelos por provider, mimica arena-de-ias)
- Admin API runtime (CRUD providers, aliases, config)
- Model aliasing: `aliases:` mapeia model virtual -> provider + model real
- Resolvedor `simulation-army` em `pkg/server/chat.go:119-162`
- Circuit breaker, retry 429/5xx, key rotation, fallback entre providers
- 5 providers ativos: gemini, nvidia, zai, groq, openrouter
- 21 providers desativados (placeholder vazio, basta setar env var)
- Knowledge DB SQLite (`pkg/knowledge/`)
- Swarm consensus (`pkg/swarm/swarm.go`): classifica intent, top-2 em paralelo, valida via Jaccard

### 1.2 Projetos de simulacao (clones open-source)
Caminho: `/home/lucas/Projetos/projects/ai-research-and-agents/simulacao-multi-agent/`

| Projeto | Stack | O que faz | Status |
|---------|-------|-----------|--------|
| `launch-simulation/` | Next.js + FastAPI + LangGraph | 30 personas sinteticas, funil AIDA, swarm dynamics | Funcional (rodou 12 simu) |
| `market-fish/` | Python + Streamlit | 128 consumidores IA heterogeneos, 6 LLMs, 30 rounds | Instalado, nao rodado |
| `foresight/` | Docker + backend + frontend | (nao inspecionado a fundo) | Presente |
| `viralix/` | Node + backend + frontend | Dinamica de rede e influenciadores | Presente |

### 1.3 Motor de simulacao proprio
Caminho: `src/`
- `advanced_simulation.py` (673 linhas): funil AIDA bidirecional, agentes empresariais, boca a boca, categorizacao de rejeicoes. Selecao de provider: Groq > NVIDIA > OpenRouter > env. Rate limit 5s entre chamadas.
- `rule_based_simulation.py` (19KB): motor deterministico calibrado por pesquisa de mercado, sem API.
- `run_advanced_scenarios.py`, `run_rule_based_scenarios.py`: orquestradores.

### 1.4 Cenarios prontos
`scenarios/devincriator/variant_{a..f}.txt` (branding, 6 segmentos)
`scenarios/slz_n8n/variant_{a..f}.txt` (seguranca EMIVE, 6 segmentos)
Formato: `name=`, `description=`, `price_usd=`, `channel=`, `target_market=`, `num_agents=30`

### 1.5 Pesquisa de mercado
`pesquisa/` (11 arquivos): concorrencia, criticas, sistemas existentes, fatores de decisao B2B Brasil, faturamento/margens, orcamento marketing, orcamento seguranca, sazonalidade, segmentos automotivos SLZ, ticket medio.

### 1.6 Resultados historicos
- `RELATORIO-FINAL.md`: 12 simulacoes (6 DevinCriator + 6 SLZ), Groq Llama 4 Scout, N=30 cada.
- `RELATORIO-SIMULACAO-EXERCITO-IA.md`: relatorio do simulation-army (N=30, SLZ-C, 6.7% conversao).
- `advanced_results/`, `rule_based_results/`: JSONs de saida.

### 1.7 Infraestrutura
- `.venv/` Python 3.11 com deps do launch-simulation + market-fish instaladas
- Fixes documentados em `SETUP.md` (onnxruntime, ddgs, OpenRouter registry)
- `graphify-out/` gerado (grafo de dependencias do projeto)

## 2. O que PRECISAMOS (gaps identificados)

### 2.1 Gap critico no gocat (verificacao nivel S)
O resolvedor `simulation-army` em `pkg/server/chat.go:119-162` **nao faz ensemble**:
- Escolhe UM modelo aleatorio do pool por chamada (`rng.Intn(len(pool))`)
- Nao dispara N modelos em paralelo
- Nao agrega respostas
- Nao mede diversidade
- Nao tem schema de saida estruturado

O relatorio `RELATORIO-SIMULACAO-EXERCITO-IA.md` descreve "distribuicao concorrente" que **nao existe no codigo**. A versao atual e equivalente a round-robin aleatorio, nao a um exercito heterogeneo com agregacao.

### 2.2 Gaps de metodologia (evidencia nivel A: papers 2025-2026)
| Gap | Paper que endereça | Status atual |
|-----|---------------------|--------------|
| Agregacao estruturada (consenso, nao votacao) | Council Mode, CHOIR | Ausente |
| Independencia entre chamadas (sem shared context) | Diversity Collapse | Nao garantido |
| Metrica de diversidade (entropia, KL, pairwise) | PSII, Diversity Collapse | Ausente |
| Calibracao contra benchmark externo | WVS-grounded, MarketFish | Ausente |
| Baseline de modelo unico para comparacao | AI Council | Ausente |
| Validacao de coerencia por modelo frontier | AI Council | Ausente |
| Power analysis + IC95% + multiplas seeds | estatistica basica | N=30 fixo, sem IC |
| Schema JSON estruturado de decisao | (engenharia basica) | Parcial (advanced_simulation tem JSON mas nao normalizado) |

### 2.3 Gaps de framework
| Necessidade | Framework candidato | Razao |
|-------------|---------------------|-------|
| Estatistica (IC, bootstrap, permutacao) | `scipy.stats` + `numpy` | stdlib cientifica Python, ja no .venv |
| Diversidade (entropia, KL) | `scipy.stats.entropy` | stdlib cientifica |
| Avaliacao de LLM (eval harness) | proprio eval em pytest | ponytail: nao instalar framework se 1 eval basta |
| Personas representativas | NVIDIA Nemotron-Personas-Brazil | dataset publico CC BY 4.0 (8M+ personas BR) |
| Orquestracao de chamadas paralelas | `asyncio` + `httpx` | stdlib Python, sem dep nova |
| Schema validation | `pydantic` (ja no .venv via launch-sim) | reusar dep existente |

### 2.4 Gaps de processo
- Sem eval automatico (AutoResearch nao rodou nesta area)
- Sem CI para os scripts Python
- Sem pre-commit
- Sem AGENTS.md no projeto (apenas no gocat)

## 3. O que NAO precisamos (YAGNI)

- NAO precisamos de LangChain/LangGraph novo: launch-simulation ja usa.
- NAO precisamos de framework de multi-agente novo: market-fish ja tem.
- NAO precisamos de UI nova: launch-simulation tem Next.js, market-fish tem Streamlit.
- NAO precisamos de DB novo: gocat ja tem SQLite em `pkg/knowledge/`.
- NAO precisamos de 10 arquivos: 1 modulo + 1 config + 1 eval (ponytail).

## 4. Decisao de arquitetura

Reusar o maximo do existente:
- **Gocat** como gateway: estender o resolvedor `simulation-army` para fazer ensemble real (paralelo + agregacao) em vez de round-robin aleatorio.
- **launch-simulation** como orquestrador de personas: ja tem funil AIDA e 30 personas.
- **market-fish** como referencia de ensemble heterogeneo: ja faz 6 LLMs em paralelo (estudar `engine/`).
- **src/advanced_simulation.py** como baseline de modelo unico: ja tem o funil, basta rodar com 1 provider fixo.
- **scenarios/** e **pesquisa/** como cenarios e benchmarks de calibracao.

Adicionar (minimo):
- 1 modulo `simulation_army_v2.py` (~250 linhas): pipeline ensemble + agregacao + metricas.
- 1 config `scenarios_v2/slz-c-army.yaml`: ensemble, papéis, benchmark ranges.
- 1 eval `eval/simulation_army_eval.py`: 3 checks (calibracao, diversidade, coerencia).
- 1 patch no gocat `pkg/server/chat.go`: resolvedor v2 (paralelo + sintetizador).

Nada mais. Se um segundo cenario surgir, generaliza-se; ate la, YAGNI.
