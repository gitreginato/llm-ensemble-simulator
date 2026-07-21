# Setup do Ambiente de Simulação

## Ambiente Python

```bash
cd /home/lucas/Projetos/simulacao-multi-agent
python3.11 -m venv .venv
.venv/bin/pip install --upgrade pip

# LaunchSimulation
.venv/bin/pip install -r launch-simulation/backend/requirements.txt

# MarketFish
.venv/bin/pip install -r market-fish/requirements.txt
```

## Fixes aplicados

### 1. onnxruntime vs numpy

O `onnxruntime==1.27.0` instalado pelo requirements conflitava com `numpy==1.26.4`.
Fix:
```bash
.venv/bin/pip install --force-reinstall onnxruntime==1.18.1
.venv/bin/pip install packaging==24.2 protobuf==5.29.6 --force-reinstall
```

### 2. duckduckgo-search import

O `launch-simulation` usava `from ddgs import DDGS`, mas a versão 5.3.1 do pacote usa `from duckduckgo_search import DDGS`.
Patch aplicado em: `launch-simulation/backend/app/agents/researcher.py`.

### 3. MarketFish OpenRouter

Adicionado provider `openrouter` no registry: `market-fish/config/models_registry.json`.
Modelos cadastrados:
- `google/gemini-2.5-flash-lite`
- `meta-llama/llama-4-scout-17b-16e-instruct`
- `mistralai/mistral-small-3.2-24b-instruct`

## Configuração de API

Editar `launch-simulation/backend/.env` e adicionar uma chave OpenAI-compatible.

Exemplo Groq (recomendado para simulações multi-agente):
```env
LLM_API_KEY=gsk_xxx
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL_NAME=meta-llama/llama-4-scout-17b-16e-instruct

LLM_BOOST_API_KEY=gsk_xxx
LLM_BOOST_BASE_URL=https://api.groq.com/openai/v1
LLM_BOOST_MODEL_NAME=meta-llama/llama-4-scout-17b-16e-instruct
```

Exemplo OpenRouter:
```env
LLM_API_KEY=sk-or-xxx
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL_NAME=google/gemini-2.5-flash-lite

LLM_BOOST_API_KEY=sk-or-xxx
LLM_BOOST_BASE_URL=https://openrouter.ai/api/v1
LLM_BOOST_MODEL_NAME=google/gemini-2.5-flash-lite
```

## Rodar simulações

### Uma variante
```bash
python run_scenario.py devincriator a
python run_scenario.py slz_n8n b
```

### Todas as variantes
```bash
python run_all_scenarios.py
```

## Cenários preparados (baseados em pesquisa de mercado)

### DevinCriator / Owl Regent Studio

- `scenarios/devincriator/variant_a.txt` - Padarias e confeitarias (sacola, cardápio, estoque)
- `scenarios/devincriator/variant_b.txt` - Salões de beleza e estéticas (feed, cartão, agenda)
- `scenarios/devincriator/variant_c.txt` - Bares e lanchonetes (fachada, cardápio, iFood)
- `scenarios/devincriator/variant_d.txt` - Profissionais liberais (credibilidade, proposta PDF)
- `scenarios/devincriator/variant_e.txt` - Lojas de roupas e boutiques (vitrine, sacola)
- `scenarios/devincriator/variant_f.txt` - Food trucks e quiosques (visibilidade, menu-board)

### SLZ N8N Stack

- `scenarios/slz_n8n/variant_a.txt` - Padarias e mercearias (abertura cedo, estoque)
- `scenarios/slz_n8n/variant_b.txt` - Salões de beleza e estéticas (horário noturno, botão de pânico)
- `scenarios/slz_n8n/variant_c.txt` - Lojas de roupas e calçados (vitrine, estoque)
- `scenarios/slz_n8n/variant_d.txt` - Bares e restaurantes (caixa, bebidas, porta dos fundos)
- `scenarios/slz_n8n/variant_e.txt` - Farmácias e drogarias (medicamentos controlados)
- `scenarios/slz_n8n/variant_f.txt` - Residências (família, bairros residenciais)

## Smoke test

```bash
cd launch-simulation/backend
.venv/bin/python run.py
# Deve subir em http://localhost:8000
```
