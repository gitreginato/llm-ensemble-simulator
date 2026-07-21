# Relatorio FASE 0: Simulacao Programatica EMIVE Sao Luis-MA

**Data:** 2026-07-20
**N personas:** 1000
**Segmento:** distribuido
**Mes:** 7 (sazonalidade)
**Canal:** phone_call
**Mercado:** mercado_c_nao_avisado
**Tempo de execucao:** 0.365s
**Mensalidade base:** R$ 294

---

## 1. Estatisticas Globais

| Metrica | Valor |
|---|---|
| Taxa de conversao | 16.3% |
| IC 95% bayesiano | [14.2%, 18.7%] |
| MC mediana | 17.4% |
| MC P5 | 15.9% |
| MC P95 | 19.3% |
| MC desvio | 1.0% |

**Decisoes:** {'agendou': 163, 'visualizou': 807, 'ignorou': 9, 'clicou': 21}

## 2. Objecoes

| Objecao | Contagem | % |
|---|---|---|
| existing_solution | 595 | 27.6% |
| area_externa | 550 | 25.5% |
| contract_fear | 256 | 11.9% |
| skepticism | 210 | 9.7% |
| concorrencia_local | 201 | 9.3% |
| timing | 174 | 8.1% |
| complexity | 60 | 2.8% |
| need_lack | 46 | 2.1% |
| budget | 34 | 1.6% |
| ticket_alto | 29 | 1.3% |

## 3. Competencias Medias (avaliacao do pitch)

| Competencia | Score (0-10) |
|---|---|
| Conexao Rapport | 8.0 |
| Foco Agendamento | 9.0 |
| Geracao Curiosidade | 5.0 |
| Contorno Objecoes | 7.37 |
| Fechamento Compromisso | 8.0 |

## 4. Conversao por Nicho

| Nicho | N | Agendou | Conversao | IC 95% |
|---|---|---|---|---|
| consultorio_odonto | 47 | 14 | 29.8% | [18.7%, 44.2%] |
| clinica | 39 | 10 | 25.6% | [14.7%, 41.3%] |
| estacionamento | 36 | 9 | 25.0% | [13.9%, 41.3%] |
| optica | 33 | 8 | 24.2% | [13.0%, 41.2%] |
| mecanica_diesel | 42 | 10 | 23.8% | [13.6%, 38.7%] |
| autopecas | 40 | 9 | 22.5% | [12.5%, 37.7%] |
| oficina | 36 | 8 | 22.2% | [11.9%, 38.3%] |
| laboratorio | 39 | 8 | 20.5% | [10.9%, 35.8%] |
| fisioterapia | 39 | 8 | 20.5% | [10.9%, 35.8%] |
| pet_shop | 34 | 6 | 17.6% | [8.5%, 33.7%] |
| barbearia | 42 | 7 | 16.7% | [8.4%, 30.7%] |
| hamburgueria | 25 | 4 | 16.0% | [6.6%, 34.9%] |
| estudio_tatuagem | 44 | 7 | 15.9% | [8.1%, 29.4%] |
| salao | 39 | 6 | 15.4% | [7.4%, 29.9%] |
| borracharia | 36 | 5 | 13.9% | [6.2%, 28.8%] |
| farmacia | 36 | 5 | 13.9% | [6.2%, 28.8%] |
| mercadinho | 46 | 6 | 13.0% | [6.2%, 25.8%] |
| academia | 33 | 4 | 12.1% | [5.0%, 27.5%] |
| lava_jato | 42 | 5 | 11.9% | [5.3%, 25.1%] |
| clinica_veterinaria | 51 | 6 | 11.8% | [5.6%, 23.5%] |
| loja_calcados | 41 | 4 | 9.8% | [4.0%, 22.7%] |
| mercearia | 42 | 4 | 9.5% | [3.9%, 22.2%] |
| restaurante | 32 | 3 | 9.4% | [3.5%, 24.4%] |
| loja_roupas | 38 | 3 | 7.9% | [2.9%, 20.9%] |
| estetica | 33 | 2 | 6.1% | [1.9%, 19.7%] |
| bar | 35 | 2 | 5.7% | [1.8%, 18.7%] |

## 5. Conversao por Bairro

