# Rúbrica para Atribuição de APIs às Simulações

Baseado nos benchmarks do `arena-de-ias` (atualizado 11/07/2026).

## APIs/Modelos disponíveis e perfil

| API/Modelo | Provider | Força | Fraqueza | Custo aprox |
|------------|----------|-------|----------|-------------|
| **Llama 4 Scout** | Groq | Rápido, JSON, multimodal, suporta 30k tokens/request | Não segue formato ultra-estrito (insere reasoning), TPM 30k | Free |
| **Gemini 2.5 Flash Lite** | Google / OpenRouter | Consistente, bom para UI, barato | Google free: 5 RPM; OpenRouter paid requer crédito | Free/Paid |
| **Gemini 3.1 Flash Lite Preview** | Google | Mais estável free do Gemini, JSON limpo | 5 RPM, quotas diárias | Free |
| **Mistral Small 3.2 24B** | OpenRouter | Excelente judge de imagem, consistente, 1.4s | Depende de OpenRouter free tier | Free |
| **Mistral Large 3 675B** | NVIDIA | Rápido, consistente, raciocínio | Quota NVIDIA esgota, 429 frequente | Free |
| **GLM-4.7-Flash** | Z.ai | JSON perfeito, sem code fences, sem TPM limit | 1 QPS, latência ~33s, 429/timeout frequente | Free |
| **Qwen3.6-27B** | Groq | Mais rápido do benchmark, barato | Per-request limit ~8k tokens | Free |

## Recomendação por tarefa de simulação

### 1. Simulação multi-agente com muitos agents (LaunchSimulation / MarketFish)
- **Critério:** baixo custo por agente, alta confiabilidade, JSON válido.
- **Primária:** `Llama 4 Scout (Groq)` - rápido, free, 30k/request.
- **Fallback:** `Gemini 2.5 Flash Lite (OpenRouter)` - consistente, mas requer crédito.
- **Evitar:** GLM-4.7-Flash (lento demais para 30-50 agents), NVIDIA (quota esgota).

### 2. Geração de persona / backstory detalhado
- **Critério:** qualidade de texto, criatividade, segue instrução.
- **Primária:** `Gemini 2.5 Flash Lite (OpenRouter)` ou `Mistral Large 3 (NVIDIA)`.
- **Econômica:** `Llama 4 Scout (Groq)` - suficiente para personas simples.

### 3. Extração de entidades / knowledge graph para simulação
- **Critério:** JSON válido, sem code fences, capacidade de extrair nodes/edges.
- **Primária:** `GLM-4.7-Flash (Z.ai)` - melhor score no Graphify.
- **Rápida:** `Llama 3.3 70B (Groq)` - mas limitado a ~12k tokens/request.
- **Consistente:** `Gemini 3.1 Flash Lite Preview (Google)` - mas 5 RPM.

### 4. Judge / avaliação de conteúdo gerado
- **Critério:** qualidade de julgamento, consistência de score.
- **Primária:** `Mistral Small 3.2 24B (OpenRouter)` - 7.67/10, stdev 0.47.
- **Rápida:** `Llama 4 Scout (Groq)` - 6.67/10, 0.7s.
- **Alta qualidade:** `Llama 3.2 90B Vision (NVIDIA)` - 7.83/10, mas instável.

### 5. Simulação de conteúdo social (Viralix)
- **Critério:** qualidade de texto, entendimento de nicho, sentimento.
- **Primária:** `Gemini 2.5 Flash Lite (OpenRouter)` - consistente e capaz em UI/texto.
- **Fallback:** `Llama 4 Scout (Groq)` - rápido e free.

## Recomendação final para este projeto

Dado que queremos rodar várias simulações com custo controlado:

| Ferramenta | API recomendada | Motivo |
|------------|-----------------|--------|
| **LaunchSimulation** | `Llama 4 Scout (Groq)` | Free, rápido, 30k/request, suficiente para 30 agents |
| **MarketFish** | `Llama 4 Scout (Groq)` ou `Gemini 2.5 Flash Lite (OpenRouter)` | Groq para economia, OpenRouter para qualidade de personas |
| **Viralix** | `Gemini 2.5 Flash Lite (OpenRouter)` | Qualidade de texto e sentimento |

## Nota sobre OpenRouter vs Groq

- **Groq:** melhor custo/beneficio free, mas rate limit real é TPM (não RPM). Para 30 agents com prompts ~2k tokens, ~1-2 simulações/min.
- **OpenRouter:** mais flexível, modelos pagos mais capazes, mas free tier limitado e upstream pode dar 429.
