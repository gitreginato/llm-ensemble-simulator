# Simulation Army v2

Simulacao de mercado multi-agente com ensemble heterogeneo de LLMs para reducao de vies cognitivo em personas sinteticas.

## O que e

Um pipeline de 3 camadas que processa cada persona sintetica por **3 modelos de vendors distintos** em paralelo (GPT-4o, DeepSeek V3.1, Llama 3.3 70B), agrega as respostas via 1 modelo sintetizador de consenso, e mede a diversidade estatisticamente. O objetivo e reduzir o vies de modelo unico em simulacoes de funil de vendas (AIDA), obtendo taxas de conversao que convergem para a media critica de mercado em vez do otimismo/pessimismo homogeneo de um unico alinhamento.

## Por que existe

Simulacoes convencionais com 1 modelo so (ex: so Groq/Llama) introduzem vies sistemático:
- **Alinhamento de provedor**: modelos replicam comportamentos homogeneos de otimismo/pessimismo.
- **Homogeneidade de raciocínio**: personas distintas adquirem o mesmo perfil de tomada de decisao.

A literatura 2025-2026 valida a solucao:
- **AI Council** (Pith 2026): heterogeneidade arquitetural reduz concentracao de 1a escolha em ~25pp (p<0.001).
- **Council Mode** (arXiv 2604.02923): dispatch paralelo + sintese de consenso, -35.9% alucinacao.
- **Diversity Collapse** (arXiv 2604.18005): independencia preservada antes de agregar evita colapso de diversidade.
- **Plurals** (CHI 2025): focus groups sinteticos escolhidos sobre zero-shot em 75% dos trials.

## Arquitetura (resumo)

```
[Persona] -> [3 modelos em paralelo, independentes]
                -> [Sintetizador de consenso (1 modelo frontier)]
                    -> [Decisao agregada + divergence_score]
                        -> [Metricas: entropia, KL, IC95%]
```

Detalhe completo: `docs/BLUEPRINT.md`

## O que ja temos

| Componente | Caminho | Status |
|------------|---------|--------|
| Gocat (gateway LLM, 395 testes) | `/home/lucas/Projetos/gocat` | Ativo, 5 providers |
| launch-simulation (orquestrador) | `launch-simulation/` | Funcional, rodou 12 simulacoes |
| market-fish (referencia ensemble) | `market-fish/` | Instalado |
| Motor proprio (funil AIDA) | `src/advanced_simulation.py` | Funcional |
| Cenarios SLZ-C + DevinCriator | `scenarios/` | 12 variantes prontas |
| Pesquisa de mercado SLZ | `pesquisa/` | 11 arquivos |
| .venv Python 3.11 | `.venv/` | Deps instaladas |

Inventario completo: `docs/INVENTARIO.md`

## O que precisamos instalar

Minimo (ponytail):
- `httpx` (async HTTP para ensemble paralelo)

Frameworks e justificativa: `docs/FRAMEWORKS.md`

## Como o gocat entra

O gocat fica como gateway simples (roteia 1 modelo por chamada). O simulador Python faz N chamadas concorrentes via `httpx` async, uma por modelo, e agrega localmente. Nao mexer no gocat estavel.

Detalhe: `docs/GOCAT-INTEGRATION.md`

## Setup

```bash
cd /home/lucas/Projetos/projects/ai-research-and-agents/simulacao-multi-agent

# 1. Ativar venv existente
source .venv/bin/activate

# 2. Instalar httpx (unica dep nova)
pip install httpx

# 3. Verificar gocat no ar
curl -s http://127.0.0.1:8080/health
# se nao estiver: cd /home/lucas/Projetos/gocat && ./gocat &

# 4. Verificar 3 modelos do ensemble respondem
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Authorization: Bearer $GOCAT_API_KEY" \
  -d '{"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":"ping"}]}' | jq .choices[0].message.content
```

## Uso (apos implementar)

```bash
# Piloto: 30 personas, 3 seeds
python -m simulation_army_v2 run --scenario scenarios_v2/slz-c-army.yaml --n 30 --seed 42

# Baseline modelo unico (obrigatorio para comparacao)
python -m simulation_army_v2 baseline --scenario scenarios_v2/slz-c-army.yaml --model gpt-4o --n 30

# Producao: 300 personas, 3 seeds, IC95%
python -m simulation_army_v2 run --scenario scenarios_v2/slz-c-army.yaml --n 300 --seed 42,43,44

# A/B test de oferta
python -m simulation_army_v2 ab-test --scenario scenarios_v2/slz-c-army.yaml \
  --variant-a pitch_tecnico --variant-b pitch_financeiro --n 300
```

## Eval

```bash
.venv/bin/pytest eval/simulation_army_eval.py -v
```

3 checks:
1. **Calibracao**: mediana da conversao geral dentro de [2%, 8%] (benchmark publico B2B Brasil)
2. **Diversidade**: entropia do ensemble > entropia do melhor baseline (p<0.05, permutacao)
3. **Coerencia**: >= 90% das decisoes com `confianca >= 0.6` e `raciocinio` nao-vazio

## Roadmap

`ROADMAP.md`

## Kanban (fila de tarefas)

```bash
python3 /home/lucas/Projetos/projects/ai-research-and-agents/agentic-engineering/kanban-agent/scripts/kanban.py show
python3 /home/lucas/Projetos/projects/ai-research-and-agents/agentic-engineering/kanban-agent/scripts/kanban.py next
```

Workflow por task: RESEARCH -> IMPLEMENT -> TEST -> PONYTAIL -> AUTORESEARCH -> DONE.

## Limitacoes declaradas

- Benchmark publico (2-8% conversao B2B Brasil) e proxy global, nao especifico de seguranca patrimonial em SLZ. Recalibrar com dados reais EMIVE quando disponiveis.
- Personas sinteticas nao representam minorias especificas de SLZ (limitacao PSII, WVS-grounded).
- Custo ~4.2x tokens vs modelo unico (Council Mode). Estimar antes de N=300.
- Se entropia do ensemble ~= baseline (sem ganho de diversidade), a hipotese e refutada e paramos.

## Documentacao

- `docs/BLUEPRINT.md`: arquitetura tecnica detalhada (3 fases, 12 passos)
- `docs/INVENTARIO.md`: o que temos vs o que precisamos
- `docs/FRAMEWORKS.md`: frameworks a instalar (e quais NAO instalar)
- `docs/GOCAT-INTEGRATION.md`: integracao com gocat existente
- `ROADMAP.md`: fases, milestones, criterios de parada
- `RELATORIO-SIMULACAO-EXERCITO-IA.md`: relatorio original (historico)
- `RELATORIO-FINAL.md`: 12 simulacoes anteriores (historico)

## Principios

1. **Ponytail**: 1 modulo + 1 config + 1 eval. stdlib antes de dep. YAGNI.
2. **Factualidade**: toda claim verificada nesta sessao ou declarada como hipotese com nivel de evidencia.
3. **AutoResearch**: eval primeiro, depois implementar. Subagentes em paralelo para edge cases.
4. **Honestidade**: se a hipotese for refutada (sem ganho de diversidade), parar e reportar.
