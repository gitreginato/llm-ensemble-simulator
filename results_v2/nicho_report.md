# Analise de Nichos: Que tipos de loja mais agendam?

**Data:** 2026-07-20
**Metodo:** Baseline 1 modelo (command-a-03-2025 via gocat), N=10 por nicho, seed=42
**Total:** 80 requests, 80 OK (100% sucesso), ~3min runtime, $0 custo
**Oferta:** Sistema de Seguranca Inteligente EMIVE (visita tecnica R$ 1)

## Ranking de Conversao por Nicho

| Rank | Nicho | Conversao | Agendaram | WTP medio | Latencia |
|---|---|---|---|---|---|
| 1 | **loja_roupas** | **50%** | 5/10 | R$ 651 | 3.7s |
| 2 | **bar** | **20%** | 2/10 | R$ 451 | 3.7s |
| 3 | loja_calcados | 10% | 1/10 | R$ 464 | 3.0s |
| 3 | autopecas | 10% | 1/10 | R$ 493 | 3.4s |
| 3 | mercearia | 10% | 1/10 | R$ 321 | 3.3s |
| 6 | farmacia | 0% | 0/10 | R$ 778 | 3.9s |
| 6 | hamburgueria | 0% | 0/10 | R$ 638 | 3.5s |
| 6 | oficina | 0% | 0/10 | R$ 422 | 4.5s |

## Driver #1: Roubo Recente (theft)

**100% dos que agendaram tinham `recent_event=theft` OU `has_existing_security=none/diy_cameras`.**

| Fator | Agendaram | Nao agendaram |
|---|---|---|
| recent_event=theft | 8/8 (100%) | 0 |
| recent_event != theft | 2/72 (3%) | 70 |
| has_existing_security=none | 4/13 (31%) | 9 |
| has_existing_security=diy_cameras | 2/24 (8%) | 22 |
| has_existing_security=alarm_monitored | 1/11 (9%) | 10 |
| has_existing_security=full_system | 1/14 (7%) | 13 |

**Insight:** Roubo recente e o gatilho universal. Sem roubo, quase ninguem agenda.

## Driver #2: Perfil de Risco

| Risk Profile | Conversao | WTP medio |
|---|---|---|
| crisis_driven | 33% (5/15) | R$ 657 |
| innovator | 20% (2/10) | R$ 745 |
| conservative | 10% (2/20) | R$ 521 |
| pragmatic | 7% (3/35) | R$ 521 |

**Insight:** crisis_driven converte 5x mais que pragmatic. Sao o alvo prioritario.

## Por que alguns nichos nao convertem?

### farmacia (0%, WTP alto R$ 778)
- **Objecao dominante:** existing_solution (10/10)
- **Causa:** farmacias ja tem alarme monitorado ou sistema completo (satisfacao 6-8/10)
- **Narrativa:** "ja possui sistema de alarme monitorado com satisfacao razoavel"
- **Mismatch:** oferta foca em "vitrine exposta" e "estoque de vestuario" - farmacia tem vitrine mas nao de roupas
- **WTP alto mas nao converte:** dinheiro nao e o problema, e a satisfacao com o atual

### hamburgueria (0%, WTP R$ 638)
- **Objecao dominante:** existing_solution (8/10)
- **Causa:** hamburguerias ja tem sistema completo (satisfacao 7-8/10)
- **Narrativa:** "ja possui sistema de seguranca completo e esta satisfeita"
- **Mismatch:** oferta menciona "portas de aco" e "vitrine" - hamburgueria tem caixa e cozinha, nao vitrine

### oficina (0%, WTP R$ 422)
- **Objecao dominante:** existing_solution (7/10)
- **Causa:** oficinas ja tem sistema completo ou DIY cameras
- **Narrativa:** "ja possui sistema de seguranca completo com satisfacao de 7/10"
- **Mismatch:** oferta fala em "estoque valioso fechado a noite" - oficina tem ferramentas e veiculos, nao "estoque"

## O Mismatch da Oferta EMIVE

A oferta atual e otimizada para **loja de roupas**:
- "protecao do estoque de vestuario contra arrombamentos noturnos nas portas de aco"
- "vitrine exposta"
- "lojista deixa estoque valioso fechado a noite"

Isso explica por que loja_roupas converte 50% e os outros nichos convertem 0-20%: **a mensagem nao fala a dor deles**.

### O que cada nicho ouve (e nao se identifica)

| Nicho | Dor real | O que a oferta diz |
|---|---|---|
| farmacia | Medicamentos controlados, furto de remedios, compliance | "estoque de vestuario" |
| hamburgueria | Caixa noturno, movimento de clientes, saida de caixa | "vitrine exposta" |
| oficina | Ferramentas caras, veiculos de clientes, arrombamento | "estoque valioso fechado" |
| bar | Movimento noturno, alcool, brigas, caixa | "portas de aco" |
| autopecas | Pecas caras, ferramentas, arrombamento noturno | "vestuario" |
| mercearia | Produtos pereciveis, furto de clientes, caixa | "vitrine" |

## Recomendacao: Nichos Prioritarios para Scrap no Maps

### Tier 1: Alto potencial (foco primario)
1. **loja_roupas** (50% conv, WTP R$ 651) - mensagem atual ja funciona
2. **bar** (20% conv, WTP R$ 451) - mensagem precisa adaptar para "movimento noturno"

### Tier 2: Potencial medio (precisa mensagem adaptada)
3. **loja_calcados** (10% conv, WTP R$ 464) - similar a roupas, vitrine exposta
4. **autopecas** (10% conv, WTP R$ 493) - estoque valioso, arrombamento
5. **mercearia** (10% conv, WTP R$ 321) - WTP baixo mas converte com theft

### Tier 3: Baixo potencial (mensagem atual nao funciona)
6. **farmacia** (0% conv, WTP R$ 778) - ja tem sistema, mismatch total
7. **hamburgueria** (0% conv, WTP R$ 638) - ja tem sistema, mismatch
8. **oficina** (0% conv, WTP R$ 422) - ja tem sistema, mismatch

### Filtro para scrap no Maps
**Priorizar lojas com indicadores de:**
- Roubo recente (noticias locais, queixas em redes sociais)
- Sem seguranca ou seguranca DIY (Google Street View: sem cameras visiveis)
- Perfil crisis_driven (area com alto indice de criminalidade)

**Evitar lojas com:**
- Sistema completo visivel (cameras profissionais, alarme)
- Cadeias/franquias (ja tem seguranca corporativa)

## Proximos Passos

1. **Adaptar mensagem por nicho** (roteiros especificos)
2. **Rodar N=30 por nicho** com mensagem adaptada para validar
3. **Scrap Google Maps** com filtros: nicho + bairro + indicadores de dor
4. **A/B test** mensagem generica vs mensagem adaptada por nicho
