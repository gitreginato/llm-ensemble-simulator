# LLM Ensemble Simulator

> Simulação de mercado multi-agente com ensemble heterogêneo de LLMs para redução de viés cognitivo em personas sintéticas. Cada persona é processada por 3 modelos de vendors distintos em paralelo, agregada via sintetizador de consenso, com diversidade medida estatisticamente.

## Stack

| Camada | Tecnologia | Por quê |
|--------|-----------|---------|
| Linguagem | Python 3.11+ | Ecossistema, type hints, async |
| LLMs | GPT-4o, DeepSeek V3.1, Llama 3.3 70B | Heterogeneidade arquitetural reduz viés |
| Agregação | Sintetizador de consenso (1 modelo frontier) | Dispatch paralelo + síntese |
| Métricas | numpy, scipy | Entropia, KL divergence, IC95% |
| Testes | pytest (316 testes) | TDD, edge cases, adapters |
| Adaptadores | Ollama, Cline, Kilocode, Devin | Rate limit independente por source |

## O que aprendi

- **Viés de modelo único é real e mensurável**: simulações com 1 só LLM (ex: só Llama) introduzem viés sistemático de alinhamento. Personas distintas adquirem o mesmo perfil de tomada de decisão. Validei isso com baseline antes de implementar o ensemble.
- **Ensemble heterogêneo reduz viés**: 3 modelos de vendors distintos em paralelo, agregados por sintetizador de consenso. A literatura 2025-2026 valida: AI Council (Pith 2026) mostra -25pp em concentração de 1a escolha (p<0.001), Council Mode (arXiv 2604.02923) mostra -35.9% alucinação.
- **Diversidade precisa ser preservada antes de agregar**: se agregar cedo, o colapso de diversidade anula o ganho do ensemble (arXiv 2604.18005). Implementei independência total antes da síntese.
- **Métricas estatísticas para validar ganho**: entropia do ensemble > entropia do baseline (p<0.05, permutação). KL divergence entre distribuições de decisão. IC95% para taxas de conversão.
- **Adaptadores com rate limit independente**: cada source (Ollama, Cline, Kilocode, Devin) tem seu próprio adapter com rate limit isolado, evitando que uma source bloqueie as outras.
- **Honestidade científica**: se a entropia do ensemble for ~= baseline (sem ganho de diversidade), a hipótese é refutada e paramos. Documentei isso como princípio do projeto.

## Arquitetura

```
[Persona] -> [3 modelos em paralelo, independentes]
                -> [Sintetizador de consenso (1 modelo frontier)]
                    -> [Decisão agregada + divergence_score]
                        -> [Métricas: entropia, KL, IC95%]
```

```
simulation_army_v2/
├── ensemble.py              # Fan-out + sintetizador (5 sources)
├── personas_v5.py           # Gerador de personas com bairros, sazonalidade
├── modelo_probabilistico.py # Sigmoid + Bayes + Monte Carlo
├── informacao.py            # Entropia, MI, JSD, chi-quadrado
├── pitch_templates.py       # Pitch por nicho + objeções + competências
├── bairros_slz.py           # 13 bairros reais de São Luís-MA
├── baseline.py              # Baseline modelo único (obrigatório para comparação)
├── ollama_adapter.py        # Adapter Ollama direto (HTTP, rate limit independente)
├── cline_adapter.py         # Adapter Cline CLI (subprocess, headless --json)
├── kilocode_adapter.py      # Adapter Kilocode CLI (subprocess, JSON events)
├── devin_adapter.py         # Adapter Devin CLI (subprocess --print)
├── metrics.py               # Métricas de avaliação
├── costs.py                 # Estimativa de custo de tokens
└── audit.py                 # Auditoria de resultados
```

## Funcionalidades

- **FASE 0 (sem LLM)**: simulador programático puro. 26 nichos, 13 bairros reais, modelo sigmoid com 12 features. N=1000 em 0.37s, conversão ~16% vs 13.4% real (dataset 142 personas).
- **FASE 1 (com LLM)**: ensemble heterogêneo com 3+ models em paralelo, síntese de consenso, divergência medida.
- **A/B test de ofertas**: comparar pitches (técnico vs financeiro) com N personas e IC95%.
- **Métricas estatísticas**: entropia, KL divergence, JSD, chi-quadrado, MI, IC95%.
- **Calibração contra benchmark**: mediana de conversão dentro de [2%, 8%] (benchmark B2B Brasil).
- **Auditoria**: rastreabilidade de decisões, raciocínio não-vazio, confiança >= 0.6.

## Como rodar

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# FASE 0: simulador programático (sem LLM, sem rede)
PYTHONPATH=. python scripts/run_sim_v0.py -n 1000 --mes 7

# FASE 1: ensemble com LLMs
PYTHONPATH=. python -m simulation_army_v2.ensemble \
  --scenario scenarios_v2/slz-c-army-v5-fast.yaml \
  --n 128 --seed 42 \
  --output results_v2/ensemble_v5_fast_n128_s42.json

# Baseline modelo único (obrigatório para comparação)
PYTHONPATH=. python -m simulation_army_v2.baseline \
  --scenario scenarios_v2/slz-c-army-v5-fast.yaml \
  --model gpt-4o --n 30

# A/B test
PYTHONPATH=. python -m simulation_army_v2.ab_test \
  --scenario scenarios_v2/slz-c-army-v5-fast.yaml \
  --variant-a pitch_tecnico --variant-b pitch_financeiro --n 300

# Testes
pytest tests_v2/ -v
```

## Testes

316 testes em `tests_v2/` cobrindo:
- Modelo probabilístico (232+205 testes): sigmoid, Bayes, Monte Carlo, edge cases
- Personas v5 (250+286 testes): geração, bairros, sazonalidade, budget, edge cases
- Ensemble (148+96 testes): fan-out, síntese, helpers
- Pitch templates (135+134 testes): por nicho, objeções, edge cases
- Schema, config, costs, metrics, audit, dashboard

```bash
pytest tests_v2/ -v
```

## Avaliação

3 checks de validação:

1. **Calibração**: mediana da conversão geral dentro de [2%, 8%] (benchmark B2B Brasil)
2. **Diversidade**: entropia do ensemble > entropia do melhor baseline (p<0.05, permutação)
3. **Coerência**: >= 90% das decisões com confiança >= 0.6 e raciocínio não-vazio

## Limitações declaradas

- Benchmark público (2-8% conversão B2B Brasil) é proxy global, não específico do domínio. Recalibrar com dados reais quando disponíveis.
- Custo ~4.2x tokens vs modelo único (Council Mode). Estimar antes de N=300.
- Se entropia do ensemble ~= baseline (sem ganho de diversidade), a hipótese é refutada e paramos.

## Fundamentação acadêmica

- **AI Council** (Pith 2026): heterogeneidade arquitetural reduz concentração de 1a escolha em ~25pp (p<0.001)
- **Council Mode** (arXiv 2604.02923): dispatch paralelo + síntese de consenso, -35.9% alucinação
- **Diversity Collapse** (arXiv 2604.18005): independência preservada antes de agregar evita colapso
- **Plurals** (CHI 2025): focus groups sintéticos escolhidos sobre zero-shot em 75% dos trials

## Licença

[MIT](LICENSE)
