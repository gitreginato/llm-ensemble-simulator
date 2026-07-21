# Blueprint Tecnico: Simulation Army v2

Data: 2026-07-19
Status: design (nao implementado)
Principio: ponytail. 1 modulo + 1 config + 1 eval. stdlib antes de dep. YAGNI.

## 1. Objetivo

Tornar a metodologia de "exercito heterogeneo de IAs" **efetiva e defensavel**:
1. Validacao cientifica (calibracao contra benchmark, metrica de diversidade, IC95%)
2. Aplicacao pratica (A/B test de oferta para EMIVE/SLZ-C)
3. Framework reutilizavel (1 modulo Python, 1 config YAML, 1 eval pytest)

## 2. Fundamentacao cientifica (evidencia nivel A/B, 2025-2026)

| Paper | Achave que valida | Aplicacao aqui |
|-------|-------------------|----------------|
| AI Council (Pith 2026) | Heterogeneidade arquitetural reduz concentracao de 1a escolha em ~25pp (p<0.001). Efeito aparece quando nao ha resposta objetivamente correta. | 1 modelo por papel cognitivo (pragmatico, conservador, conversacional) |
| Council Mode (arXiv 2604.02923) | Dispatch paralelo + sintese por consenso: -35.9% alucinacao, +7.8pts TruthfulQA. Custo 4.2x tokens. | Pipeline 3 camadas com sintetizador |
| CHOIR (ACL 2026) | Votacao majoritaria empata em N baixo. Harmonizacao estruturada supera. | Sintetizador decide, nao votacao |
| Diversity Collapse (arXiv 2604.18005) | Topologia densa contrai diversidade. Independencia preservada antes de agregar. | N chamadas sem shared context |
| Plurals (CHI 2025) | Focus groups sinteticos escolhidos sobre zero-shot em 75% dos trials. | Personas + ensemble = foco group |
| MarketFish | 128 consumidores em 6 LLMs, 6 papers acadêmicos. Mesmo paradigma. | Referencia de implementacao |
| Sirius 2026, PowerGO, Touchstone, StealthAgents, eesier, ORRJO | Benchmarks publicos B2B Brasil: conversao 2-8%, agendamento 1-8% | Calibracao do eval |

## 3. Arquitetura

```
[Persona i] (perfil socioeconomico + estagio AIDA + oferta)
        |
        v
   [Fan-out async]  (httpx.AsyncClient, asyncio.gather)
        |
   +---+---+---+
   |   |   |   |
   v   v   v   v
 [gpt-4o] [DeepSeek-V3.1] [llama-3.3-70b]  (3 modelos, vendors distintos)
   |   |   |
   v   v   v
 [N respostas estruturadas JSON]
        |
        v
   [Sintetizador-consenso]  (1 modelo frontier, ex: gpt-4o-mini)
   Le os N raciocinios, marca concordancia/discordancia,
   produz decisao agregada + divergence_score (0=unanime, 1=split total)
        |
        v
   [Decisao agregada + score de divergencia]
        |
        v
   [Coletor de metricas]
   - entropia de Shannon sobre distribuicao de decisoes
   - pairwise disagreement rate
   - KL divergence vs baseline modelo unico
   - taxa de conversao + IC95% (bootstrap)
```

### 3.1 Camada 1: Fan-out independente (P2: independencia)
- Cada modelo recebe o MESMO prompt da persona, sem ver as respostas dos outros.
- `httpx.AsyncClient` + `asyncio.gather` dispara as 3 chamadas concorrentes.
- Timeout por chamada: 30s (alinhado com gocat).
- Se 1 falhar, ensemble prossegue com 2 (logar, `divergence_score` alto).

### 3.2 Camada 2: Sintetizador de consenso (P3: agregacao estruturada)
- 1 chamada adicional a um modelo frontier (ex: `gpt-4o-mini` via openrouter).
- Input: os N JSONs de resposta + instrucao de sintetizar.
- Output: decisao agregada + `divergence_score` + `concordancia` (lista de pares concordantes/discordantes).
- Nao e votacao: o sintetizador le os raciocinios e decide qual decisao e mais coerente com a persona, marcando divergencias.

