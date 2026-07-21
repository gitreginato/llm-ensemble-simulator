"""Gerador de personas v5 com bairros reais de Sao Luis, sazonalidade e budget mensal.

Diferenca vs v4:
- Bairros reais (BAIRROS_SLZ) em vez de genericos
- Sazonalidade Sao Luis (Sao Joao junho, Natal dezembro)
- Budget mensal de seguranca derivado do revenue
- Mensalidade por porte (R$ 294 a R$ 450)
- Contrato de 3 anos com multa proporcional aos meses restantes
- Ticket medio = mensalidade * 36 meses (compromisso total)
- 26 nichos com revenue realista (autopecas > loja_roupas, farmacia > todos)
- Segmentos classificados como perene ou volatil
- Limitacao EMIVE: so area interna (precisa_area_externa por nicho)
- Saturacao concorrencia local (20-30 instaladores em SLZ)
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from simulation_army_v2.bairros_slz import BAIRROS_SLZ, get_sazonalidade

# === CONFIGURACAO CONTRATUAL EMIVE ===
CONTRATO_MESES = 36  # 3 anos
MENSALIDADE_MIN = 294.00  # porte pequeno
MENSALIDADE_MAX = 450.00  # porte grande

# === LIMITACAO PRODUTO: EMIVE SO COBRE AREA INTERNA ===
# Probabilidade de o cliente precisar de area externa (camera de patio, fachada, estacionamento)
# Quase todos querem, mas alguns nichos precisam mais que outros
# User: "o povo quer camera externa e a gente nao tem"
P_PRECISA_AREA_EXTERNA: dict[str, float] = {
    # Alta necessidade (patio/estoque externo/veiculos)
    "estacionamento": 0.95,
    "autopecas": 0.85,
    "mecanica_diesel": 0.85,
    "borracharia": 0.80,
    "mercearia": 0.75,
    "mercadinho": 0.70,
    "oficina": 0.80,
    "lava_jato": 0.90,
    # Media necessidade (vitrine/fachada)
    "loja_roupas": 0.70,
    "loja_calcados": 0.70,
    "optica": 0.65,
    "pet_shop": 0.60,
    "restaurante": 0.60,
    "hamburgueria": 0.55,
    "bar": 0.55,
    # Baixa necessidade (predominantemente interno)
    "farmacia": 0.50,
    "clinica": 0.45,
    "consultorio_odonto": 0.40,
    "clinica_veterinaria": 0.50,
    "laboratorio": 0.40,
    "fisioterapia": 0.40,
    "barbearia": 0.45,
    "salao": 0.45,
    "academia": 0.50,
    "estetica": 0.40,
    "estudio_tatuagem": 0.45,
}

# === SATURACAO CONCORRENCIA LOCAL ===
# ~20-30 instaladores locais em SLZ com install base
# Probabilidade de ja ter concorrente local instalado (independente de has_existing_security)
# Bairros comerciais tem mais instaladores atuando
P_CONCORRENCIA_LOCAL_BASE = 0.35  # 35% base

# === BASINES DE REVENUE POR NICHO (realista para Sao Luis-MA) ===
# revenue: faturamento mensal em R$
# margin: margem de lucro (fracao)
# sec: fracao do revenue destinada a seguranca
# perene: True = segmento estavel, False = volatil/sazonal
# porte: pequeno, medio, grande (define mensalidade)
SEGMENT_BASELINES_V5: dict[str, dict] = {
    # === PERENE: alto faturamento, estavel ===
    "farmacia": {
        "revenue": (150000, 500000), "margin": (0.08, 0.15),
        "sec": (0.006, 0.018), "perene": True, "porte": "grande",
    },
    "mercearia": {
        "revenue": (80000, 250000), "margin": (0.05, 0.12),
        "sec": (0.005, 0.015), "perene": True, "porte": "medio",
    },
    "autopecas": {
        "revenue": (130000, 350000), "margin": (0.15, 0.25),
        "sec": (0.010, 0.030), "perene": True, "porte": "medio",
    },
    "oficina": {
        "revenue": (30000, 120000), "margin": (0.10, 0.20),
        "sec": (0.008, 0.022), "perene": True, "porte": "pequeno",
    },
    "mercadinho": {
        "revenue": (40000, 150000), "margin": (0.05, 0.12),
        "sec": (0.005, 0.015), "perene": True, "porte": "pequeno",
    },
    "clinica": {
        "revenue": (60000, 250000), "margin": (0.15, 0.30),
        "sec": (0.008, 0.020), "perene": True, "porte": "medio",
    },
    "consultorio_odonto": {
        "revenue": (40000, 150000), "margin": (0.20, 0.35),
        "sec": (0.008, 0.020), "perene": True, "porte": "pequeno",
    },
    "pet_shop": {
        "revenue": (30000, 100000), "margin": (0.15, 0.25),
        "sec": (0.008, 0.020), "perene": True, "porte": "pequeno",
    },
    # === SEMI-PERENE: estavel mas com alguma sazonalidade ===
    "barbearia": {
        "revenue": (15000, 60000), "margin": (0.20, 0.35),
        "sec": (0.005, 0.015), "perene": True, "porte": "pequeno",
    },
    "salao": {
        "revenue": (25000, 100000), "margin": (0.18, 0.30),
        "sec": (0.008, 0.020), "perene": True, "porte": "pequeno",
    },
    "academia": {
        "revenue": (30000, 120000), "margin": (0.15, 0.25),
        "sec": (0.008, 0.020), "perene": True, "porte": "medio",
    },
    # === AUTOMOTIVO (similar a autopecas, perenes, alto valor) ===
    "estacionamento": {
        "revenue": (40000, 150000), "margin": (0.20, 0.40),
        "sec": (0.010, 0.025), "perene": True, "porte": "medio",
    },
    "mecanica_diesel": {
        "revenue": (80000, 280000), "margin": (0.15, 0.25),
        "sec": (0.010, 0.030), "perene": True, "porte": "medio",
    },
    "lava_jato": {
        "revenue": (20000, 80000), "margin": (0.20, 0.35),
        "sec": (0.008, 0.020), "perene": True, "porte": "pequeno",
    },
    "borracharia": {
        "revenue": (30000, 100000), "margin": (0.15, 0.25),
        "sec": (0.008, 0.020), "perene": True, "porte": "pequeno",
    },
    # === SAUDE (similar a clinica/farmacia, perenes, alto valor) ===
    "laboratorio": {
        "revenue": (100000, 400000), "margin": (0.12, 0.20),
        "sec": (0.008, 0.018), "perene": True, "porte": "grande",
    },
    "clinica_veterinaria": {
        "revenue": (50000, 180000), "margin": (0.15, 0.28),
        "sec": (0.008, 0.020), "perene": True, "porte": "medio",
    },
    "fisioterapia": {
        "revenue": (30000, 120000), "margin": (0.18, 0.32),
        "sec": (0.008, 0.020), "perene": True, "porte": "pequeno",
    },
    "optica": {
        "revenue": (40000, 150000), "margin": (0.20, 0.35),
        "sec": (0.008, 0.020), "perene": True, "porte": "pequeno",
    },
    # === SERVICOS PESSOAIS (similar a barbearia/salao, perenes) ===
    "estetica": {
        "revenue": (40000, 160000), "margin": (0.20, 0.35),
        "sec": (0.008, 0.020), "perene": True, "porte": "medio",
    },
    "estudio_tatuagem": {
        "revenue": (25000, 100000), "margin": (0.25, 0.40),
        "sec": (0.008, 0.020), "perene": True, "porte": "pequeno",
    },
    # === VOLATIL: sazonal, alta rotatividade, concorrencia online ===
    "loja_roupas": {
        "revenue": (30000, 120000), "margin": (0.20, 0.35),
        "sec": (0.010, 0.030), "perene": False, "porte": "pequeno",
    },
    "loja_calcados": {
        "revenue": (30000, 100000), "margin": (0.20, 0.30),
        "sec": (0.010, 0.025), "perene": False, "porte": "pequeno",
    },
    "bar": {
        "revenue": (30000, 150000), "margin": (0.15, 0.25),
        "sec": (0.008, 0.025), "perene": False, "porte": "medio",
    },
    "hamburgueria": {
        "revenue": (40000, 180000), "margin": (0.15, 0.25),
        "sec": (0.008, 0.020), "perene": False, "porte": "medio",
    },
    "restaurante": {
        "revenue": (40000, 200000), "margin": (0.10, 0.20),
        "sec": (0.008, 0.020), "perene": False, "porte": "medio",
    },
}

NAMES_MALE = ["Joao", "Carlos", "Pedro", "Lucas", "Marcos", "Rafael", "Bruno", "Felipe",
              "Andre", "Thiago", "Ricardo", "Eduardo", "Paulo", "Marcelo", "Rodrigo"]
NAMES_FEMALE = ["Maria", "Ana", "Juliana", "Camila", "Fernanda", "Patricia", "Aline",
                "Beatriz", "Carla", "Daniela", "Erika", "Gabriela", "Larissa", "Mariana"]
SURNAMES = ["Silva", "Santos", "Oliveira", "Souza", "Lima", "Ferreira", "Almeida",
            "Pereira", "Costa", "Nascimento", "Barros", "Cardoso", "Ribeiro", "Pinto"]

RISK_PROFILES = ["conservative", "pragmatic", "crisis_driven", "innovator"]
RISK_WEIGHTS = [0.25, 0.40, 0.20, 0.15]

EXISTING_SECURITY = ["none", "diy_cameras", "alarm_monitored", "full_system"]
EXISTING_SECURITY_WEIGHTS = [0.15, 0.35, 0.25, 0.25]

RECENT_EVENTS = ["none", "theft", "competitor_new", "renovation", "slow_month"]
RECENT_EVENT_WEIGHTS_BASE = [0.50, 0.08, 0.10, 0.20, 0.12]


@dataclass
class PersonaV5:
    """Persona v5 com bairros reais, budget mensal, contrato, ticket medio e limitacoes EMIVE."""
    id: int
    owner_name: str
    gender: str
    segment: str
    segment_perene: bool
    segment_porte: str
    bairro: str
    bairro_risco: str
    bairro_perfil: str
    bairro_p_theft: float
    risk_profile: str
    recent_event: str
    has_existing_security: str
    existing_security_satisfaction: int
    revenue_mensal: float
    margin: float
    budget_mensal_seguranca: float
    mensalidade_emive: float
    ticket_medio_36m: float
    multa_proporcional_base: float
    wtp_brl: float
    pode_pagar_mensalidade: bool
    precisa_area_externa: bool = False
    concorrencia_local_instalada: bool = False
    mes: int = 7
    season: str = "media"
    season_revenue_multiplier: float = 1.0
    decision_maker: str = "solo"
    tech_savviness: int = 5
    trust_local_providers: int = 5
    bio: str = ""


def _choice_weighted(rng: random.Random, items: list, weights: list):
    return rng.choices(items, weights=weights, k=1)[0]


def _bairro_ponderado(rng: random.Random) -> str:
    bairros = list(BAIRROS_SLZ.keys())
    pesos = [BAIRROS_SLZ[b]["empresas"] for b in bairros]
    return rng.choices(bairros, weights=pesos, k=1)[0]


def _gerar_recent_event(rng: random.Random, bairro_p_theft: float) -> str:
    p_theft_ajustado = bairro_p_theft * 2
    weights = RECENT_EVENT_WEIGHTS_BASE.copy()
    weights[1] = p_theft_ajustado
    total = sum(weights)
    weights = [w / total for w in weights]
    return _choice_weighted(rng, RECENT_EVENTS, weights)


def _calcular_mensalidade(porte: str, rng: random.Random) -> float:
    """Calcula mensalidade baseada no porte do negocio.
    Pequeno: R$ 294 (minimo)
    Medio: R$ 350-400
    Grande: R$ 400-450

    Raises:
        ValueError: se porte nao for pequeno/medio/grande.
    """
    if porte == "pequeno":
        return MENSALIDADE_MIN
    elif porte == "medio":
        return rng.uniform(350, 400)
    elif porte == "grande":
        return rng.uniform(400, MENSALIDADE_MAX)
    raise ValueError(
        f"porte invalido: '{porte}'. Validos: pequeno, medio, grande."
    )


def _gerar_bio(p: PersonaV5) -> str:
    partes = [
        f"Dono(a) de {p.segment.replace('_', ' ')} no {p.bairro}",
        f"Faturamento mensal R$ {p.revenue_mensal:.0f}",
        f"Porte {p.segment_porte}, mensalidade R$ {p.mensalidade_emive:.0f}",
    ]
    if p.segment_perene:
        partes.append("segmento perene (estavel)")
    else:
        partes.append("segmento volatil (sazonal)")
    if p.has_existing_security == "none":
        partes.append("sem seguranca eletronica atualmente")
    elif p.has_existing_security == "diy_cameras":
        partes.append("tem cameras baratas sem monitoramento")
    elif p.has_existing_security == "alarm_monitored":
        partes.append("tem alarme monitorado concorrente")
    else:
        partes.append("tem sistema completo de seguranca")
    if p.recent_event == "theft":
        partes.append("sofreu roubo recente")
    elif p.recent_event == "renovation":
        partes.append("esta reformando o negocio")
    elif p.recent_event == "slow_month":
        partes.append("mes de movimento fraco")
    if p.precisa_area_externa:
        partes.append("precisa de cameras externas (EMIVE nao cobre)")
    if p.concorrencia_local_instalada:
        partes.append("concorrencia local ja atua na regiao")
    return ". ".join(partes) + "."


def generate_personas_v5(
    n: int,
    segment: str | None = None,
    mes: int = 7,
    seed: int = 42,
) -> list[PersonaV5]:
    """Gera N personas v5.

    Args:
        n: numero de personas
        segment: nicho especifico ou None para distribuir entre todos
        mes: mes (1-12) para sazonalidade
        seed: seed aleatoria

    Returns:
        Lista de PersonaV5
    """
    rng = random.Random(seed)
    personas = []
    if not 1 <= mes <= 12:
        raise ValueError(f"mes invalido: {mes}. Deve estar entre 1 e 12.")
    saz = get_sazonalidade(mes)
    season_label = "alta" if saz["revenue_multiplier"] > 1.1 else ("black_friday" if saz["revenue_multiplier"] > 1.05 else "media")

    valid_segments = set(SEGMENT_BASELINES_V5.keys())
    if segment is not None and segment not in valid_segments:
        raise ValueError(
            f"segment invalido: '{segment}'. Validos: {sorted(valid_segments)}."
        )

    for i in range(1, n + 1):
        seg = segment or rng.choice(list(SEGMENT_BASELINES_V5.keys()))
        baseline = SEGMENT_BASELINES_V5[seg]

        bairro_nome = _bairro_ponderado(rng)
        bairro = BAIRROS_SLZ[bairro_nome]

        # Revenue com sazonalidade (volateis sao mais afetados)
        revenue_base = rng.uniform(*baseline["revenue"])
        if not baseline["perene"]:
            revenue = revenue_base * saz["revenue_multiplier"]
        else:
            revenue = revenue_base * (1.0 + (saz["revenue_multiplier"] - 1.0) * 0.3)  # perenes menos afetados

        margin = rng.uniform(*baseline["margin"])

        # Budget mensal de seguranca
        sec_ratio = rng.uniform(*baseline["sec"])
        budget_mensal = revenue * sec_ratio

        # Mensalidade baseada no porte
        mensalidade = _calcular_mensalidade(baseline["porte"], rng)

        # Ticket medio = compromisso total de 36 meses
        ticket_medio = mensalidade * CONTRATO_MESES

        # Multa base = meses restantes * mensalidade (pior caso: cancela no mes 1)
        multa_base = (CONTRATO_MESES - 1) * mensalidade

        # WTP = budget mensal * 36 (compromisso que cliente esta disposto a assumir)
        wtp = budget_mensal * CONTRATO_MESES * rng.uniform(0.5, 1.5)

        pode_pagar = budget_mensal >= mensalidade

        recent_event = _gerar_recent_event(rng, bairro["p_theft_base"] * saz["p_theft_multiplier"])
        risk_profile = _choice_weighted(rng, RISK_PROFILES, RISK_WEIGHTS)
        has_security = _choice_weighted(rng, EXISTING_SECURITY, EXISTING_SECURITY_WEIGHTS)
        sat = 0 if has_security == "none" else rng.randint(3, 9)

        gender = rng.choice(["male", "female", "female", "male"])
        first = rng.choice(NAMES_MALE if gender == "male" else NAMES_FEMALE)
        last = rng.choice(SURNAMES)
        owner_name = f"{first} {last}"

        decision_maker = rng.choice(["solo", "family", "partner"])
        tech_savviness = rng.randint(2, 8)
        trust_local = rng.randint(4, 9)

        # Limitacao EMIVE: precisa de area externa?
        p_externa = P_PRECISA_AREA_EXTERNA.get(seg, 0.50)
        precisa_externa = rng.random() < p_externa

        # Saturacao concorrencia local: 35% base + variacao por bairro
        # Bairros com mais empresas = mais instaladores atuando
        n_empresas_bairro = bairro.get("empresas", 1000)
        p_concorrencia = P_CONCORRENCIA_LOCAL_BASE + min(0.20, n_empresas_bairro / 20000)
        concorrencia_instalada = rng.random() < p_concorrencia

        p = PersonaV5(
            id=i,
            owner_name=owner_name,
            gender=gender,
            segment=seg,
            segment_perene=baseline["perene"],
            segment_porte=baseline["porte"],
            bairro=bairro_nome,
            bairro_risco=bairro["risco"],
            bairro_perfil=bairro["perfil"],
            bairro_p_theft=bairro["p_theft_base"],
            risk_profile=risk_profile,
            recent_event=recent_event,
            has_existing_security=has_security,
            existing_security_satisfaction=sat,
            revenue_mensal=revenue,
            margin=margin,
            budget_mensal_seguranca=budget_mensal,
            mensalidade_emive=mensalidade,
            ticket_medio_36m=ticket_medio,
            multa_proporcional_base=multa_base,
            wtp_brl=wtp,
            pode_pagar_mensalidade=pode_pagar,
            precisa_area_externa=precisa_externa,
            concorrencia_local_instalada=concorrencia_instalada,
            mes=mes,
            season=season_label,
            season_revenue_multiplier=saz["revenue_multiplier"],
            decision_maker=decision_maker,
            tech_savviness=tech_savviness,
            trust_local_providers=trust_local,
        )
        p.bio = _gerar_bio(p)
        personas.append(p)

    return personas


def persona_to_dict(p: PersonaV5) -> dict[str, Any]:
    def _round(v, n):
        return None if v is None else round(v, n)

    return {
        "id": p.id,
        "owner_name": p.owner_name,
        "gender": p.gender,
        "segment": p.segment,
        "segment_perene": p.segment_perene,
        "segment_porte": p.segment_porte,
        "bairro": p.bairro,
        "bairro_risco": p.bairro_risco,
        "bairro_perfil": p.bairro_perfil,
        "bairro_p_theft": p.bairro_p_theft,
        "risk_profile": p.risk_profile,
        "recent_event": p.recent_event,
        "has_existing_security": p.has_existing_security,
        "existing_security_satisfaction": p.existing_security_satisfaction,
        "revenue_mensal": _round(p.revenue_mensal, 2),
        "margin": _round(p.margin, 4),
        "budget_mensal_seguranca": _round(p.budget_mensal_seguranca, 2),
        "mensalidade_emive": _round(p.mensalidade_emive, 2),
        "ticket_medio_36m": _round(p.ticket_medio_36m, 2),
        "multa_proporcional_base": _round(p.multa_proporcional_base, 2),
        "wtp_brl": _round(p.wtp_brl, 2),
        "pode_pagar_mensalidade": p.pode_pagar_mensalidade,
        "precisa_area_externa": p.precisa_area_externa,
        "concorrencia_local_instalada": p.concorrencia_local_instalada,
        "contrato_meses": CONTRATO_MESES,
        "mes": p.mes,
        "season": p.season,
        "season_revenue_multiplier": p.season_revenue_multiplier,
        "decision_maker": p.decision_maker,
        "tech_savviness": p.tech_savviness,
        "trust_local_providers": p.trust_local_providers,
        "bio": p.bio,
    }
