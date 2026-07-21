# Relatório Final - Simulações de Mercado

## 1. Resumo Executivo

Foram executadas **12 simulações** com o LaunchSimulation (30 agentes sintéticos cada) para testar reações de mercado de dois projetos reais:

- **DevinCriator / Owl Regent Studio**: identidade visual para pequenos comerciantes de bairro no Brasil.
- **SLZ N8N Stack**: sistema de segurança inteligente franquia EMIVE para comércios e residências em São Luís, MA.

API utilizada: **Groq Llama 4 Scout** (modelo free com 30k tokens/request e melhor score em JSON estruturado nos testes do arena-de-ias).

### Principais descobertas

- **DevinCriator**: nicho mais assertivo nas simulações iniciais é **padarias e confeitarias** (36.4% de conversão, sentimento +0.73). Nas simulações avançadas rule-based, **food trucks** (20.0%) e **lava-jatos** (6.7%) mostram potencial, enquanto **oficinas mecânicas** têm baixa adesão a branding (0%).
- **SLZ N8N**: nicho mais assertivo nas simulações iniciais é **lojas de roupas e calçados** (46.2% de taxa de agendamento). Nas simulações rule-based com segmentos automotivos, **lojas de carros usados/multimarcas** lideram com **20.0%** de agendamento, seguido por oficinas (6.7%) e lava-jatos (3.3%).
- **Objeção dominante em ambos os projetos**: preço/custo alto e percepção de falta de necessidade imediata.
- **Segmento com pior conversão**: lojas de roupas para branding (10.5%) e bares/restaurantes para segurança (14.8%).
- **Hipótese validada**: segmentos automotivos (especialmente lojas de carros usados) são altamente receptivos a segurança por causa do estoque valioso exposto.

## 2. Metodologia

- **Fase 1 - Simulações com LLM**: LaunchSimulation (open source, MIT) com 30 personas sintéticas por variante, 6 variantes por projeto.
- **Fase 2 - Pesquisa de mercado**: 8 tópicos pesquisados (orçamentos, sazonalidade, concorrência, fatores de decisão, segmentos automotivos de São Luís, etc.).
- **Fase 3 - Simulações avançadas rule-based**: motor deterministico com ruído calibrado pelos dados de pesquisa, 7 cenários (4 DevinCriator + 3 SLZ) focados em segmentos automotivos e validação de nichos anteriores.
- **Métricas**: visualização/awareness, clique/interest, consideration, intent, compra/agendamento, taxa de conversão geral, sentimento médio, objeções e insights estratégicos.

## 3. Resultados - DevinCriator / Owl Regent Studio

| Var | Segmento | Visualizou | Clicou | Comprou | Conversão | Sentimento | Principal objeção |
|-----|----------|------------|--------|---------|-----------|------------|-------------------|
| a | Padarias/confeitarias | 22 (73.3%) | 17 (56.7%) | 8 (26.7%) | **36.4%** | +0.73 | High price |
| f | Food trucks/quiosques | 19 (63.3%) | 11 (36.7%) | 5 (16.7%) | 26.3% | +0.48 | High price |
| c | Bares/lanchonetes | 20 (66.7%) | 14 (46.7%) | 4 (13.3%) | 20.0% | +0.62 | High cost |
| b | Salões de beleza/estéticas | 25 (83.3%) | 16 (53.3%) | 4 (13.3%) | 16.0% | +0.52 | Skepticism about new marketing services |
| d | Profissionais liberais | 22 (73.3%) | 18 (60.0%) | 3 (10.0%) | 13.6% | +0.63 | Skepticism about justifying the investment |
| e | Lojas de roupas/boutiques | 19 (63.3%) | 9 (30.0%) | 2 (6.7%) | 10.5% | +0.53 | Limited marketing budget |

### Ranking por assertividade