### 3.3 Camada 3: Coletor de metricas (P5: diversidade quantitativa)
- Para cada estagio do funil (awareness, interest, agendamento):
  - Distribuicao de decisoes dos N modelos
  - Entropia de Shannon: `H = -sum(p_i * log2(p_i))`
  - Pairwise disagreement: % de pares (i,j) com decisao_i != decisao_j
  - KL divergence entre distribuicao do ensemble e distribuicao do baseline
- Teste de permutacao: H_exercito > H_baseline com p<0.05

## 4. Schema de decisao (P0.1: contrato)

Cada modelo retorna JSON estruturado (pydantic valida):

```python
class DecisaoPersona(BaseModel):
    decisao: Literal["visualizou", "clicou", "agendou", "ignorou"]
    wtp: float  # willingness to pay, R$
    sentimento: float  # -1.0 a 1.0
    objecoes: list[str]  # categorias: budget, timing, existing_solution, skepticism, complexity, need_lack
    confianca: float  # 0.0 a 1.0, auto-avaliacao do modelo
    raciocinio: str  # 1-3 frases justificando
    modelo: str  # nome do modelo que respondeu (preenchido pelo orquestrador)
```

Sintetizador retorna:

```python
class DecisaoAggregada(BaseModel):
    decisao_final: Literal["visualizou", "clicou", "agendou", "ignorou"]
    wtp_medio: float
    sentimento_medio: float
    objecoes_consolidadas: list[str]
    divergence_score: float  # 0=unanime, 1=split total
    concordancia: list[dict]  # [{modelo_a, modelo_b, concordam: bool}]
    confianca_agregada: float
    raciocinio_sintese: str
```

## 5. Ensemble de modelos com papeis (P1: heterogeneidade)

| Papel cognitivo | Modelo | Provider gocat | Razao do papel |
|------------------|--------|----------------|----------------|
| Pragmatico / orcamento | `gpt-4o` (ou `openai/gpt-4o` via openrouter) | github ou openrouter | GPT-4o foca em viabilidade financeira (relatorio) |
| Conservador / risco tecnico | `DeepSeek-V3.1` (ou `deepseek/deepseek-chat-v3.1`) | sambanova ou openrouter | DeepSeek foca em profundidade tecnica (relatorio) |
| Conversacional / prova social | `llama-3.3-70b-versatile` | groq | Llama foca em aspectos praticos/conversacionais (relatorio) |

Nao aleatorizar: cada persona e processada pelos 3 modelos com papéis fixos. AI Council mostra que parear perspectiva <-> modelo sustenta o desacordo. Roteamento round-robin aleatorio reintroduz homogeneidade.

Sintetizador: `gpt-4o-mini` (frontier barato, via openrouter).

## 6. Benchmark de calibracao (P4: calibracao externa)

Proxy publico (evidencia nivel B, declarar limitacao):
- Conversao geral B2B Brasil: **2-8%** (Sirius 2026, PowerGO 2026)
- Cold outreach -> agendamento: **1-8%** (Touchstone, StealthAgents, eesier)
- WhatsApp positive reply: **10-20%** (eesier)

Criterio de aceitacao do eval:
1. **Calibracao**: mediana da conversao geral da simulacao dentro de [2%, 8%]
2. **Diversidade**: entropia do ensemble > entropia do melhor baseline (p<0.05, permutacao)
3. **Coerencia**: >= 90% das decisoes com `confianca >= 0.6` e `raciocinio` nao-vazio

Limitacao declarar: proxy global, nao especifico de seguranca patrimonial em SLZ. Quando EMIVE tiver dados reais, recalibrar.

## 7. Baseline de modelo unico (obrigatorio)

Rodar o MESMO cenario SLZ-C 3 vezes, cada vez com 1 modelo so:
- Baseline GPT-4o: todas as 30 personas processadas so por gpt-4o
- Baseline DeepSeek: todas as 30 personas so por DeepSeek-V3.1
- Baseline Llama: todas as 30 personas so por llama-3.3-70b-versatile

Sem baseline, nao da provar que o exercito reduz viés. O relatorio atual compara contra "cenarios anteriores" nao especificados.

## 8. Escala estatistica (P6: power)

- Piloto: N=30 personas x 3 seeds = 90 runs por condicao (4 condicoes: ensemble + 3 baselines)
- Producao: N=300 personas x 3 seeds = 900 runs por condicao
- Reportar IC95% (bootstrap, 10000 resamples) para cada taxa de conversao
- Power analysis: para detectar diferenca de 3pp entre ensemble e baseline com 80% power, N~=300 por condicao
- Piloto N=30 serve para validar pipeline e estimar custo antes de escalar

