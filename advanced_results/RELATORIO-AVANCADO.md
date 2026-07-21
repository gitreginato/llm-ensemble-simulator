# Relatorio de Simulacoes Avancadas - Funil Bidirecional
Gerado em: 2026-07-12 20:47
Metodologia: agentes empresariais com atributos realistas avaliam oferta em 5 estagios; fase de boca a boca atualiza decisoes.

## DevinCriator / Owl Regent Studio

| Cenario | Segmento | Awareness | Interest | Consideration | Intent | Compra | Conversao geral | Sentimento | Impacto budget | Principal rejeicao |
|---------|----------|-----------|----------|---------------|--------|--------|-----------------|------------|----------------|---------------------|
| DC-AUTO-01 | lava_jato | 30 | 11 | 9 | 1 | 0 | 0.0% | -0.33 | 102.9% | budget |
| DC-AUTO-02 | oficina | 30 | 8 | 6 | 2 | 2 | 6.7% | -0.26 | 107.1% | budget |
| DC-VAL-01 | padaria | 30 | 9 | 7 | 2 | 1 | 3.3% | -0.39 | 195.9% | budget |
| DC-VAL-02 | food_truck | 30 | 16 | 14 | 7 | 6 | 20.0% | -0.13 | 83.9% | budget |

## SLZ N8N Stack

| Cenario | Segmento | Awareness | Interest | Consideration | Intent | Agendamento/Compra | Conversao geral | Sentimento | Impacto budget | Principal rejeicao |
|---------|----------|-----------|----------|---------------|--------|--------------------|-----------------|------------|----------------|---------------------|
| SLZ-AUTO-01 | carros_usados | 30 | 18 | 13 | 5 | 2 | 6.7% | -0.04 | 0.2% | existing_solution |
| SLZ-AUTO-02 | oficina | 30 | 13 | 10 | 4 | 3 | 10.0% | -0.09 | 0.0% | existing_solution |
| SLZ-AUTO-03 | lava_jato | 30 | 23 | 16 | 9 | 8 | 26.7% | +0.10 | 7.1% | existing_solution |

### DC-AUTO-01 - Identidade Visual para Lava-Jatos e Estetica Automotiva de Bairro
- Produto: Owl Regent Studio - Lava-Jatos e Estetica Automotiva
- Preco: R$ 244.00 (one_time)
- Conversao geral: 0.0%
- Sentimento medio: -0.33
- Impacto medio no budget: 102.9%
- Distribuicao de rejeicoes: {'budget': 30}

**Exemplos de agentes:**
- Daniel Lima (lava_jato): renda R$ 53,756.83, seguranca existente: alarm_monitored, perfil: pragmatic, decidiu: nao comprou - Preço alto para meu orçamento de marketing
- Carlos Pereira (lava_jato): renda R$ 26,274.13, seguranca existente: full_system, perfil: pragmatic, decidiu: nao comprou - Preço alto para meu orçamento de marketing
- Carlos Almeida (lava_jato): renda R$ 43,597.77, seguranca existente: full_system, perfil: pragmatic, decidiu: nao comprou - Preço alto para meu orçamento de marketing

### DC-AUTO-02 - Identidade Visual para Oficinas Mecanicas de Bairro
- Produto: Owl Regent Studio - Oficinas Mecanicas
- Preco: R$ 244.00 (one_time)
- Conversao geral: 6.7%
- Sentimento medio: -0.26
- Impacto medio no budget: 107.1%
- Distribuicao de rejeicoes: {'existing_solution': 5, 'budget': 23}

**Exemplos de agentes:**
- Patricia Ferreira (oficina): renda R$ 70,623.85, seguranca existente: full_system, perfil: conservative, decidiu: nao comprou - Não preciso de branding agora, tenho uma solução de segurança full_system
- Luana Ribeiro (oficina): renda R$ 44,545.30, seguranca existente: full_system, perfil: innovator, decidiu: nao comprou - Preço alto para meu orçamento de marketing
- Joao Lima (oficina): renda R$ 64,793.42, seguranca existente: full_system, perfil: conservative, decidiu: nao comprou - Preço alto para meu orçamento de marketing

### DC-VAL-01 - Identidade Visual para Padarias e Confeitarias de Bairro
- Produto: Owl Regent Studio - Padarias e Confeitarias
- Preco: R$ 244.00 (one_time)
- Conversao geral: 3.3%
- Sentimento medio: -0.39
- Impacto medio no budget: 195.9%
- Distribuicao de rejeicoes: {'budget': 29}

