# Progresso FASE 1: Simulacao com LLM

Inicio: 2026-07-21 (sessao noturna, usuario dormindo)

## Objetivo
Rodar ensemble heterogeneo de LLMs (5 sources, 12 modelos) em 128 personas
(top 8 bairros x 8 nichos x 2) e comparar com FASE 0 (modelo probabilistico).

## Tasks Kanban (FASE 1)

| ID | Task | Status | Inicio | Fim |
|---|---|---|---|---|
| 36 | Adaptar ensemble.py para personas V5 | in_progress | 2026-07-21 | - |
| 37 | Criar cenario V5 YAML | backlog | - | - |
| 38 | Configurar auth Cline CLI | in_progress | 2026-07-21 | - |
| 39 | Validar conectividade 5 sources | backlog | - | - |
| 40 | Rodar piloto 128 personas | backlog | - | - |
| 41 | Relatorio FASE 1 vs FASE 0 | backlog | - | - |
| 42 | Auditoria cruzada Devin 10% | backlog | - | - |
| 43 | Expandir N=300 | backlog | - | - |
| 44 | A/B test | backlog | - | - |

## Log de execucao

### 2026-07-21 inicio
- 304 testes passando (FASE 0 + adapters cline/ollama)
- Kanban FASE 1 criado com 9 tasks e dependencias
- Iniciando #36 (adaptar ensemble V5) e #38 (auth cline) em paralelo

### 2026-07-21 #38 done: Auth Cline CLI
- Cline CLI configurado com gocat como backend (http://127.0.0.1:8080/v1)
- Provider: openai-compatible (gocat), keys ficam no gocat
- Validado: gpt-oss:120b via cline retorna JSON valido em ~18s

### 2026-07-21 #36 done: Adaptar ensemble para V5
- USER_PROMPT_TEMPLATE_V5 criado com mensalidade, contrato, limitacoes EMIVE
- _profile_v5_to_prompt_kwargs mapeia PersonaV5 para prompt
- config.py aceita persona_version (v4/v5) e mes (1-12)
- ensemble.py detecta persona_version e usa generate_personas_v5
- Schema atualizado com 4 novas objecoes: area_externa, concorrencia_local, contract_fear, ticket_alto
- 316 testes passando (305 + 11 novos)

### 2026-07-21 #37 done: Cenario V5 YAML
- slz-c-army-v5.yaml: 11 modelos, 5 sources, persona_version=v5
- Sources: gocat (3), kilocode (2), devin (2), cline (2), ollama (2)
- Sintetizador: gemma4:31b (gpt-oss:120b falhou, reasoning model)
- Benchmark: 10-20% (calibrado FASE 0)

### 2026-07-21 #39 done: Conectividade 5 sources
- gocat: OK (6s)
- kilocode: OK (21s)
- devin: OK (16s)
- cline: OK (14s) apos remover --baseurl do comando
- ollama: OK (8s)
- 5/5 sources funcionando via gocat

### 2026-07-21 #40 in_progress: Piloto N=4
- 4 personas processadas, 38/44 chamadas OK (86%)
- gocat: 12/12 (100%), ollama: 8/8 (100%), cline: 6/8 (75%)
- kilocode: 7/8 (87%), devin: 5/8 (62%)
- Sintetizador gpt-oss:120b falhou 3/4 (content vazio, reasoning model)
- Trocado para gemma4:31b: sintese OK na 1a persona
- Custo: $0.00 (todos free)
- Conversao: 0% (apenas 1 sintese, visualizou)

### 2026-07-21 #40 N=8 completo (cenario fast)
- 8/8 personas, 8/8 sinteses OK (gemma4:31b 100%)
- 45/48 chamadas OK (94%)
- 0% conversao (sintetizador conservador: 4 clicou, 4 visualizou)
- Modelos individuais: 5 agendaram (11.1%), 17 clicaram, 19 visualizaram, 4 ignoraram
- Divergence score medio: 0.35
- Objecoes top: area_externa (7), contract_fear (6), existing_solution (6)
- Custo: $0.00
- Tempo: ~20min (2.5min/persona)

### 2026-07-21 #40 N=128 em andamento (cenario fast)
- Cenario fast: 6 modelos, 3 sources (gocat, cline, ollama), sem kilocode/devin
- ~2.3min/persona = ~5h estimadas para 128 personas
- 3/128 personas processadas ate agora
- Rodando em background durante a noite
