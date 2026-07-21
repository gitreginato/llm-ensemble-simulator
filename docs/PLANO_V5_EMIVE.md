# Plano: Simulation Army v5 - EMIVE Sao Luis-MA (Realista)

**Data:** 2026-07-20
**Status:** Aguardando aprovacao do usuario
**Fontes autorizadas:** APENAS os 3 documentos em /home/lucas/Projetos/slz_seguranca_treinamento/ + dados reais da sessao + pesquisa de bairros de Sao Luis
**Mensalidade base:** R$ 294/mes (valor fornecido pelo usuario, plano base)
**N:** a definir (foco primeiro na precisao do simulador)

---

## Diagnostico: Onde estamos agora

### Dados reais coletados nesta sessao (evidencia S)

**Simulacao atual (62 personas, so loja_roupas):**
- Conversao media: 15% (9/62 agendaram)
- Driver #1: `recent_event=theft` -> 100% agendaram (8/8)
- Driver #2: `has_existing_security=none` -> 31% agendaram (4/13)
- Driver #3: `risk_profile=crisis_driven` -> 33% converte (vs 4% pragmatic)
- Sem roubo recente: 3% converte (2/72)
- Com `full_system` + satisfacao >= 7: 0% converte

**Analise multi-nicho (80 requests, 8 nichos, N=10 cada):**
- loja_roupas: 50% conversao (WTP R$ 651)
- bar: 20% (WTP R$ 451)
- loja_calcados: 10% (WTP R$ 464)
- autopecas: 10% (WTP R$ 493)
- mercearia: 10% (WTP R$ 321)
- farmacia: 0% (WTP R$ 778, todos com existing_solution)
- hamburgueria: 0% (WTP R$ 638, todos com existing_solution)
- oficina: 0% (WTP R$ 422, todos com existing_solution)

**Performance dos modelos (ensemble v4, 120 requests):**
- devin: 100% sucesso (11/11)
- kilocode: 93% sucesso (51/55)
- gocat: 54% sucesso (29/54) - 3 modelos sempre 503

### O que o documento da empresa diz (fonte unica de verdade)

**De AGREGADO_EMPRESA.md:**
- SLZ = franqueada homologada EMIVE (maior da America Latina)
- 3 pilares: Inibicao (placa = 36x mais seguranca), Deteccao (sensores + cameras), Acao (Central 24h)
- Hardware: Central Inviolavel (4 canais: Wifi, Ethernet, GPRS, telefone), Sensor Magnetico (acelerometro 5 niveis, anti-falso-alarme), Sensor Presenca, Controle Remoto (4 botoes, criptografado), Camera Interna Full HD 360 com audio bidirecional, Camera Externa IP67 visao noturna colorida, Teclado Smart (senha de coacao), Sirene Sem Fio (repetidor de sinal)
- Software: App EMIVE (arme/desarme remoto, relatorios, cameras, deslocamento monitorado, alertas emergencia, notificacao esquecimento)
- Tom de voz: seria mas amigavel, objetiva mas nao tecnica, assertiva mas nao pretensiosa, realista mas acolhedora, pontual mas empatica, agil mas atenciosa, segura mas nao arrogante, sem sensacionalismo
- Regra ABSOLUTA: "Nunca explique detalhes tecnicos ou precos por telefone"
- Scripts: Mercado A (conhecidos, foco em feedback), Mercado C Avisado (indicacao avisada), Mercado C Nao Avisado (indicacao fria)
- Objecao "nao sei se estou interessado": usar recomendante como gancho

**De BLUEPRINT_SIMULACOES.md:**
- 5 cenarios de treinamento (CEN-01 a CEN-05)
- Objecoes comuns reais: "muito caro mensalidade", "ja tenho cameras pelo celular", "moro em apartamento nao precisa", "cachorro dispara alarme", "furadeiras e fios na casa nova"
- Variaveis: resistencia do lead (baixa/media/alta), canal (ligacao/WhatsApp)
- 5 competencias avaliadas: conexao/rapport, foco no agendamento, geracao de curiosidade, contorno de objecoes, fechamento/compromisso
- Regra: se vendedor explicar tecnica/preco por telefone, cliente perde interesse