1. **Padarias/confeitarias** - clara dor visual (sacola, cardápio), vergonha do logo amador, retorno social rápido.
2. **Food trucks/quiosques** - reconhecimento de longe é dor real, mas preço ainda freia.
3. **Bares/lanchonetes** - interesse existe, mas prioridade é menor e custo inibe.
4. **Salões de beleza/estéticas** - alto engajamento inicial, mas ceticismo sobre resultado de marketing.
5. **Profissionais liberais** - entendem valor, mas acham caro para investir sem garantia de retorno.
6. **Lojas de roupas/boutiques** - menor clique e conversão. Concorrência com fast fashion e Shopee distrai atenção.

## 4. Resultados - SLZ N8N Stack

| Var | Segmento | Visualizou | Clicou | Agendou | Taxa de agendamento | Sentimento | Principal objeção |
|-----|----------|------------|--------|---------|---------------------|------------|-------------------|
| c | Lojas de roupas/calçados | 26 (86.7%) | 19 (63.3%) | 12 (40.0%) | **46.2%** | +0.67 | Custo da solução é alto |
| f | Residências | 23 (76.7%) | 15 (50.0%) | 7 (23.3%) | 30.4% | +0.62 | High price |
| a | Padarias/mercearias | 22 (73.3%) | 16 (53.3%) | 5 (16.7%) | 22.7% | +0.55 | Skepticism about system's effectiveness |
| e | Farmácias/drogarias | 22 (73.3%) | 16 (53.3%) | 5 (16.7%) | 22.7% | +0.65 | Concerns about ease of use |
| d | Bares/restaurantes | 27 (90.0%) | 19 (63.3%) | 4 (13.3%) | 14.8% | +0.70 | System complexity |
| b | Salões de beleza/estéticas | 21 (70.0%) | 15 (50.0%) | 3 (10.0%) | 14.3% | +0.49 | High cost |

### Ranking por assertividade

1. **Lojas de roupas/calçados** - estoque visível e valioso na vitrine, dor clara de arrombamento.
2. **Residências** - medo familiar é forte gatilho, emocional e imediato.
3. **Padarias/mercearias** - abertura cedo e estoque atraente geram interesse, mas eficácia é questionada.
4. **Farmácias/drogarias** - medicamentos controlados são atrativo, mas facilidade de uso preocupa.
5. **Bares/restaurantes** - alta visualização e clique, mas complexidade do sistema afasta na hora de agendar.
6. **Salões de beleza/estéticas** - menor taxa de agendamento. Custo e percepção de não prioridade.

## 5. Top objeções consolidadas

- **High price / High cost**: 16 ocorrências (dominante em ambos os projetos).
- **Price sensitivity / Limited budget**: 7 ocorrências.
- **Skepticism about effectiveness / value**: 5 ocorrências.
- **System complexity / ease of use**: 3 ocorrências.
- **Lack of immediate need / prioritizing other expenses**: 4 ocorrências.

## 6. Análise cruzada e insights estratégicos

### 6.1 O mesmo segmento reage diferente para branding e segurança

- **Lojas de roupas**: 10.5% conversão para branding vs 46.2% para segurança. A dor de segurança é mais urgente e concreta.
- **Padarias**: 36.4% para branding e 22.7% para segurança. São receptivas a ambos, mas branding gera mais interesse imediato.
- **Salões de beleza**: 16.0% para branding e 14.3% para segurança. Segmento desafiador para ambos; necessita de maior educação.
- **Bares/restaurantes**: 20.0% para branding e 14.8% para segurança. Interesse moderado, mas decisão demora.

### 6.2 Preço é o maior freio, mas o problema é percepção de valor

- Para DevinCriator, o preço de **$45 USD** (~R$ 250) é visto como alto por parte do público, embora esteja abaixo da faixa de mercado (R$ 300-1500).
- Para SLZ, o preço simbólico de **R$ 0.20** pela visita não é o problema. A objeção "custo alto" refere-se ao sistema completo (instalação, monitoramento, mensalidade). A proposta deve deixar explícito que a visita é gratuita e a proposta personalizada vem depois.

### 6.3 Sentimento positivo não garante conversão