**Exemplos de agentes:**
- Debora Lima (padaria): renda R$ 43,500.07, seguranca existente: none, perfil: conservative, decidiu: nao comprou - Preço muito alto para meu orçamento de marketing
- Bruno Oliveira (padaria): renda R$ 60,750.31, seguranca existente: diy_cameras, perfil: conservative, decidiu: nao comprou - Preço muito alto para meu orçamento de marketing
- Rafael Mendes (padaria): renda R$ 54,095.61, seguranca existente: none, perfil: pragmatic, decidiu: nao comprou - Preço muito alto para meu orçamento de marketing

### DC-VAL-02 - Identidade Visual para Food Trucks e Quiosques
- Produto: Owl Regent Studio - Food Trucks e Quiosques
- Preco: R$ 244.00 (one_time)
- Conversao geral: 20.0%
- Sentimento medio: -0.13
- Impacto medio no budget: 83.9%
- Distribuicao de rejeicoes: {'budget': 24}

**Exemplos de agentes:**
- Carlos Costa (food_truck): renda R$ 29,072.62, seguranca existente: full_system, perfil: pragmatic, decidiu: nao comprou - Preço alto para meu orçamento de marketing (mudou de ideia apos indicacao)
- Debora Ferreira (food_truck): renda R$ 43,620.61, seguranca existente: full_system, perfil: conservative, decidiu: nao comprou - Preço muito alto para meu orçamento de marketing
- Aline Almeida (food_truck): renda R$ 38,358.14, seguranca existente: none, perfil: crisis_driven, decidiu: nao comprou - Preço muito alto para meu orçamento de marketing

### SLZ-AUTO-01 - SLZ Seguranca Inteligente para Lojas de Carros Usados e Multimarcas
- Produto: SLZ Seguranca Inteligente - Lojas de Carros Usados
- Preco: R$ 0.20 (visit)
- Conversao geral: 6.7%
- Sentimento medio: -0.04
- Impacto medio no budget: 0.2%
- Distribuicao de rejeicoes: {'timing': 2, 'existing_solution': 17, 'budget': 9}

**Exemplos de agentes:**
- Juliana Ribeiro (carros_usados): renda R$ 445,356.02, seguranca existente: full_system, perfil: pragmatic, decidiu: nao comprou - Não é o momento certo para investir em segurança
- Carlos Costa (carros_usados): renda R$ 257,961.11, seguranca existente: alarm_monitored, perfil: innovator, decidiu: nao comprou - Já tenho um sistema de alarme monitorado
- Camila Almeida (carros_usados): renda R$ 274,794.94, seguranca existente: full_system, perfil: innovator, decidiu: comprou/agendou - Custo benefício da visita técnica

### SLZ-AUTO-02 - SLZ Seguranca Inteligente para Oficinas Mecanicas
- Produto: SLZ Seguranca Inteligente - Oficinas Mecanicas
- Preco: R$ 0.20 (visit)
- Conversao geral: 10.0%
- Sentimento medio: -0.09
- Impacto medio no budget: 0.0%
- Distribuicao de rejeicoes: {'budget': 7, 'existing_solution': 20}

**Exemplos de agentes:**
- Bruno Nascimento (oficina): renda R$ 45,919.21, seguranca existente: diy_cameras, perfil: conservative, decidiu: nao comprou - Preço mensal pode ser alto para meu orçamento
- Gabriela Rodrigues (oficina): renda R$ 42,669.20, seguranca existente: alarm_monitored, perfil: crisis_driven, decidiu: nao comprou - Preço mensal pode ser alto para minha oficina
- Aline Souza (oficina): renda R$ 47,071.49, seguranca existente: full_system, perfil: conservative, decidiu: nao comprou - já tenho sistema de segurança

### SLZ-AUTO-03 - SLZ Seguranca Inteligente para Lava-Jatos e Estetica Automotiva
- Produto: SLZ Seguranca Inteligente - Lava-Jatos
- Preco: R$ 0.20 (visit)
- Conversao geral: 26.7%
- Sentimento medio: +0.10
- Impacto medio no budget: 7.1%
- Distribuicao de rejeicoes: {'existing_solution': 15, 'budget': 7}

**Exemplos de agentes:**
- Leticia Mendes (lava_jato): renda R$ 44,000.32, seguranca existente: alarm_monitored, perfil: crisis_driven, decidiu: nao comprou - Já tenho um sistema de alarme monitorado
- Camila Santos (lava_jato): renda R$ 48,308.15, seguranca existente: diy_cameras, perfil: conservative, decidiu: nao comprou - Eu já tenho câmeras caseiras, não preciso de mais nada
- Juliana Ribeiro (lava_jato): renda R$ 23,575.43, seguranca existente: diy_cameras, perfil: innovator, decidiu: comprou/agendou - Preço justo, mas preciso saber mais sobre o sistema completo