### Gaps criticos (o que torna o simulador impreciso hoje)

1. **Mensalidade nao existe no modelo**: simulacao so considera "visita R$ 1". EMIVE cobra R$ 294/mes. Sem isso, WTP nao reflete realidade e a objecao "muito caro pagar mensalidade" (do blueprint) nunca aparece.
2. **Bairros de Sao Luis nao mapeados**: cenario usa bairros genericos. Sao Luis e policentrica (Turu 4813 empresas, Renascenca 3865, Calhau 3789). Bairros perigosos (Cidade Operaria, Coroadinho, Vila Embratel) vs comerciais (Calhau, Cohama, Renascenca).
3. **Sazonalidade real de Sao Luis**: Sao Joao (junho), Natal (dezembro) afetam fluxo e risco.
4. **Mensagem generica**: oferta so fala "estoque de vestuario". Bar, farmacia, hamburgueria, oficina nao se identificam com a dor.
5. **Sem validacao cruzada**: sintetizador nao e auditado por modelo neutro.
6. **Hardware EMIVE nao modelado**: o documento descreve 8 equipamentos com features especificas (acelerometro anti-falso-alarme, 4 canais de redundancia, senha de coacao, audio bidirecional). O prompt nao menciona nada disso.
7. **Scripts da empresa nao integrados**: o blueprint tem 3 scripts de abordagem (Mercado A/B/C) e 5 cenarios de treinamento. A simulacao nao usa nenhum.
8. **Tom de voz da marca ausente**: o documento define 8 atributos de tom. O prompt do sintetizador nao os segue.
9. **Canal de contato nao modelado**: blueprint diferencia ligacao vs WhatsApp. Simulacao so tem word_of_mouth.
10. **Resistencia do lead nao modelada**: blueprint tem 3 niveis (baixa/media/alta). Simulacao nao usa.

---

## Plano: 4 frentes em 2 fases

### FASE 1: Precisao do simulador (deterministico)

#### 1.1 Modelar mensalidade R$ 294 no cenario

O documento diz "nunca explique precos por telefone" mas o cliente PRECISA saber que existe mensalidade para ter a objecao "muito caro pagar mensalidade" (que esta no blueprint). Modelar:

```yaml
pricing:
  visit_fee: 1.00              # visita tecnica (ja existe)
  monthly_fee: 294.00           # plano base EMIVE (valor do usuario)
  installation: 0               # sem custo de instalacao (comodato, conforme documento)
  contract_model: "monthly"     # sem fidelidade forcada (documento nao menciona fidelidade)
  price_disclosure_rule: "never_on_phone"  # regra do blueprint
```

No `BusinessProfile`, adicionar `monthly_budget_security` derivado do `wtp_brl`. Se `monthly_budget < 294`, objecao `budget` e automatica. Se `monthly_budget >= 294`, cliente pode pagar mas pode ter outras objecoes.

O prompt deve MENCIONAR que existe mensalidade (para gerar a objecao real) mas sem dar o valor (regra do blueprint: "nunca explique precos por telefone"). O cliente reage baseado no seu budget mensal.

**Arquivos:** `src/advanced_simulation.py` (BusinessProfile + generate_personas), `scenarios_v2/slz-c-army-v5.yaml`, `simulation_army_v2/ensemble.py` (USER_PROMPT_TEMPLATE)

#### 1.2 Modelar hardware EMIVE no prompt

O documento descreve 8 equipamentos com features especificas. O prompt atual so menciona "sensores de vibracao" e "cameras com visao noturna". Adicionar features reais que resolvem objecoes do blueprint:

| Equipamento (do documento) | Objecao que resolve (do blueprint) |
|---|---|
| Sensor Magnetico com acelerometro 5 niveis | "cachorro dispara alarme" (anti-falso-alarme) |
| Tecnologia sem fio criptografada | "furadeiras e fios na casa nova" (instalacao sem obra) |
| Central Inviolavel 4 canais (Wifi, Ethernet, GPRS, telefone) | "se cortarem a internet funciona?" (redundancia) |
| Camera com audio bidirecional | "ja tenho cameras pelo celular" (diferenca: audio + monitoramento 24h) |
| Sirene 120dB + placa EMIVE | "placa gera 36x mais seguranca" (inibicao) |
| Teclado Smart com senha de coacao | "e se me assaltarem na entrada?" (coacao silenciosa) |
| App EMIVE com deslocamento monitorado | "quero ver pelo celular" (app + extras) |
| Bateria interna 10h (No-Break) | "se faltar luz funciona?" (autonomia) |

O prompt nao lista tecnicas (regra: "objetiva mas nao tecnica"). Menciona o BENEFICIO que resolve a objecao.

**Arquivos:** `simulation_army_v2/ensemble.py` (USER_PROMPT_TEMPLATE com beneficios mapeados)

#### 1.3 Mapear bairros reais de Sao Luis

Substituir bairros genericos por bairros reais com perfil de risco (fontes: G1, SSP-MA, LeadJet, artigos academicos):

```python
BAIRROS_SLZ = {
    # Alto fluxo comercial, menor risco relativo
    "Calhau": {"empresas": 3789, "risco": "medio", "perfil": "comercial_alto"},
    "Cohama": {"empresas": 2800, "risco": "medio", "perfil": "comercial_alto"},
    "Renascenca": {"empresas": 3865, "risco": "baixo", "perfil": "comercial_alto"},
    "Turu": {"empresas": 4813, "risco": "medio", "perfil": "comercial_medio"},
    "Centro": {"empresas": 3259, "risco": "alto", "perfil": "comercial_historico"},
    "Sao Cristovao": {"empresas": 1500, "risco": "alto", "perfil": "comercial_medio"},
    "Vinhais": {"empresas": 1200, "risco": "medio", "perfil": "residencial_comercial"},
    "Olho DAgua": {"empresas": 900, "risco": "alto", "perfil": "comercial_medio"},
    "Ponta do Farol": {"empresas": 700, "risco": "medio", "perfil": "comercial_alto"},
    "Joao Paulo": {"empresas": 1100, "risco": "alto", "perfil": "comercial_medio"},
    # Periferia, risco alto (CVLI concentrado aqui)
    "Cidade Operaria": {"empresas": 800, "risco": "muito_alto", "perfil": "periferia"},
    "Coroadinho": {"empresas": 600, "risco": "muito_alto", "perfil": "periferia"},
    "Vila Embratel": {"empresas": 500, "risco": "muito_alto", "perfil": "periferia"},
}
```

Bairros de risco alto/muito alto aumentam probabilidade de `recent_event=theft`. Bairros comerciais altos aumentam WTP. Fonte: LeadJet (95.066 empresas, distribuicao por bairro) + SSP-MA (CVLI concentrado em Cidade Operaria, Coroadinho, Vila Embratel, 42% das 4104 ocorrencias 2014-2019) + G1 (arrombamentos reais em Maranhao Novo, Joao Paulo, Cohama, Parque Jair, Vila Embratel).

**Arquivos:** `src/advanced_simulation.py` (BAIRROS_SLZ + generate_personas)

#### 1.4 Integrar scripts e cenarios do blueprint

O blueprint define 3 scripts de abordagem e 5 cenarios de treinamento. Integrar no simulador:

**Canal de contato (do blueprint):**
```yaml
channels:
  - phone_call      # ligacao telefonica (scripts 1, 2, 3 do AGREGADO)
  - whatsapp        # mensagens curtas (blueprint: "gatilhos de curiosidade rapidos")
```

**Mercado / nivel de frieza (do AGREGADO + blueprint):**
```yaml
lead_temperature:
  mercado_a: "conhecido do vendedor, foco em feedback"
  mercado_c_avisado: "indicacao avisada, foco em conexao"
  mercado_c_nao_avisado: "indicacao fria, quebrar gelo com amigo em comum"
```

**Resistencia do lead (do blueprint):**
```yaml
lead_resistance:
  baixa: "aceita agendamento apos 1 contorno de objecao"
  media: "2 objecoes firmes (preco + utilidade) antes de aceitar"
  alta: "ocupado, resistente, exige fortes argumentos de conexao"
```

