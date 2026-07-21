# Roadmap: Simulation Army v2

Data: 2026-07-19
Status: design aprovado, pronto para implementar

## Visao

Transformar o "exercito de IAs" de round-robin aleatorio (estado atual do gocat) em ensemble heterogeneo com agregacao estruturada, calibracao contra benchmark publico, e metrica de diversidade estatistica. 3 fases, 12 passos.

## Fase 0: Fundacao (1 dia)

**Objetivo**: tornar a metodologia defensavel e reproduzivel antes de escalar.

| Passo | Entrega | Criterio de conclusao |
|-------|---------|----------------------|
| P0.1 | Schema pydantic `DecisaoPersona` + `DecisaoAggregada` | `pydantic` valida schema sem erro |
| P0.2 | Config `scenarios_v2/slz-c-army.yaml` com ensemble de 3 papeis | YAML carrega, 3 modelos mapeados |
| P0.3 | Benchmark ranges no config: conversao [2%, 8%], agendamento [1%, 8%] | Ranges declarados com fonte (Sirius, Touchstone, eesier) |

**Checkpoint Fase 0**: config carrega, schema valida. Nada roda ainda.

## Fase 1: Motor de simulacao com agregacao (2-3 dias)

**Objetivo**: substituir o "distribui concorrentemente" vago por pipeline mensuravel.

| Passo | Entrega | Criterio de conclusao |
|-------|---------|----------------------|
| P1.3 | Baseline modelo unico: rodar SLZ-C com so GPT-4o, so DeepSeek, so Llama (N=30 cada) | 3 JSONs de saida, 3 taxas de conversao |
| P1.1 | Pipeline ensemble: `simulation_army_v2.py` com fan-out async + sintetizador | 1 run N=30 produz decisoes agregadas + divergence_score |
| P1.2 | Metricas de diversidade: entropia, KL, pairwise disagreement vs baseline | Teste de permutacao p<0.05 OU refutacao documentada |

**Checkpoint Fase 1**: ensemble roda end-to-end, metricas calculadas.

**Criterio de parada antecipada**: se P1.2 mostrar entropia do ensemble ~= baseline (p>0.05), PARAR. Hipotese refutada. Reportar e nao continuar para Fase 2.

## Fase 2: Validacao cientifica (2 dias)

**Objetivo**: claim defensavel de "mais realista" com dados.

| Passo | Entrega | Criterio de conclusao |
|-------|---------|----------------------|
| P2.2 | Eval pytest `eval/simulation_army_eval.py`: 3 checks (calibracao, diversidade, coerencia) | `pytest -v` passa, score >= 0.8 |
| P2.1 | Escala N=300 x 3 seeds, IC95% (bootstrap) | Relatorio com IC95% por taxa de conversao |
| P2.3 | Auditoria de coerencia: 10% das decisoes auditadas por modelo frontier diferente | % rejeitadas < 10% |

**Checkpoint Fase 2**: eval score >= 0.8, IC95% reportado, auditoria passa.

**Criterio de parada antecipada**: se P2.2 score < 0.5 apos 3 iteracoes, PARAR. Metodologia nao defensavel com modelos/providers disponiveis.

## Fase 3: Aplicacao pratica + Empacotamento (2 dias)

**Objetivo**: gerar acao real para EMIVE/SLZ-C e empacotar como framework reutilizavel.

| Passo | Entrega | Criterio de conclusao |
|-------|---------|----------------------|
| P3.1 | A/B test de oferta: pitch tecnico vs pitch financeiro, N=300 cada | Diferenca de conversao com IC95%, recomendacao |
| P3.2 | Mapa de objecoes ponderado: frequencia x impacto (phi) | Ranking de objecoes por prioridade |
| P3.3 | CLI empacotada: `python -m simulation_army_v2 run/baseline/ab-test` | 3 comandos funcionais, README atualizado |

**Checkpoint Fase 3**: A/B test tem vencedor declarado (ou empate tecnico documentado), CLI funciona.

## Milestones

| Milestone | Fases | Entrega | Criterio de saida |
|-----------|-------|---------|-------------------|
| M1: Pipeline funcional | Fase 0 + Fase 1 | Ensemble roda N=30, metricas calculadas | P1.2 passa OU refutacao documentada |
| M2: Validado cientificamente | Fase 2 | Eval >= 0.8, IC95%, auditoria | P2.3 passa |
| M3: Aplicacao pratica | Fase 3 | A/B test + objecoes + CLI | P3.3 passa |

## Dependencias entre passos

```
P0.1 -> P0.2 -> P0.3
              |
              v
P1.3 (baseline primeiro!) -> P1.1 -> P1.2
                                    |
                                    v (se nao refutado)
                              P2.2 -> P2.1 -> P2.3
                                                |
                                                v
                                          P3.1 -> P3.2 -> P3.3
```

P1.3 (baseline) DEVE vir antes de P1.1 (ensemble). Sem baseline, nao da provar reducao de vies.

## Criterios de parada (globais)

1. **Refutacao de diversidade** (apos P1.2): se entropia do ensemble ~= baseline (p>0.05), parar. Hipotese refutada.
2. **Eval insuficiente** (apos P2.2): se score < 0.5 apos 3 iteracoes, parar. Metodologia nao defensavel.
3. **Custo proibitivo** (antes de P2.1): se estimativa de custo N=300 x 4.2x tokens > orcamento, parar e pedir aprovacao.
4. **Provider indisponivel**: se 2+ dos 3 modelos do ensemble ficarem indisponiveis e nao houver substituto de vendor distinto, parar. Heterogeneidade e pre-requisito.

## Fora de escopo (YAGNI explicito)

- UI web nova (launch-simulation tem Next.js, market-fish tem Streamlit)
- Framework de multi-agente novo (Autogen, CrewAI): overkill para 1 pipeline
- DB novo: gocat ja tem SQLite
- RAG: nao temos necessidade, temos pesquisa em arquivos
- Generalizacao para outros cenarios antes de SLZ-C funcionar: YAGNI

## Riscos

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|--------------|---------|-----------|
| Benchmark publico != mercado SLZ | Alta | Medio | Declarar limitacao, recalibrar com dados EMIVE |
| Custo 4.2x tokens | Media | Alto | Piloto N=30 primeiro, estimar antes de N=300 |
| Modelos convergem (RLHF compartilhado) | Media | Alto | P1.2 detecta, parar se refutado |
| 1 provider cai | Alta | Baixo | Ensemble prossegue com 2, logar |
| Sintetizador viesado | Baixa | Medio | P2.3 auditoria com vendor diferente |
