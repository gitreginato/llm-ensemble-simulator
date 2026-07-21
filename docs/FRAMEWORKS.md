# Frameworks e Dependencias

Data: 2026-07-19
Principio: ponytail. stdlib antes de dep nova. 1 linha antes de 50. Reusar o que ja esta no .venv.

## 1. Ja instalados no .venv (reusar, nao reinstalar)

Verificacao: `SETUP.md` + `pip list` (rodar para confirmar antes de usar).

| Pacote | Origem | Uso no projeto |
|--------|--------|----------------|
| `requests` | launch-simulation | chamadas HTTP sincronas |
| `python-dotenv` | launch-simulation | load .env |
| `pydantic` | launch-simulation | schema validation |
| `numpy` | market-fish | arrays, estatistica |
| `scipy` | market-fish | entropia, KL, bootstrap, permutacao |
| `pandas` | market-fish | tabulacao de resultados |
| `streamlit` | market-fish | dashboard (opcional) |
| `onnxruntime==1.18.1` | market-fish (fix em SETUP.md) | embeddings locais |
| `duckduckgo-search` | launch-simulation | pesquisa web |
| `langgraph` | launch-simulation | orquestracao de agentes |
| `pytest` | tests | eval harness |

## 2. A instalar (minimo, justificado)

### 2.1 `httpx` (async HTTP)
Razao: ensemble paralelo precisa de chamadas concorrentes. `requests` e sincrono. `httpx` suporta async nativo e e compativel OpenAI.
Ponytail check: `httpx` e leve (~200KB), sem deps pesadas, mantido pela mesma equipe do `requests`. Publicado ha anos.
Instalar: `.venv/bin/pip install httpx`

### 2.2 Nenhum outro

Tudo o resto (estatistica, diversidade, schema, eval) ja esta coberto por scipy + pydantic + pytest que ja estao no .venv.

## 3. Frameworks externos (datasets, nao pacotes pip)

### 3.1 NVIDIA Nemotron-Personas-Brazil
Razao: personas sinteticas representativas do Brasil (8M+ personas, CC BY 4.0). Substitui a geracao ad-hoc de personas por LLM, reduzindo viés de "LLM gerando LLM".
Acesso: HuggingFace streaming (sem download full). Ja usado pelo `market-simulation` PyPI (referencia).
Ponytail check: se as 30 personas atuais (em `scenarios/`) ja sao suficientes para o piloto, adiar Nemotron para a Fase 2 (N=300). Nao instalar agora.

### 3.2 Benchmarks publicos de conversao B2B (ja coletados nesta sessao)
Evidencia nivel B (web_search em fontes nomeadas, 2026):
- Sirius CRM Anuario 2026: conversao lead->cliente Brasil media 8%, saudavel 2-5%
- PowerGO 2026: exemplo B2B 6.5% conversao geral
- Touchstone BPO 2026: contact-to-meeting 4-10% (SaaS/B2B tech)
- StealthAgents 2026: cold call->appointment 1-3% (unoptimized), 4-8% (optimized)
- eesier 2026: WhatsApp positive reply 10-20%, meeting rate 1-3%
- ORRJO 2026: meeting booked per outreach 0.5-1.2% (average), 1.5-2.5% (good)

Range adotado como proxy de calibração: **conversao geral 2-8%**, **agendamento 1-8%**.
Limitacao declarar: proxy global, nao especifico de seguranca patrimonial em SLZ. Quando EMIVE tiver dados reais, recalibrar.

## 4. NAO instalar (YAGNI explicito)

| Pacote | Razao do nao |
|--------|--------------|
| `langchain` | launch-simulation ja usa langgraph, nao duplicar |
| `autogen` | overkill para 1 pipeline de 3 camadas |
| `crewai` | overkill, nao temos 5+ agentes com papéis complexos |
| `llama-index` | nao temos RAG, temos pesquisa em arquivos |
| `vllm` | nao servimos modelos, usamos APIs |
| `sentence-transformers` | onnxruntime ja esta no .venv para embeddings |
| `opentelemetry` | gocat ja tem /metrics Prometheus |
| `mlflow` | 1 eval pytest basta, nao precisamos de MLOps platform |

## 5. Comando unico de setup (apos aprovacao)

```bash
cd /home/lucas/Projetos/projects/ai-research-and-agents/simulacao-multi-agent
.venv/bin/pip install httpx
# verificar:
.venv/bin/pip list | grep -E "httpx|scipy|pydantic|pytest|numpy|pandas"
```

## 6. Validacao de versao (regra global: > 7 dias publicado)

Antes de instalar `httpx`, verificar data da ultima release estavel:
```bash
.venv/bin/pip index versions httpx  # ou pip install httpx==  (forca erro que lista versoes)
```
Rejeitar `latest` flutuante. Fixar versao especifica publicada ha > 7 dias.