**5 cenarios de treinamento (do blueprint):**
- CEN-01: Prospeccao Mercado A
- CEN-02: Lead Frio Mercado C Nao Avisado
- CEN-03: Dono de Comercio (indoor)
- CEN-04: Objeção de Preco (Mensalidade)
- CEN-05: Objeção Tecnica (Pet/Fios)

**Arquivos:** `scenarios_v2/slz-c-army-v5.yaml`, `simulation_army_v2/ensemble.py` (USER_PROMPT_TEMPLATE com canal + mercado + resistencia)

#### 1.5 Sazonalidade real de Sao Luis

```python
SAZONALIDADE_SLZ = {
    "alta": ["junho", "dezembro"],      # Sao Joao, Natal
    "media": ["janeiro", "fevereiro", "marco", "abril", "maio", "julho", "agosto", "setembro", "outubro", "novembro"],
}
```

Em junho (Sao Joao): mais fluxo, mais caixa, mais risco. Em dezembro (Natal): idem. Em novembro (Black Friday): pico de vendas no varejo.

**Arquivos:** `src/advanced_simulation.py` (generate_personas ajusta season baseado no mes)

---

### FASE 2: Validacao e nichos

#### 2.1 Auditoria cruzada via Devin (adaptative mode)

Implementar validador de coerencia que roda em 10% das respostas do sintetizador:
- Devin CLI no modo adaptative (consome cota do usuario, mas ok para avaliacao)
- Verifica: decisao final coerente com decisoes individuais? divergence score correto? objecoes consolidadas refletem as individuais? tom de voz segue os 8 atributos da marca?
- Se incoerente, marca no JSON com `audit_flag: "incoerente"` e re-roda sintese
- Avalia tambem as 5 competencias do blueprint: conexao/rapport, foco no agendamento, geracao de curiosidade, contorno de objecoes, fechamento/compromisso

**Arquivos:** `simulation_army_v2/ensemble.py` (funcao `_audit_synthesis` via devin_adapter), `tests_v2/test_audit.py`

#### 2.2 Expandir nichos com dor real mapeada

Nichos prioritarios para EMIVE em Sao Luis (baseado em dados de criminalidade G1/SSP-MA + fluxo comercial LeadJet):

| Nicho | Dor real em SLZ | Mensagem adaptada |
|---|---|---|
| loja_roupas | Arrombamento noturno, vitrine exposta (G1: loja no Maranhao Novo) | "protecao de vitrine e estoque, sensores de vibracao nas portas de aco" |
| loja_calcados | Mesmo que roupas, vitrine exposta | Similar a roupas |
| bar | Movimento noturno, alcool, caixa, saida de clientes (Cohama, Calhau) | "monitoramento 24h do caixa e saida, cameras com audio bidirecional" |
| autopecas | Estoque valioso (pecas), ferramentas, arrombamento (Parque Jair) | "sensores de vibracao no estoque, cameras externas IP67" |
| mercearia | Estoque perecivel, furto de clientes, caixa | "cameras no caixa e corredores, alarme noturno" |
| farmacia | Medicamentos controlados, compliance, furto | "controle de acesso, cameras, relatorios auditaveis" |
| hamburgueria | Caixa noturno, saida de caixa, movimento | "cameras no caixa e cozinha, alarme noturno" |
| oficina | Ferramentas caras, veiculos de clientes, arrombamento | "sensores de vibracao nas portas, cameras externas" |

**Arquivos:** `scenarios_v2/slz-c-army-v5-{nicho}.yaml` (8 arquivos), `simulation_army_v2/ensemble.py` (USER_PROMPT_TEMPLATE dinamico)

#### 2.3 Rodar simulacao v5 (N a definir)

Para cada nicho:
- Personas com bairros reais, sazonalidade, mensalidade R$ 294, hardware EMIVE, scripts do blueprint
- Ensemble 22 modelos (ou baseline 1 modelo se custo proibitivo)
- Checkpoint incremental (ja implementado)
- Dashboard por nicho
- Auditoria cruzada via Devin em 10% das sinteses