| Bairro | Risco | N | Agendou | Conversao | IC 95% |
|---|---|---|---|---|---|
| Vila Embratel | muito_alto | 16 | 7 | 43.8% | [22.9%, 66.9%] |
| Coroadinho | muito_alto | 27 | 7 | 25.9% | [13.4%, 44.9%] |
| Centro | alto | 134 | 29 | 21.6% | [15.6%, 29.4%] |
| Sao Cristovao | alto | 59 | 11 | 18.6% | [10.8%, 30.5%] |
| Olho DAgua | alto | 33 | 6 | 18.2% | [8.8%, 34.6%] |
| Calhau | medio | 159 | 27 | 17.0% | [12.0%, 23.7%] |
| Cohama | medio | 104 | 17 | 16.4% | [10.6%, 24.8%] |
| Joao Paulo | alto | 41 | 6 | 14.6% | [7.0%, 28.6%] |
| Renascenca | baixo | 145 | 20 | 13.8% | [9.2%, 20.4%] |
| Turu | medio | 172 | 22 | 12.8% | [8.6%, 18.7%] |
| Vinhais | medio | 55 | 7 | 12.7% | [6.4%, 24.1%] |
| Cidade Operaria | muito_alto | 26 | 3 | 11.5% | [4.3%, 29.3%] |
| Ponta do Farol | medio | 29 | 1 | 3.5% | [0.8%, 17.3%] |

## 6. Analise de Informacao

### 6.1 Informacao Mutua (feature ; decisao)

| Feature | MI (bits) | Interpretacao |
|---|---|---|
| recent_event | 0.1891 | driver forte |
| segment | 0.0635 | driver moderado |
| has_existing_security | 0.0184 | driver fraco |
| risk_profile | 0.0061 | driver fraco |

### 6.2 Entropia por Nicho

| Nicho | H (bits) | H norm | Distribuicao |
|---|---|---|---|
| laboratorio | 1.167 | 0.584 | {'visualizou': 28, 'agendou': 8, 'ignorou': 2, 'clicou': 1} |
| consultorio_odonto | 1.153 | 0.576 | {'visualizou': 31, 'ignorou': 1, 'agendou': 14, 'clicou': 1} |
| salao | 1.153 | 0.577 | {'visualizou': 29, 'clicou': 3, 'agendou': 6, 'ignorou': 1} |
| hamburgueria | 1.015 | 0.641 | {'visualizou': 19, 'clicou': 2, 'agendou': 4} |
| estacionamento | 0.983 | 0.62 | {'agendou': 9, 'visualizou': 26, 'clicou': 1} |
| optica | 0.983 | 0.62 | {'visualizou': 24, 'agendou': 8, 'clicou': 1} |
| mecanica_diesel | 0.945 | 0.596 | {'visualizou': 31, 'agendou': 10, 'ignorou': 1} |
| oficina | 0.937 | 0.591 | {'agendou': 8, 'visualizou': 27, 'clicou': 1} |
| fisioterapia | 0.895 | 0.565 | {'visualizou': 30, 'agendou': 8, 'clicou': 1} |
| estudio_tatuagem | 0.887 | 0.56 | {'agendou': 7, 'visualizou': 35, 'ignorou': 2} |
| loja_roupas | 0.871 | 0.549 | {'visualizou': 31, 'agendou': 3, 'clicou': 4} |
| pet_shop | 0.855 | 0.54 | {'visualizou': 27, 'agendou': 6, 'clicou': 1} |
| clinica | 0.821 | 0.821 | {'visualizou': 29, 'agendou': 10} |
| barbearia | 0.806 | 0.509 | {'visualizou': 34, 'agendou': 7, 'ignorou': 1} |
| autopecas | 0.769 | 0.769 | {'visualizou': 31, 'agendou': 9} |
| farmacia | 0.758 | 0.478 | {'visualizou': 30, 'agendou': 5, 'clicou': 1} |
| academia | 0.723 | 0.456 | {'agendou': 4, 'visualizou': 28, 'clicou': 1} |
| mercadinho | 0.705 | 0.445 | {'visualizou': 39, 'agendou': 6, 'clicou': 1} |
| restaurante | 0.645 | 0.407 | {'visualizou': 28, 'clicou': 1, 'agendou': 3} |
| mercearia | 0.613 | 0.386 | {'visualizou': 37, 'clicou': 1, 'agendou': 4} |
| borracharia | 0.581 | 0.581 | {'visualizou': 31, 'agendou': 5} |
| lava_jato | 0.527 | 0.527 | {'visualizou': 37, 'agendou': 5} |
| clinica_veterinaria | 0.523 | 0.523 | {'visualizou': 45, 'agendou': 6} |
| estetica | 0.523 | 0.33 | {'visualizou': 30, 'ignorou': 1, 'agendou': 2} |
| loja_calcados | 0.461 | 0.461 | {'visualizou': 37, 'agendou': 4} |
| bar | 0.316 | 0.316 | {'agendou': 2, 'visualizou': 33} |

