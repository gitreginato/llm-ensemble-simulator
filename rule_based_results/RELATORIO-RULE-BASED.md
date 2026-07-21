# Relatorio de Simulacoes Avancadas - Funil Bidirecional
Gerado em: 2026-07-12 21:24
Metodologia: agentes empresariais com atributos realistas avaliam oferta em 5 estagios; fase de boca a boca atualiza decisoes.

## DevinCriator / Owl Regent Studio

| Cenario | Segmento | Awareness | Interest | Consideration | Intent | Compra | Conversao geral | Sentimento | Impacto budget | Principal rejeicao |
|---------|----------|-----------|----------|---------------|--------|--------|-----------------|------------|----------------|---------------------|
| DC-AUTO-01 | lava_jato | 22 | 15 | 11 | 8 | 2 | 6.7% | -0.03 | 11.4% | need_lack |
| DC-AUTO-02 | oficina | 24 | 14 | 9 | 4 | 0 | 0.0% | -0.06 | 8.2% | need_lack |
| DC-VAL-01 | padaria | 26 | 17 | 12 | 4 | 1 | 3.3% | -0.04 | 8.4% | need_lack |
| DC-VAL-02 | food_truck | 25 | 22 | 15 | 13 | 6 | 20.0% | +0.10 | 14.4% | timing |

## SLZ N8N Stack

| Cenario | Segmento | Awareness | Interest | Consideration | Intent | Agendamento/Compra | Conversao geral | Sentimento | Impacto budget | Principal rejeicao |
|---------|----------|-----------|----------|---------------|--------|--------------------|-----------------|------------|----------------|---------------------|
| SLZ-AUTO-01 | carros_usados | 25 | 25 | 19 | 16 | 6 | 20.0% | +0.11 | 0.0% | timing |
| SLZ-AUTO-02 | oficina | 21 | 14 | 11 | 8 | 2 | 6.7% | -0.05 | 0.0% | need_lack |
| SLZ-AUTO-03 | lava_jato | 23 | 16 | 10 | 8 | 1 | 3.3% | -0.05 | 0.1% | need_lack |

### DC-AUTO-01 - Identidade Visual para Lava-Jatos e Estetica Automotiva de Bairro
- Produto: Owl Regent Studio - Lava-Jatos e Estetica Automotiva
- Preco: R$ 197.00 (one_time)
- Conversao geral: 6.7%
- Sentimento medio: -0.03
- Impacto medio no budget: 11.4%
- Distribuicao de rejeicoes: {'need_lack': 15, 'timing': 10, 'skepticism': 3}

**Exemplos de agentes:**
- Joao Araujo (lava_jato): renda R$ 31,001.17, seguranca existente: none, perfil: crisis_driven, decidiu: nao comprou - Não vejo necessidade agora
- Eduardo Mendes (lava_jato): renda R$ 26,386.37, seguranca existente: alarm_monitored, perfil: conservative, decidiu: comprou/agendou - 
- Renata Souza (lava_jato): renda R$ 48,182.87, seguranca existente: none, perfil: pragmatic, decidiu: nao comprou - Não vejo necessidade agora

### DC-AUTO-02 - Identidade Visual para Oficinas Mecanicas de Bairro
- Produto: Owl Regent Studio - Oficinas Mecanicas
- Preco: R$ 197.00 (one_time)
- Conversao geral: 0.0%
- Sentimento medio: -0.06
- Impacto medio no budget: 8.2%
- Distribuicao de rejeicoes: {'need_lack': 16, 'timing': 11, 'skepticism': 3}

**Exemplos de agentes:**
- Joao Araujo (oficina): renda R$ 45,627.20, seguranca existente: diy_cameras, perfil: crisis_driven, decidiu: nao comprou - Não vejo necessidade agora
- Eduardo Mendes (oficina): renda R$ 36,974.45, seguranca existente: full_system, perfil: conservative, decidiu: nao comprou - Não vejo necessidade agora
- Renata Souza (oficina): renda R$ 77,842.89, seguranca existente: diy_cameras, perfil: conservative, decidiu: nao comprou - Estou fechando o mês, depois eu vejo

### DC-VAL-01 - Identidade Visual para Padarias e Confeitarias de Bairro
- Produto: Owl Regent Studio - Padarias e Confeitarias
- Preco: R$ 197.00 (one_time)
- Conversao geral: 3.3%
- Sentimento medio: -0.04
- Impacto medio no budget: 8.4%
- Distribuicao de rejeicoes: {'need_lack': 13, 'timing': 9, 'skepticism': 5, 'budget': 2}