**N a definir** apos FASE 1 pronta e validada com N=2.

#### 2.4 Roteiros de conversa (so apos consolidar simulacao)

So depois que a simulacao v5 estiver consolidada com todos os vieses, dados e afins:
- Agregar resultados de todos os nichos
- Identificar padroes de conversao por nicho, bairro, risk_profile, recent_event
- Criar roteiros baseados nos dados reais (nao em achismo)
- 8 nichos * 2 canais (ligacao + WhatsApp) * 3 mercados (A, C avisado, C nao avisado)
- Matriz de objecoes com respostas baseadas no blueprint da empresa

**Arquivos:** `roteiros/` (so apos FASE 2.3 completa)

---

## Ordem de execucao (dependencias)

```
FASE 1: Precisao do simulador (deterministico, sem rede)
  1.1 Mensalidade R$ 294 no YAML + BusinessProfile    [2h]
  1.2 Hardware EMIVE no prompt (beneficios mapeados)   [1h]
  1.3 Bairros reais de Sao Luis                        [2h]
  1.4 Scripts + cenarios + canal + resistencia          [2h]
  1.5 Sazonalidade Sao Luis                             [30min]
  -> Validar com testes unitarios + N=2 por nicho

FASE 2: Validacao e nichos (precisa FASE 1)
  2.1 Auditoria cruzada via Devin adaptative            [2h]
  2.2 8 cenarios YAML por nicho + prompt dinamico       [3h]
  2.3 Rodar v5 (N a definir)                            [a definir]
  2.4 Roteiros (so apos 2.3 consolidado)               [3h]
```

**Tempo total FASE 1:** ~7h (sem run, so construcao + testes unitarios)
**Tempo total FASE 2 (sem run):** ~5h
**Tempo run v5:** depende do N (a definir)

---

## Riscos e mitigacoes

| Risco | Prob | Impacto | Mitigacao |
|---|---|---|---|
| gocat 503 nos 3 modelos problematicos | 100% | Medio | Remover do cenario v5 |
| kilocode timeout em modelos pesados | 30% | Baixo | Ja tem backoff adaptativo |
| Devin adaptative consome cota | Certo | Baixo | So 10% das sinteses, usuario autorizou |
| Mensalidade R$ 294 muda | Baixo | Medio | Usuario confirmou valor |
| Bairros sem dados precisos | Baixo | Baixo | LeadJet + SSP-MA + G1 tem dados |
| Sintetizador incoerente | Media | Medio | Auditoria cruzada via Devin (2.1) |

---

## Decisoes que preciso da sua aprovacao

1. **Mensalidade**: R$ 294/mes fixo (plano base). Confirmado pelo usuario. So um plano ou tem variacoes?
2. **Instalacao**: R$ 0 (comodato, sem custo de instalacao). Correto?
3. **Nichos**: 8 nichos (roupas, calcados, bar, autopecas, mercearia, farmacia, hamburgueria, oficina). Quer adicionar/remover algum?
4. **N**: definir apos FASE 1 pronta. Concorda?
5. **Auditoria**: Devin adaptative em 10% das sinteses. Confirmado pelo usuario.
6. **Roteiros**: so apos simulacao consolidada. Confirmado pelo usuario.
7. **Foco**: construir simulador preciso primeiro (FASE 1), depois validar e escalar (FASE 2). Concorda?

---

## Entregaveis finais

1. **Simulador v5 preciso**: cenario com mensalidade R$ 294, hardware EMIVE, bairros de SLZ, scripts do blueprint, sazonalidade
2. **Auditoria cruzada**: validacao via Devin adaptative em 10% das sinteses
3. **Simulacao v5**: N personas por nicho com dados estruturados (JSON + dashboard)
4. **Relatorio consolidado**: ranking de nichos por conversao, WTP, objecoes, bairros
5. **Roteiros de conversa**: so apos simulacao consolidada, baseados em dados reais
6. **Mapa de prospeccao**: bairros prioritarios por nicho para scrap no Maps
7. **Documentacao**: AGENTS.md atualizado com aprendizados