## 9. Validacao cruzada de coerencia (P7)

Amostra de 10% das decisoes auditadas por 1 modelo frontier diferente do sintetizador (ex: `claude` se disponivel, senao `gpt-4o` se o sintetizador for `gpt-4o-mini`).
O auditor pontua coerencia 0..1 sem ver o modelo de origem.
Rejeitar decisoes com score < 0.5 (reprocessar ou marcar como ruido).

## 10. A/B test de oferta (Fase 3)

- Variante A: pitch tecnico atual ("sensores de vibracao e IA")
- Variante B: pitch financeiro proposto ("protecao do estoque contra arrombamento")
- N=300 em cada, comparar conversao com IC95%
- Diferenca significativa (IC95% nao inclui 0) = recomendar B

## 11. Mapa de objecoes ponderado (Fase 3)

Sair de "3 categorias qualitativas" para frequencia x impacto:
- Para cada categoria de objecao: % de personas que a citaram
- Correlacao entre citar a objecao e nao-converter (phi coefficient)
- Priorizar objecao com maior (frequencia x correlacao_negativa)

## 12. Empacotamento ponytail (P8)

Estrutura de arquivos (minimo):

```
simulacao-multi-agent/
  simulation_army_v2.py          # ~250 linhas: pipeline ensemble + agregacao + metricas
  scenarios_v2/
    slz-c-army.yaml              # 1 config: personas, oferta, ensemble, benchmark ranges
  eval/
    simulation_army_eval.py      # 1 eval pytest: 3 checks (calibracao, diversidade, coerencia)
  docs/
    BLUEPRINT.md                 # este arquivo
    INVENTARIO.md
    FRAMEWORKS.md
    GOCAT-INTEGRATION.md
  README.md
  ROADMAP.md
```

CLI:
```bash
python -m simulation_army_v2 run --scenario scenarios_v2/slz-c-army.yaml --n 30 --seed 42
python -m simulation_army_v2 baseline --scenario scenarios_v2/slz-c-army.yaml --model gpt-4o --n 30
python -m simulation_army_v2 ab-test --scenario scenarios_v2/slz-c-army.yaml --variant-a pitch_tecnico --variant-b pitch_financeiro --n 300
```

Nada mais. Sem framework abstrato, sem plugins, sem 10 arquivos. Se um segundo cenario surgir, generaliza-se; ate la, YAGNI.

## 13. Ordem de execucao

```
P0.1 (schema pydantic) -> P0.2 (ensemble papeis no config) -> P0.3 (benchmark ranges no config)
  -> P1.3 (baseline modelo unico primeiro!) -> P1.1 (pipeline ensemble) -> P1.2 (metricas diversidade)
  -> P2.2 (eval pytest) -> P2.1 (N=300) -> P2.3 (auditoria coerencia)
  -> P3.1 (A/B test) -> P3.2 (objecoes ponderadas) -> P3.3 (empacotar CLI)
```

## 14. Criterio de parada antecipada

Se P1.2 mostrar que entropia do ensemble ~= baseline (sem ganho de diversidade, p>0.05), **PARAR** e reportar que a hipotese foi refutada. Nao continuar para Fase 2/3. Isto e o principio P5 + honestidade factual.

Se P2.2 (eval) score < 0.5 apos 3 iteracoes, **PARAR** e reportar que a metodologia nao e defensavel com os modelos/providers disponiveis. Nao inflar resultados.

## 15. Riscos e limitacoes (declarar explicitamente)

| Risco | Mitigacao |
|-------|-----------|
| Benchmark publico != mercado SLZ/seguranca patrimonial | Declarar como hipotese nivel B. Recalibrar com dados reais EMIVE quando disponiveis |
| Custo 4.2x tokens (Council Mode) | Estimar custo antes de N=300. Piloto N=30 primeiro |
| Modelos convergem mesmo heterogeneos (RLHF compartilhado) | Metrica P1.2 detecta. Se entropia ~= baseline, exército nao ajuda |
| Personas sinteticas nao representam minorias (PSII, WVS) | Documentar limitacao. Nao claim sobre subgrupos especificos de SLZ |
| 1 dos 3 providers cai | Ensemble prossegue com 2, divergence_score alto, logar |
| Sintetizador viesado | Auditoria P2.3 com modelo de vendor diferente |