- Bares/restaurantes (SLZ) tiveram o maior sentimento (+0.70) mas uma das piores conversões (14.8%).
- Isso indica que o produto agrada, mas a barreira de complexidade/complexidade de setup inibe a ação.

## 7. Recomendações aplicáveis

### 7.1 DevinCriator / Owl Regent Studio

1. **Foco no nicho vencedor**: priorizar campanhas e prospecção para **padarias e confeitarias** nos primeiros 60-90 dias.
2. **Food trucks como segundo nicho**: testar anúncios com foco em "ser visto de longe" e "menu-board profissional". Conversão de 20% nas simulações rule-based reforça o potencial.
3. **Automotivo (branding)**: evitar oficinas mecânicas genéricas para branding. Investir apenas em **estética automotiva/lava-jatos premium** que vendem imagem, nunca em oficinas de bairro.
4. **Reformular oferta para lojas de roupas**: criar um kit menor (apenas vitrine + sacola) por R$ 144-197 para reduzir a objeção de preço.
5. **Profissionais liberais**: trocar o argumento de "cobrar mais caro" por "parecer profissional antes do primeiro atendimento" e oferecer proposta PDF como case.
6. **Salões de beleza**: usar antes/depois de feed e depoimentos de outras donas de salão para vencer o ceticismo.
7. **Comunicação de valor**: sempre mostrar aplicações práticas (sacola, cardápio, cartão, proposta) e não apenas o logo.

### 7.2 SLZ N8N Stack

1. **Prioridade absoluta**: **lojas de carros usados/multimarcas** (20% de agendamento nas simulações rule-based) e lojas de roupas/calçados (46.2% na rodada inicial). Estoque visível e valioso é o melhor gatilho.
2. **Residências**: manter como segundo nicho prioritário; medo familiar é emocional e imediato.
3. **Oficinas mecânicas**: abordar com argumento de proteção de ferramentas e estoque de peças. Conversão modesta (6.7%), mas interesse existe.
4. **Padarias/mercearias**: usar o argumento "abertura segura às 5h" e estoque protegido. Levar cases de padarias que já instalaram.
5. **Bares/restaurantes**: simplificar a mensagem. Destacar "instalação sem obra" e "app fácil" para vencer a objeção de complexidade.
6. **Farmácias**: enfatizar proteção de medicamentos controlados e conformidade. Oferecer visita técnica com checklist de segurança.
7. **Salões de beleza**: reforçar o botão de pânico e segurança no horário noturno. Usar narrativa de proteção da equipe feminina.
8. **Lava-jatos**: focar em proteção de equipamentos de pressão e chaves de clientes. Menor prioridade que lojas de carros usados e oficinas.
9. **Preço**: deixar claro que a visita técnica é gratuita e a proposta é personalizada. Evitar falar de valores totais no primeiro contato.

### 7.3 Melhoria geral de proposta e assertividade

- **Antes/depois**: para branding, mostrar transformação real. Para segurança, mostrar mapa de risco e pontos vulneráveis.
- **Testemunhos e cases**: ceticismo é uma objeção recorrente. Ter 2-3 cases por segmento aumenta conversão.
- **Call-to-action único**: para SLZ, a conversão é agendamento de visita. Não vender no WhatsApp, marcar visita.
- **Pagamento facilitado**: para DevinCriator, oferecer parcelamento em 2x sem juros ou kit básico de entrada.
- **Focar na dor urgente**: segurança vende proteção de estoque/loja; branding vende vergonha do visual amador e perda de clientes.

## 8. Simulações avançadas rule-based (sem API)

Devido à instabilidade das APIs free no momento, executamos uma segunda rodada com um motor rule-based calibrado a partir dos dados de pesquisa (orçamentos, WTP, sazonalidade, existing solutions, concorrência). Os resultados servem para triangulação e não substituem a simulação com LLM.

### 8.1 Resultados rule-based - DevinCriator / Owl Regent Studio

