# Simulacao Multi-Agent - Agent Notes

## Build/Test Commands

```bash
cd /home/lucas/Projetos/projects/ai-research-and-agents/simulacao-multi-agent
.venv/bin/pytest tests_v2/                    # 316 tests, ~5s
PYTHONPATH=. .venv/bin/python scripts/run_sim_v0.py -n 1000 --mes 7
PYTHONPATH=. .venv/bin/python scripts/gerar_relatorio_fase0.py
PYTHONPATH=. .venv/bin/python scripts/test_connectivity.py
PYTHONPATH=. .venv/bin/python -m simulation_army_v2.ensemble --scenario scenarios_v2/slz-c-army-v5-fast.yaml --n 128 --seed 42 --output results_v2/ensemble_v5_fast_n128_s42.json
PYTHONPATH=. .venv/bin/python scripts/gerar_relatorio_fase1.py
```

## FASE 0: Simulador Programatico (sem LLM, sem rede)

- 26 nichos (perenes + volateis), 13 bairros reais de Sao Luis-MA
- Modelo: sigmoid com 12 features (theft, no_security, perene, area_externa, concorrencia_local, etc)
- Mensalidade R$ 294-450 por porte. Contrato 36 meses com multa proporcional
- Limitacao EMIVE: so area interna (P_PRECISA_AREA_EXTERNA por nicho)
- Saturacao concorrencia: 20-30 instaladores locais em SLZ
- 288 testes FASE 0 (218 originais + 70 edge cases) + 16 testes adapters = 304 total
- N=1000 em 0.37s, conversao ~16% vs 13.4% real (dataset 142 personas)

## Arquitetura

- `simulation_army_v2/personas_v5.py`: gerador de personas com bairros, sazonalidade, budget
- `simulation_army_v2/modelo_probabilistico.py`: sigmoid + Bayes + Monte Carlo
- `simulation_army_v2/informacao.py`: entropia, MI, JSD, chi-quadrado
- `simulation_army_v2/pitch_templates.py`: pitch por nicho + objecoes + competencias
- `simulation_army_v2/bairros_slz.py`: 13 bairros reais + sazonalidade
- `simulation_army_v2/cline_adapter.py`: adapter Cline CLI (subprocess, headless --json)
- `simulation_army_v2/ollama_adapter.py`: adapter Ollama direto (HTTP, sem gocat, rate limit independente)
- `simulation_army_v2/devin_adapter.py`: adapter Devin CLI (subprocess --print)
- `simulation_army_v2/kilocode_adapter.py`: adapter Kilocode CLI (subprocess, JSON events)
- `simulation_army_v2/ensemble.py`: fan-out + sintetizador (sources: gocat, kilocode, devin, cline, ollama)
- `scripts/run_sim_v0.py`: CLI do simulador FASE 0
- `scripts/gerar_relatorio_fase0.py`: relatorio MD + mapa de prospeccao JSON

## Sources de LLM (FASE 1)

| Source | Adapter | Rate limit | Modelos |
|---|---|---|---|
| gocat | `_call_model` (baseline.py) | compartilhado | SambaNova, Groq, GitHub, Ollama cloud |
| kilocode | `kilocode_adapter.py` | independente | via kilocode CLI |
| devin | `devin_adapter.py` | independente | glm-5-2, swe-1-7, swe-1-6 |
| cline | `cline_adapter.py` | independente | qualquer provider do cline (anthropic, openai, openrouter, ollama, etc.) |
| ollama | `ollama_adapter.py` | independente | gpt-oss:120b, gpt-oss:20b, nemotron-3-*, minimax-*, gemma4:31b |

Config Ollama: `OLLAMA_BASE_URL` (default: https://ollama.com/v1) + `OLLAMA_API_KEY`

## Limitacoes Conhecidas

- `est_empresas_nicho` usa heuristica 5% (1/26 nichos). Upgrade: LeadJet tem distribuicao real
- `NICHOS_PERENES` derivado de SEGMENT_BASELINES_V5["perene"] (unica fonte de verdade)
- `beta_posterior` usa np.random.default_rng seeded por rng.randint (numpy nao aceita random.Random)
- Dataset real tem 142 personas (19 agendaram = 13.4%). Simulado da ~16%
