# Copilot Instructions: llm-ensemble-simulator

## Visao geral
Simulacao de mercado multi-agente com ensemble heterogeneo de LLMs para reducao de
vies cognitivo em personas sinteticas. Cada persona e processada por 3 modelos de
vendors distintos em paralelo, agregada via sintetizador de consenso.

## Stack
- Python 3.11+ com type hints
- numpy + scipy para metricas estatisticas
- pydantic para config e validacao
- httpx para chamadas HTTP async
- Adaptadores: Ollama, Cline, Kilocode, Devin
- pytest (316 testes)

## Convencoes
- Cada source tem rate limit independente
- Diversidade preservada antes de agregar (nao agregar cedo)
- Metricas: entropia, KL divergence, IC95%
- Se entropia do ensemble ~= baseline, hipotese refutada (parar)
- Dados sinteticos com seed fixo em testes
- Commits em portugues, Conventional Commits

## NAO faca
- Nao hardcodear API keys (sempre .env)
- Nao agregar respostas antes da sintese (colapsa diversidade)
- Nao usar um unico LLM (viess sistemático de alinhamento)
- Nao logar tokens ou dados sensiveis
- Nao commitar .env ou resultados com dados reais