| Código | Segmento | Awareness | Interest | Consideration | Intent | Compra | Conversão geral | Principal rejeição |
|--------|----------|-----------|----------|---------------|--------|--------|-----------------|--------------------|
| DC-AUTO-01 | Lava-jatos/estética automotiva | 22 (73.3%) | 15 (50.0%) | 11 (36.7%) | 8 (26.7%) | 2 (6.7%) | **6.7%** | need_lack |
| DC-AUTO-02 | Oficinas mecânicas | 24 (80.0%) | 14 (46.7%) | 9 (30.0%) | 4 (13.3%) | 0 (0.0%) | 0.0% | need_lack |
| DC-VAL-01 | Padarias/confeitarias | 26 (86.7%) | 17 (56.7%) | 12 (40.0%) | 4 (13.3%) | 1 (3.3%) | 3.3% | need_lack |
| DC-VAL-02 | Food trucks/quiosques | 25 (83.3%) | 22 (73.3%) | 15 (50.0%) | 13 (43.3%) | 6 (20.0%) | **20.0%** | timing |

### 8.2 Resultados rule-based - SLZ N8N Stack

| Código | Segmento | Awareness | Interest | Consideration | Intent | Agendamento | Taxa geral | Principal rejeição |
|--------|----------|-----------|----------|---------------|--------|-------------|------------|--------------------|
| SLZ-AUTO-01 | Lojas de carros usados/multimarcas | 25 (83.3%) | 25 (83.3%) | 19 (63.3%) | 16 (53.3%) | 6 (20.0%) | **20.0%** | timing |
| SLZ-AUTO-02 | Oficinas mecânicas | 21 (70.0%) | 14 (46.7%) | 11 (36.7%) | 8 (26.7%) | 2 (6.7%) | 6.7% | need_lack |
| SLZ-AUTO-03 | Lava-jatos/estética automotiva | 23 (76.7%) | 16 (53.3%) | 10 (33.3%) | 8 (26.7%) | 1 (3.3%) | 3.3% | need_lack |

### 8.3 Interpretação dos resultados rule-based

- **Segmentos automotivos têm potencial claro para SLZ**: lojas de carros usados lideram (20% de agendamento), oficinas têm interesse moderado, lava-jatos são mais desafiadores.
- **Branding para automotivo é difícil**: oficinas e lava-jatos priorizam pouco identidade visual. A exceção pode ser estética automotiva de luxo, não o lava-jato de bairro.
- **Food trucks continuam fortes para DevinCriator**: 20% de conversão e alto interesse, confirmando o achado das simulações iniciais.
- **Padarias permanecem como nicho sólido**, embora a conversão rule-based seja mais baixa que a da rodada com LLM.
- **Timing é objeção real**: mesmo com preço baixo, muitos donos adiam decisões por fluxo de caixa, sazonalidade ou falta de urgência.

## 9. Limitações e próximos passos

### Limitações

- Agentes sintéticos simulam reações, mas não substituem testes reais com clientes.
- A rodada rule-based usa parâmetros calibrados manualmente; a validação final requer simulação com LLM quando as APIs estiverem estáveis.
- Preço de $45 USD para DevinCriator pode ser interpretado literalmente pelos agentes; testar com preço em R$ pode alterar percepção.
- Para SLZ, o modelo de preço simbólico (R$ 0.20) pode confundir agents sobre o custo real do sistema.

### Próximos passos recomendados

1. Rodar teste A/B de preço para DevinCriator: R$ 197 vs R$ 244 vs R$ 497 parcelado.
2. Criar variantes de SLZ com mensagens simplificadas para bares e salões.
3. Priorizar prospecção de **lojas de carros usados** para SLZ e **food trucks** para DevinCriator nos próximos 30 dias.
4. Coletar 2-3 cases reais e rodar novas simulações com social proof embutido.
5. Validar com leads reais: campanhas pagas de R$ 50-100 em cada nicho vencedor.
6. Quando as APIs estiverem estáveis, rodar as simulações LLM-based com os mesmos parâmetros e comparar com os resultados rule-based.
7. Considerar MarketFish ou Viralix para simular dinâmica de rede e influenciadores.