**Exemplos de agentes:**
- Joao Araujo (padaria): renda R$ 44,626.03, seguranca existente: none, perfil: crisis_driven, decidiu: nao comprou - Não vejo necessidade agora
- Eduardo Mendes (padaria): renda R$ 40,588.08, seguranca existente: alarm_monitored, perfil: conservative, decidiu: comprou/agendou - 
- Renata Souza (padaria): renda R$ 59,660.01, seguranca existente: none, perfil: pragmatic, decidiu: nao comprou - Não vejo necessidade agora

### DC-VAL-02 - Identidade Visual para Food Trucks e Quiosques
- Produto: Owl Regent Studio - Food Trucks e Quiosques
- Preco: R$ 197.00 (one_time)
- Conversao geral: 20.0%
- Sentimento medio: +0.10
- Impacto medio no budget: 14.4%
- Distribuicao de rejeicoes: {'need_lack': 8, 'timing': 12, 'budget': 2, 'skepticism': 2}

**Exemplos de agentes:**
- Joao Araujo (food_truck): renda R$ 24,626.03, seguranca existente: none, perfil: crisis_driven, decidiu: nao comprou - Não vejo necessidade agora
- Eduardo Mendes (food_truck): renda R$ 20,588.08, seguranca existente: alarm_monitored, perfil: conservative, decidiu: comprou/agendou - 
- Renata Souza (food_truck): renda R$ 39,660.01, seguranca existente: none, perfil: pragmatic, decidiu: nao comprou - Não vejo necessidade agora

### SLZ-AUTO-01 - SLZ Seguranca Inteligente para Lojas de Carros Usados e Multimarcas
- Produto: SLZ Seguranca Inteligente - Lojas de Carros Usados
- Preco: R$ 0.20 (visit)
- Conversao geral: 20.0%
- Sentimento medio: +0.11
- Impacto medio no budget: 0.0%
- Distribuicao de rejeicoes: {'need_lack': 5, 'timing': 9, 'existing_solution': 5, 'skepticism': 5}

**Exemplos de agentes:**
- Joao Araujo (carros_usados): renda R$ 195,512.31, seguranca existente: diy_cameras, perfil: crisis_driven, decidiu: nao comprou - Não vejo necessidade agora
- Eduardo Mendes (carros_usados): renda R$ 147,056.91, seguranca existente: full_system, perfil: conservative, decidiu: nao comprou - Não vejo necessidade agora
- Renata Souza (carros_usados): renda R$ 375,920.17, seguranca existente: diy_cameras, perfil: conservative, decidiu: nao comprou - Estou fechando o mês, depois eu vejo

### SLZ-AUTO-02 - SLZ Seguranca Inteligente para Oficinas Mecanicas
- Produto: SLZ Seguranca Inteligente - Oficinas Mecanicas
- Preco: R$ 0.20 (visit)
- Conversao geral: 6.7%
- Sentimento medio: -0.05
- Impacto medio no budget: 0.0%
- Distribuicao de rejeicoes: {'need_lack': 16, 'timing': 6, 'existing_solution': 2, 'skepticism': 4}

**Exemplos de agentes:**
- Joao Araujo (oficina): renda R$ 45,627.20, seguranca existente: diy_cameras, perfil: crisis_driven, decidiu: nao comprou - Não vejo necessidade agora
- Eduardo Mendes (oficina): renda R$ 36,974.45, seguranca existente: full_system, perfil: conservative, decidiu: nao comprou - Não vejo necessidade agora
- Renata Souza (oficina): renda R$ 77,842.89, seguranca existente: diy_cameras, perfil: conservative, decidiu: nao comprou - Estou fechando o mês, depois eu vejo

### SLZ-AUTO-03 - SLZ Seguranca Inteligente para Lava-Jatos e Estetica Automotiva
- Produto: SLZ Seguranca Inteligente - Lava-Jatos
- Preco: R$ 0.20 (visit)
- Conversao geral: 3.3%
- Sentimento medio: -0.05
- Impacto medio no budget: 0.1%
- Distribuicao de rejeicoes: {'need_lack': 14, 'timing': 12, 'existing_solution': 2, 'skepticism': 1}

**Exemplos de agentes:**
- Joao Araujo (lava_jato): renda R$ 31,001.17, seguranca existente: none, perfil: crisis_driven, decidiu: nao comprou - Não vejo necessidade agora
- Eduardo Mendes (lava_jato): renda R$ 26,386.37, seguranca existente: alarm_monitored, perfil: conservative, decidiu: nao comprou - Não vejo necessidade agora
- Renata Souza (lava_jato): renda R$ 48,182.87, seguranca existente: none, perfil: pragmatic, decidiu: nao comprou - Estou fechando o mês, depois eu vejo
