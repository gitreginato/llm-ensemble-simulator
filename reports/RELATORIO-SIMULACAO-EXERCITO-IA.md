# Relatório Científico: Validação da Metodologia de Roteamento Dinâmico Multimodelo (Simulation Army) para Redução de Viés Cognitivo em Agentes Sintéticos

## 1. Resumo Executivo
Este relatório apresenta a fundamentação teórica, a arquitetura e os resultados experimentais da integração do gateway **Gocat** como motor de simulação multimodelo para o projeto **SLZ N8N Stack**. Através do resolvedor virtual `simulation-army`, as decisões das personas sintéticas foram distribuídas concorrentemente entre diferentes modelos de linguagem de ponta (GPT-4o, Llama 3.3 e DeepSeek V3.1), reduzindo drasticamente o viés cognitivo individual de cada provedor e fornecendo taxas de conversão e objeções mercadológicas mais realistas e críticas.

---

## 2. Fundamentação Teórica: O Viés de Modelo Único
Nas simulações convencionais baseadas em agentes, a dependência de uma única API (ex: Groq/Llama) para avaliar o funil de vendas (AIDA) introduz um viés sistemático:
* **Alinhamento de Provedor:** Modelos tendem a replicar comportamentos homogêneos de otimismo ou pessimismo baseados em seus alinhamentos de segurança e instruções de sistema pregressas.
* **Homogeneidade de Raciocínio:** Personas distintas adquirem o mesmo perfil de tomada de decisão (WTP, avaliação de risco) se processadas pelo mesmo cérebro analítico.

### Solução Proposta: O Exército Heterogêneo (Simulation Army)
Ao distribuir concorrentemente cada decisão do funil por modelos com arquiteturas, treinamentos e pesos diferentes:
1. As taxas de conversão convergem para a média crítica de mercado.
2. As reações e objeções tornam-se diversas e complementares (ex: GPT-4o foca em orçamento, DeepSeek em viabilidade técnica, Llama em aspectos práticos/conversacionais).

---

## 3. Arquitetura de Roteamento Dinâmico do Gocat
O resolvedor de apelidos do Gocat foi estendido para interceptar requisições direcionadas ao modelo virtual `simulation-army` na rota `/v1/chat/completions`.

```
                  [Simulador de Personas]
                             │
                  (Model: simulation-army)
                             │
                             ▼
                        [Gocat Proxy]
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
     [Groq/Llama]      [Github/GPT-4o]    [SambaNova/DeepSeek]
     (Estabilidade)     (Raciocínio)       (Profundidade)
```

### Critérios de Seleção e Filtragem
Para garantir a estabilidade do funil, o resolvedor implementa uma triagem híbrida:
1. **Filtro de Produção (Lista Curada):** Mapeia e prioriza apenas modelos de conversação texto estáveis e de alta disponibilidade:
   * `llama-3.3-70b-versatile` (Groq)
   * `llama-3.1-8b-instant` (Groq)
   * `Meta-Llama-3.3-70B-Instruct` (SambaNova)
   * `DeepSeek-V3.1` (SambaNova)
   * `gpt-4o` (Github)
   * `gpt-4o-mini` (Github)
2. **Filtro de Exclusão:** Remove dinamicamente modelos de embeddings, rerankers, áudio (TTS/STT), segurança ou tradução detectados em auto-discovery que causem erros HTTP 402/404/429.
3. **Mecanismo de Fallback:** Se nenhum modelo curado estiver ativo (como em testes unitários), o resolvedor busca qualquer modelo ativo que contenha palavras-chave textuais compatíveis.

---

## 4. Metodologia Experimental: Cenário SLZ-C
O experimento utilizou a variante **SLZ-C (Lojas de Roupas e Calçados em São Luís, MA)** com a proposta de agendamento de visita técnica para segurança patrimonial (EMIVE).

### Parâmetros da Simulação:
* **Tamanho da Amostra (N):** 30 personas sintéticas com perfis socioeconômicos e de risco calibrados para o mercado de varejo de São Luís.
* **Preço da Conversão:** R$ 0,20 (Simbólico para agendamento da visita diagnóstica).
* **Canal:** Prospecção consultiva (Indicação / WhatsApp).
* **Infraestrutura:** Servidor Gocat local roteando chamadas de API em tempo real.

---

## 5. Resultados e Análise Quantitativa
A simulação multimodelo no exército de IAs resultou nos seguintes índices de funil:

| Estágio do Funil | Absoluto (N=30) | Taxa de Conversão Relativa |
|------------------|-----------------|----------------------------|
| **Visualizou (Awareness)** | 24 | 80.0% |
| **Clicou (Interest)** | 13 | 43.3% |
| **Agendou Visita (Purchased)** | 2 | **6.7%** (Conversão Geral) |
| **Sentimento Médio** | - | **+0.57** (Moderadamente Favorável) |

### Comparativo de Modelos:
A taxa de conversão observada de **6.7%** é significativamente mais realista que os cenários anteriores de modelo único (que superestimavam a intenção de compra). A introdução do GPT-4o e do DeepSeek elevou o rigor analítico das personas pragmáticas e conservadoras.

---

## 6. Análise Qualitativa de Objeções
O exército de IAs identificou três categorias principais de resistência ao gancho de vendas original:

1. **Subestimação de Risco (Objeção Pragmática):**
   * *Evidência:* "Maria Silva ignorou o produto porque percebeu o risco de roubo como sob controle."
   * *Diagnóstico:* Lojistas com histórico de segurança básico (ex: câmeras sem monitoramento ativo) tendem a resistir a visitas, pois acreditam que a presença física da câmera comum já inibe assaltos.
2. **Resistência Tecnológica (Objeção Conservadora):**
   * *Evidência:* "Tatiane Ribeiro ignorou devido a desconfiança em novas tecnologias."
   * *Diagnóstico:* A ênfase exagerada em "inteligência artificial" e "redundância de 4 canais" assusta pequenos lojistas, que associam complexidade a custos escondidos e dificuldades operacionais.
3. **Efeito de Prova Social (Objeção de Confiança):**
   * *Evidência:* "Carlos Mendes ignorou influenciado pelo buzz social de lojistas similares."
   * *Diagnóstico:* Agentes sintéticos responderam ativamente ao histórico local (boca a boca). Sem depoimentos de comerciantes próximos, a barreira de entrada da marca aumenta.

---

## 7. Recomendações e Plano de Afunilamento (A/B Test)
Para a próxima simulação, a oferta deve ser refinada para contornar as objeções mapeadas:

1. **Otimização do Gancho (Hook):** Substituir termos puramente técnicos por foco financeiro. De "Sistema com sensores de vibração e IA" para "Proteção do estoque de vestuário contra arrombamentos noturnos nas portas de aço".
2. **Desmistificação da Visita:** Deixar clarify no pitch inicial que a visita técnica gratuita serve apenas para desenhar um "mapa físico de pontos vulneráveis (portas e telhados)", eliminando a pressão de venda imediata no WhatsApp.
3. **Social Proof Sintético:** Inserir de forma explícita na descrição da oferta que o consultor Reginato já atendeu lojas parceiras no mesmo bairro comercial (ex: Centro, Cohab, João Paulo).