> H alta = imprevisivel (pitch importa). H baixa = deterministico (pouco o que fazer).

## 7. Comparacao com Dataset Real (142 personas)

| Metrica | Real (142) | Simulado (N=1000) |
|---|---|---|
| Conversao | 13.4% | 16.3% |
| MI recent_event | 0.2662 | 0.1891 |
| MI segment | 0.073 | 0.0635 |
| H global | 0.672 | (ver entropia por nicho acima) |

## 8. Mapa de Prospeccao (top 20 bairro x nicho)

| Bairro | Nicho | Risco | Conv | IC 95% | WTP med | Empresas est. | Potencial |
|---|---|---|---|---|---|---|---|
| Centro | mercearia | alto | 100.0% | [15.9%, 98.7%] | R$ 34173 | 162 | 162 |
| Centro | oficina | alto | 60.0% | [21.9%, 88.1%] | R$ 16832 | 162 | 97 |
| Renascenca | clinica | baixo | 50.0% | [9.5%, 90.8%] | R$ 153425 | 193 | 96 |
| Turu | fisioterapia | medio | 40.0% | [12.1%, 78.0%] | R$ 13821 | 240 | 96 |
| Calhau | salao | medio | 50.0% | [14.5%, 85.5%] | R$ 33808 | 189 | 94 |
| Calhau | mecanica_diesel | medio | 50.0% | [18.3%, 81.8%] | R$ 213944 | 189 | 94 |
| Cohama | optica | medio | 60.0% | [21.9%, 88.1%] | R$ 58278 | 140 | 84 |
| Centro | optica | alto | 50.0% | [14.5%, 85.5%] | R$ 24418 | 162 | 81 |
| Centro | loja_calcados | alto | 50.0% | [14.5%, 85.5%] | R$ 32242 | 162 | 81 |
| Turu | restaurante | medio | 33.3% | [7.0%, 80.5%] | R$ 86550 | 240 | 80 |
| Calhau | optica | medio | 40.0% | [12.1%, 78.0%] | R$ 45865 | 189 | 75 |
| Sao Cristovao | clinica | alto | 100.0% | [15.9%, 98.7%] | R$ 38950 | 75 | 75 |
| Cohama | oficina | medio | 50.0% | [9.5%, 90.8%] | R$ 29025 | 140 | 70 |
| Turu | hamburgueria | medio | 28.6% | [8.5%, 65.8%] | R$ 34879 | 240 | 68 |
| Renascenca | estudio_tatuagem | baixo | 33.3% | [12.3%, 65.7%] | R$ 32433 | 193 | 64 |
| Calhau | oficina | medio | 33.3% | [7.0%, 80.5%] | R$ 36089 | 189 | 63 |
| Calhau | pet_shop | medio | 33.3% | [12.3%, 65.7%] | R$ 46423 | 189 | 63 |
| Calhau | consultorio_odonto | medio | 33.3% | [9.9%, 71.6%] | R$ 35111 | 189 | 63 |
| Vinhais | hamburgueria | medio | 100.0% | [15.9%, 98.7%] | R$ 11165 | 60 | 60 |
| Centro | consultorio_odonto | alto | 37.5% | [13.8%, 70.7%] | R$ 55385 | 162 | 60 |

## 9. Recomendacoes de Prospeccao

### 9.1 Bairros prioritarios para scrap no Maps

- **Centro** (risco alto, 3259 empresas): potencial ~1028 agendamentos
- **Turu** (risco medio, 4813 empresas): potencial ~865 agendamentos
- **Calhau** (risco medio, 3789 empresas): potencial ~767 agendamentos
- **Renascenca** (risco baixo, 3865 empresas): potencial ~602 agendamentos
- **Cohama** (risco medio, 2800 empresas): potencial ~546 agendamentos

### 9.2 Nichos prioritarios

- **consultorio_odonto**: conversao 29.8% (IC 18.7%-44.2%)
- **clinica**: conversao 25.6% (IC 14.7%-41.3%)
- **estacionamento**: conversao 25.0% (IC 13.9%-41.3%)

### 9.3 Drivers de decisao (por informacao mutua)

- **recent_event**: MI=0.1891 bits (driver significativo)
- **segment**: MI=0.0635 bits (driver significativo)

> Foco em personas com `recent_event=theft` e `has_existing_security=none` para maximizar conversao.

---

*Relatorio gerado por scripts/gerar_relatorio_fase0.py*