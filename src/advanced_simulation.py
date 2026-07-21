#!/usr/bin/env python3
"""
Simulacao de mercado avancada com funil bidirecional e agentes especificos.

Caracteristicas:
- Agentes empresariais com atributos realistas (faturamento, margem, orcamento,
  sistema existente, perfil de risco, momento do mes).
- Funil AIDA explicito: awareness -> interest -> consideration -> intent -> purchase.
- Influencia social (boca a boca) entre agentes.
- Categorizacao de rejeicoes: budget, timing, existing_solution, skepticism,
  complexity, need_lack.
- Saida em JSON + markdown.
"""

import json
import os
import random
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import requests
from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Configuracao
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / "launch-simulation" / "backend" / ".env")
load_dotenv(ROOT / "arena-de-ias" / ".env")

# Seleciona provedor disponivel (Groq e preferido: rapido e free)
if os.getenv("GROQ_API_KEY"):
    LLM_API_KEY = os.getenv("GROQ_API_KEY")
    LLM_BASE_URL = "https://api.groq.com/openai/v1"
    LLM_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
elif os.getenv("NVIDIA_API_KEY"):
    LLM_API_KEY = os.getenv("NVIDIA_API_KEY")
    LLM_BASE_URL = "https://integrate.api.nvidia.com/v1"
    LLM_MODEL = "meta/llama-3.1-70b-instruct"
elif os.getenv("OPENROUTER_API_KEY"):
    LLM_API_KEY = os.getenv("OPENROUTER_API_KEY")
    LLM_BASE_URL = "https://openrouter.ai/api/v1"
    LLM_MODEL = "google/gemini-2.5-flash-lite"
elif os.getenv("LLM_API_KEY") or os.getenv("LLM_BOOST_API_KEY"):
    LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("LLM_BOOST_API_KEY")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    LLM_MODEL = os.getenv("LLM_MODEL_NAME", "meta-llama/llama-4-scout-17b-16e-instruct")
else:
    LLM_API_KEY = None
    LLM_BASE_URL = ""
    LLM_MODEL = ""

# Rate limiting responsavel (ver API-LIMITES.md)
MIN_DELAY_SECONDS = 5.0
MAX_RETRIES = 5
BACKOFF_BASE = 2.0
BACKOFF_MAX = 60.0
_last_call_time: float = 0.0

PROMPT_SYSTEM = (
    "You are a market simulation engine. You evaluate how a specific business owner "
    "would react to a product/service offer. Return ONLY valid JSON. No markdown, no preamble."
)


def _rate_limit_wait():
    """Garante intervalo minimo entre chamadas a API."""
    global _last_call_time
    elapsed = time.time() - _last_call_time
    if elapsed < MIN_DELAY_SECONDS:
        wait = MIN_DELAY_SECONDS - elapsed
        print(f"[RateLimiter] Aguardando {wait:.1f}s antes da proxima chamada...")
        time.sleep(wait)
    _last_call_time = time.time()


# ---------------------------------------------------------------------------
# Estruturas de dados
# ---------------------------------------------------------------------------

@dataclass
class BusinessProfile:
    agent_id: str
    segment: str
    business_name: str
    owner_name: str
    age: int
    gender: str
    monthly_revenue_brl: float
    profit_margin_pct: float
    marketing_budget_brl: float
    security_budget_brl: float
    has_existing_security: str  # none, diy_cameras, alarm_monitored, full_system
    existing_security_satisfaction: int  # 1-10
    risk_profile: str  # conservative, pragmatic, innovator, crisis_driven
    decision_maker: str  # solo, family, partner
    day_of_month: int  # 1-30
    season: str  # high, normal, low
    location_bairro: str
    recent_event: str  # none, theft, competitor_new, renovation, slow_month
    tech_savviness: int  # 1-10
    trust_local_providers: int  # 1-10
    influence_score: int  # 1-10 (how much others listen to them)
    bio: str = ""
    wtp_brl: float = 0.0


@dataclass
class FunnelResult:
    awareness: bool
    interest: bool
    consideration: bool
    intent: bool
    purchased: bool
    rejection_stage: str
    rejection_reason: str
    budget_impact_pct: float
    key_objection: str
    social_post: str
    sentiment: float  # -1 to +1


@dataclass
class ScenarioConfig:
    project: str  # devincriator or slz_n8n
    code: str
    name: str
    product_name: str
    description: str
    price_brl: float
    price_model: str  # one_time, monthly, visit
    target_segment: str
    channel: str
    value_proposition: str
    pain_focus: str
    num_agents: int = 30
    persona_templates: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Geracao de personas com atributos realistas
# ---------------------------------------------------------------------------

SEGMENT_BASELINES = {
    "padaria": {"revenue": (35000, 70000), "margin": (0.10, 0.15), "mkt": (0.03, 0.07), "sec": (0.005, 0.015), "wtp_branding": (150, 400), "wtp_security": (150, 400)},
    "confeitaria": {"revenue": (25000, 60000), "margin": (0.12, 0.20), "mkt": (0.04, 0.08), "sec": (0.005, 0.015), "wtp_branding": (200, 500), "wtp_security": (150, 350)},
    "salao": {"revenue": (30000, 100000), "margin": (0.18, 0.30), "mkt": (0.05, 0.10), "sec": (0.008, 0.020), "wtp_branding": (300, 800), "wtp_security": (200, 600)},
    "barbearia": {"revenue": (25000, 60000), "margin": (0.18, 0.30), "mkt": (0.04, 0.09), "sec": (0.005, 0.015), "wtp_branding": (200, 500), "wtp_security": (150, 400)},
    "bar": {"revenue": (20000, 120000), "margin": (0.15, 0.25), "mkt": (0.04, 0.10), "sec": (0.008, 0.025), "wtp_branding": (200, 700), "wtp_security": (200, 800)},
    "lanchonete": {"revenue": (30000, 100000), "margin": (0.15, 0.25), "mkt": (0.04, 0.09), "sec": (0.006, 0.018), "wtp_branding": (200, 600), "wtp_security": (200, 500)},
    "hamburgueria": {"revenue": (50000, 150000), "margin": (0.15, 0.25), "mkt": (0.05, 0.12), "sec": (0.008, 0.020), "wtp_branding": (300, 800), "wtp_security": (250, 700)},
    "food_truck": {"revenue": (15000, 50000), "margin": (0.15, 0.25), "mkt": (0.03, 0.08), "sec": (0.003, 0.010), "wtp_branding": (150, 500), "wtp_security": (50, 200)},
    "loja_roupas": {"revenue": (50000, 180000), "margin": (0.20, 0.35), "mkt": (0.06, 0.12), "sec": (0.010, 0.030), "wtp_branding": (300, 1000), "wtp_security": (300, 1000)},
    "loja_calcados": {"revenue": (40000, 120000), "margin": (0.20, 0.30), "mkt": (0.05, 0.10), "sec": (0.010, 0.025), "wtp_branding": (250, 800), "wtp_security": (300, 900)},
    "oficina": {"revenue": (25000, 100000), "margin": (0.10, 0.20), "mkt": (0.03, 0.07), "sec": (0.008, 0.022), "wtp_branding": (200, 600), "wtp_security": (300, 900)},
    "lava_jato": {"revenue": (20000, 60000), "margin": (0.20, 0.40), "mkt": (0.03, 0.08), "sec": (0.005, 0.015), "wtp_branding": (150, 500), "wtp_security": (150, 400)},
    "autopecas": {"revenue": (40000, 150000), "margin": (0.15, 0.25), "mkt": (0.04, 0.09), "sec": (0.010, 0.030), "wtp_branding": (250, 700), "wtp_security": (400, 1200)},
    "carros_usados": {"revenue": (80000, 500000), "margin": (0.05, 0.12), "mkt": (0.04, 0.08), "sec": (0.010, 0.040), "wtp_branding": (400, 1500), "wtp_security": (800, 3000)},
    "concessionaria": {"revenue": (500000, 2000000), "margin": (0.05, 0.10), "mkt": (0.03, 0.07), "sec": (0.015, 0.050), "wtp_branding": (1000, 5000), "wtp_security": (3000, 15000)},
    "farmacia": {"revenue": (150000, 500000), "margin": (0.08, 0.15), "mkt": (0.03, 0.07), "sec": (0.006, 0.018), "wtp_branding": (300, 1000), "wtp_security": (600, 2000)},
    "mercearia": {"revenue": (80000, 200000), "margin": (0.05, 0.12), "mkt": (0.02, 0.05), "sec": (0.005, 0.015), "wtp_branding": (150, 500), "wtp_security": (300, 800)},
    "profissional_liberal": {"revenue": (8000, 30000), "margin": (0.30, 0.50), "mkt": (0.05, 0.12), "sec": (0.000, 0.005), "wtp_branding": (150, 500), "wtp_security": (0, 100)},
    "residencia": {"revenue": (8000, 50000), "margin": (0.20, 0.40), "mkt": (0.00, 0.02), "sec": (0.010, 0.050), "wtp_branding": (0, 0), "wtp_security": (150, 1000)},
}

BAIRROS_SLZ = [
    "Calhau", "Coroado", "Turu", "Olho d'Agua", "Sacavem", "Vinhais",
    "Cohama", "Renascenca", "Ponta d'Areia", "Centro", "Sao Cristovao",
    "Vila Luizao", "Divinea", "Cohab/Anil", "Forquilha", "Jardim Renascenca",
    "Cohatrac", "Maioba", "Tirirical", "Sol e Mar"
]

NAMES_MALE = ["Joao", "Carlos", "Marcelo", "Pedro", "Jose", "Francisco", "Lucas", "Mateus", "Andre", "Bruno", "Rafael", "Felipe", "Eduardo", "Daniel", "Antonio"]
NAMES_FEMALE = ["Maria", "Ana", "Luana", "Beatriz", "Gabriela", "Leticia", "Fernanda", "Juliana", "Patricia", "Renata", "Camila", "Tatiana", "Debora", "Simone", "Aline"]
SURNAMES = ["Silva", "Oliveira", "Santos", "Souza", "Lima", "Costa", "Pereira", "Ferreira", "Rodrigues", "Almeida", "Nascimento", "Araujo", "Mendes", "Barros", "Ribeiro"]

RISK_PROFILES = ["conservative", "pragmatic", "innovator", "crisis_driven"]
DECISION_MAKERS = ["solo", "family", "partner"]
SECURITY_TYPES = ["none", "diy_cameras", "alarm_monitored", "full_system"]
RECENT_EVENTS = ["none", "theft", "competitor_new", "renovation", "slow_month"]
SEASONS = ["high", "normal", "low"]


def _rand(a: float, b: float) -> float:
    return round(random.uniform(a, b), 2)


def _randint(a: int, b: int) -> int:
    return random.randint(a, b)


def _choice(seq: list[str]) -> str:
    return random.choice(seq)


def generate_personas(segment: str, num_agents: int) -> list[BusinessProfile]:
    base = SEGMENT_BASELINES.get(segment, SEGMENT_BASELINES["padaria"])
    personas = []
    for i in range(1, num_agents + 1):
        gender = _choice(["male", "female", "female", "male"])
        first = _choice(NAMES_MALE if gender == "male" else NAMES_FEMALE)
        last = _choice(SURNAMES)
        owner_name = f"{first} {last}"

        revenue = _rand(base["revenue"][0], base["revenue"][1])
        margin = _rand(base["margin"][0], base["margin"][1])
        mkt_pct = _rand(base["mkt"][0], base["mkt"][1])
        sec_pct = _rand(base["sec"][0], base["sec"][1])

        # Existing security biased by segment security budget
        if segment in ["residencia"]:
            sec_type = _choice(["none", "diy_cameras", "diy_cameras", "alarm_monitored"])
        elif segment in ["carros_usados", "oficina", "autopecas", "concessionaria", "farmacia"]:
            sec_type = _choice(["diy_cameras", "alarm_monitored", "full_system", "full_system"])
        else:
            sec_type = _choice(SECURITY_TYPES)

        # Satisfacao varia pelo tipo: DIY costuma ser insatisfatorio; sistemas pagos sao melhores
        if sec_type == "none":
            satisfaction = 0
        elif sec_type == "diy_cameras":
            satisfaction = _randint(2, 6)
        elif sec_type == "alarm_monitored":
            satisfaction = _randint(4, 8)
        else:  # full_system
            satisfaction = _randint(5, 9)

        # Risk profile biased by security type
        if sec_type == "none":
            risk = _choice(["conservative", "pragmatic", "crisis_driven", "crisis_driven"])
        else:
            risk = _choice(RISK_PROFILES + ["pragmatic", "pragmatic", "conservative"])

        # Recent event
        event_weights = {"none": 5, "theft": 1, "competitor_new": 2, "renovation": 2, "slow_month": 3}
        recent_event = random.choices(list(event_weights.keys()), weights=list(event_weights.values()))[0]

        # Season / timing
        season = random.choices(SEASONS, weights=[2, 5, 3])[0]
        day_of_month = random.choices(range(1, 31), weights=[3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])[0]

        profile = BusinessProfile(
            agent_id=f"agent_{i:03d}",
            segment=segment,
            business_name=f"{owner_name.split()[0]} {segment.replace('_', ' ').title()}",
            owner_name=owner_name,
            age=_randint(28, 65),
            gender=gender,
            monthly_revenue_brl=revenue,
            profit_margin_pct=margin,
            marketing_budget_brl=round(revenue * mkt_pct, 2),
            security_budget_brl=round(revenue * sec_pct, 2),
            has_existing_security=sec_type,
            existing_security_satisfaction=satisfaction,
            risk_profile=risk,
            decision_maker=_choice(DECISION_MAKERS),
            day_of_month=day_of_month,
            season=season,
            location_bairro=_choice(BAIRROS_SLZ),
            recent_event=recent_event,
            tech_savviness=_randint(2, 9),
            trust_local_providers=_randint(4, 10),
            influence_score=_randint(1, 10),
            wtp_brl=round(random.uniform(base["wtp_branding"][0] if "branding" in segment or segment != "residencia" else base["wtp_security"][0],
                                          base["wtp_branding"][1] if "branding" in segment or segment != "residencia" else base["wtp_security"][1]), 2),
        )
        personas.append(profile)
    return personas


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def llm_call(system: str, user: str, max_retries: int = MAX_RETRIES) -> dict:
    if not LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY nao configurada. Verifique launch-simulation/backend/.env")

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "temperature": 0.3,
        "max_tokens": 1200,
    }
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "advanced-simulation/1.0",
    }

    # Reutiliza uma sessao persistente para evitar handshake repetido
    if not hasattr(llm_call, "_session"):
        llm_call._session = requests.Session()
        llm_call._session.headers.update(headers)

    for attempt in range(max_retries + 1):
        _rate_limit_wait()
        try:
            resp = llm_call._session.post(
                f"{LLM_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
                timeout=(30, 120),
            )
            resp.raise_for_status()
            raw = resp.json()
            content = raw["choices"][0]["message"]["content"]
            content = _strip_code_fences(content)
            return json.loads(content)
        except requests.HTTPError as exc:
            code = exc.response.status_code if exc.response else 0
            body = exc.response.text[:200] if exc.response else ""
            print(f"[LLM] HTTP erro tentativa {attempt + 1}: {code} - {body}")
            # Rate limit: backoff agressivo
            wait = min(BACKOFF_MAX, BACKOFF_BASE ** attempt + (10 if code == 429 else 0))
            if attempt < max_retries:
                print(f"[LLM] Aguardando {wait:.0f}s antes de retry...")
                time.sleep(wait)
            else:
                raise RuntimeError(f"API retornou {code} apos {max_retries} tentativas. Pare para nao esgotar quota.")
        except Exception as exc:
            print(f"[LLM] Erro tentativa {attempt + 1}: {exc}")
            wait = min(BACKOFF_MAX, BACKOFF_BASE ** attempt)
            if attempt < max_retries:
                print(f"[LLM] Aguardando {wait:.0f}s antes de retry...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Todas as tentativas falharam")


# ---------------------------------------------------------------------------
# Avaliacao do funil
# ---------------------------------------------------------------------------

FUNNEL_PROMPT = """You are a realistic Brazilian small-business decision simulator.
Be CRITICAL. Most owners should NOT buy. Only buy if the offer truly fits their budget, timing, existing solutions, and pain urgency.

## Business Owner Profile
- Name: {owner_name}
- Segment: {segment}
- Monthly revenue: R$ {monthly_revenue_brl:,.2f}
- Profit margin: {profit_margin_pct:.0%}
- Marketing budget: R$ {marketing_budget_brl:,.2f}/month
- Security budget: R$ {security_budget_brl:,.2f}/month
- Existing security: {has_existing_security}
- Satisfaction with existing: {existing_security_satisfaction}/10
- Risk profile: {risk_profile}
- Decision maker: {decision_maker}
- Day of month: {day_of_month}
- Season/business moment: {season}
- Recent event: {recent_event}
- Tech savviness: {tech_savviness}/10
- Trust in local providers: {trust_local_providers}/10
- Maximum willingness to pay (WTP): R$ {wtp_brl:,.2f}

## Offer
- Product: {product_name}
- Price: R$ {price_brl:,.2f} ({price_model})
- Channel: {channel}
- Description: {description}
- Value proposition: {value_proposition}
- Pain focus: {pain_focus}

## Pre-calculated context
- Price shown: R$ {price_brl:,.2f}
- Relevant monthly budget: R$ {relevant_budget:,.2f}
- Budget impact if purchased: {budget_impact_pct:.1f}%
- Owner stated WTP: R$ {wtp_brl:,.2f}

## Task
Return ONLY a JSON object with exactly these fields:
{{
  "awareness": true/false,
  "interest": true/false,
  "consideration": true/false,
  "intent": true/false,
  "purchased": true/false,
  "rejection_stage": "none|awareness|interest|consideration|intent",
  "rejection_reason": "budget|timing|existing_solution|skepticism|complexity|need_lack|none",
  "key_objection": "short phrase in Portuguese",
  "social_post": "one sentence in Portuguese that this owner might post/think",
  "sentiment": float  // -1.0 to +1.0
}}

Critical rules - apply strictly:
- For branding offers, "purchased" means bought the kit. For security offers, "purchased" means SCHEDULED the diagnostic visit.
- awareness = false if the message would be ignored. Expect 15-35% to ignore.
- interest = true only if pain focus matches a real problem.
- consideration = true if they would ask for details or compare. Owners with DIY cameras or unsatisfactory alarm SHOULD consider upgrading. Owners with full_system and high satisfaction (>=8) usually do NOT consider.
- intent = true if they genuinely want to schedule/buy, before final budget/timing check.
- purchased = true ONLY if intent AND price <= WTP AND budget impact allows AND timing allows AND no clearly better existing solution. Budget impact <= 80% is comfortable; <= 120% is acceptable if WTP supports; > 120% is hard to justify.
- If not purchased, set rejection_stage to the highest reached stage before dropping and rejection_reason to the TRUE cause.
- day_of_month: 1-10 easier; 20-30 harder.
- season: low = harder; high = easier.
- existing_solution rejection: use only if current system is good AND owner is satisfied (>=7 for alarm/full_system, >=5 for DIY). DIY cameras alone are usually insufficient for a business.
- If price > WTP, rejection_reason must be "budget".
- If budget impact > 120% AND price close to WTP, rejection_reason should be "budget".
- If day_of_month > 25 AND season != high, rejection_reason should often be "timing".
- conservative profile: needs local proof; rejects without trust.
- innovator profile: more likely to try if budget allows.
- crisis_driven: converts if recent_event is theft and offer addresses it.
- Sentiment should reflect the owner's emotional reaction: curious/positive if interest, neutral if hesitant, negative if rejected due to price/skepticism.
- Remember: simulate REAL owners. Some will buy, most will not.

Examples of realistic decisions:
- Owner with full_system, satisfaction 8, no recent event: awareness true, interest false, rejection_stage awareness, rejection_reason need_lack, sentiment -0.1.
- Owner with diy_cameras (satisfaction 4), recent theft, budget ok: awareness true, interest true, consideration true, intent true, purchased true, sentiment +0.5.
- Owner with alarm_monitored, satisfaction 6, no theft, budget ok: awareness true, interest true, consideration true, intent true, purchased true, sentiment +0.3.
- Owner with alarm_monitored, satisfaction 8, no theft: awareness true, interest true, consideration false, rejection_stage consideration, rejection_reason existing_solution, sentiment 0.0.
- Owner with tight budget, day 28, budget impact 150%: awareness true, interest true, consideration false, rejection_stage consideration, rejection_reason timing, sentiment -0.3.
"""


def evaluate_funnel(profile: BusinessProfile, scenario: ScenarioConfig) -> FunnelResult:
    relevant_budget = profile.marketing_budget_brl if scenario.project == "devincriator" else profile.security_budget_brl
    budget_impact_pct = (scenario.price_brl / relevant_budget * 100) if relevant_budget > 0 else 999.0

    user_prompt = FUNNEL_PROMPT.format(
        owner_name=profile.owner_name,
        segment=profile.segment.replace("_", " ").title(),
        monthly_revenue_brl=profile.monthly_revenue_brl,
        profit_margin_pct=profile.profit_margin_pct,
        marketing_budget_brl=profile.marketing_budget_brl,
        security_budget_brl=profile.security_budget_brl,
        has_existing_security=profile.has_existing_security,
        existing_security_satisfaction=profile.existing_security_satisfaction,
        risk_profile=profile.risk_profile,
        decision_maker=profile.decision_maker,
        day_of_month=profile.day_of_month,
        season=profile.season,
        recent_event=profile.recent_event,
        tech_savviness=profile.tech_savviness,
        trust_local_providers=profile.trust_local_providers,
        wtp_brl=profile.wtp_brl,
        product_name=scenario.product_name,
        price_brl=scenario.price_brl,
        price_model=scenario.price_model,
        channel=scenario.channel,
        description=scenario.description,
        value_proposition=scenario.value_proposition,
        pain_focus=scenario.pain_focus,
        relevant_budget=relevant_budget,
        budget_impact_pct=budget_impact_pct,
    )

    result = llm_call(PROMPT_SYSTEM, user_prompt)

    return FunnelResult(
        awareness=result.get("awareness", False),
        interest=result.get("interest", False),
        consideration=result.get("consideration", False),
        intent=result.get("intent", False),
        purchased=result.get("purchased", False),
        rejection_stage=result.get("rejection_stage", "none"),
        rejection_reason=result.get("rejection_reason", "none"),
        budget_impact_pct=budget_impact_pct,
        key_objection=result.get("key_objection", ""),
        social_post=result.get("social_post", ""),
        sentiment=float(result.get("sentiment", 0)),
    )


# ---------------------------------------------------------------------------
# Boca a boca (influencia social)
# ---------------------------------------------------------------------------

def apply_word_of_mouth(personas: list[BusinessProfile], results: list[FunnelResult]) -> list[FunnelResult]:
    """Agentes que compraram e tem alta influencia podem converter agentes em consideration/intent."""
    updated = [r for r in results]
    buyers = [(p, r) for p, r in zip(personas, results) if r.purchased]
    for p, r in zip(personas, updated):
        if r.purchased:
            continue
        if not r.interest:
            continue
        # Ver influenciadores
        influencers = [b for b in buyers if b[0].influence_score >= 6 and b[0].segment == p.segment]
        if not influencers:
            continue
        # Probabilidade de conversao pela influencia
        influence_power = sum(b[0].influence_score for b in influencers) / len(influencers)
        boost = influence_power / 50.0  # max ~0.2
        if r.consideration and not r.intent and random.random() < boost:
            r.intent = True
            r.key_objection += " (mudou de ideia apos indicacao)"
        if r.intent and not r.purchased and r.rejection_reason in ["skepticism", "need_lack"] and random.random() < boost:
            r.purchased = True
            r.rejection_stage = "none"
            r.rejection_reason = "none"
            r.social_post += " Comprei depois de conversar com colegas do ramo."
    return updated


# ---------------------------------------------------------------------------
# Simulacao de um cenario
# ---------------------------------------------------------------------------

def run_scenario(scenario: ScenarioConfig) -> dict:
    print(f"\n[Iniciando] {scenario.name}")
    personas = generate_personas(scenario.target_segment, scenario.num_agents)

    results = []
    for p in personas:
        print(f"  Avaliando {p.agent_id}...", end="\r")
        try:
            r = evaluate_funnel(p, scenario)
        except Exception as exc:
            print(f"\n  [ERRO] {p.agent_id}: {exc}")
            r = FunnelResult(False, False, False, False, False, "awareness", "need_lack", 0, "erro tecnico", "", 0)
        results.append(r)
    print(f"  Avaliacoes completadas: {len(results)}")

    results = apply_word_of_mouth(personas, results)

    # Metricas
    total = len(results)
    awareness = sum(1 for r in results if r.awareness)
    interest = sum(1 for r in results if r.interest)
    consideration = sum(1 for r in results if r.consideration)
    intent = sum(1 for r in results if r.intent)
    purchased = sum(1 for r in results if r.purchased)

    funnel_metrics = {
        "total": total,
        "awareness": awareness,
        "interest": interest,
        "consideration": consideration,
        "intent": intent,
        "purchased": purchased,
        "awareness_rate": awareness / total,
        "interest_rate": interest / awareness if awareness else 0,
        "consideration_rate": consideration / interest if interest else 0,
        "intent_rate": intent / consideration if consideration else 0,
        "conversion_rate": purchased / intent if intent else 0,
        "overall_conversion": purchased / total,
    }

    # Rejeicoes
    rejection_counts = {}
    for r in results:
        if not r.purchased:
            reason = r.rejection_reason
            rejection_counts[reason] = rejection_counts.get(reason, 0) + 1

    avg_sentiment = sum(r.sentiment for r in results) / total
    avg_budget_impact = sum(r.budget_impact_pct for r in results) / total

    return {
        "scenario": scenario.__dict__,
        "timestamp": datetime.now().isoformat(),
        "funnel": funnel_metrics,
        "avg_sentiment": avg_sentiment,
        "avg_budget_impact_pct": avg_budget_impact,
        "rejection_counts": rejection_counts,
        "agents": [
            {
                "agent_id": p.agent_id,
                "owner_name": p.owner_name,
                "segment": p.segment,
                "monthly_revenue_brl": p.monthly_revenue_brl,
                "marketing_budget_brl": p.marketing_budget_brl,
                "security_budget_brl": p.security_budget_brl,
                "has_existing_security": p.has_existing_security,
                "risk_profile": p.risk_profile,
                "day_of_month": p.day_of_month,
                "season": p.season,
                "recent_event": p.recent_event,
                "wtp_brl": p.wtp_brl,
                "funnel": {
                    "awareness": r.awareness,
                    "interest": r.interest,
                    "consideration": r.consideration,
                    "intent": r.intent,
                    "purchased": r.purchased,
                    "rejection_stage": r.rejection_stage,
                    "rejection_reason": r.rejection_reason,
                },
                "budget_impact_pct": r.budget_impact_pct,
                "key_objection": r.key_objection,
                "social_post": r.social_post,
                "sentiment": r.sentiment,
            }
            for p, r in zip(personas, results)
        ],
    }


# ---------------------------------------------------------------------------
# Relatorio
# ---------------------------------------------------------------------------

def build_report(all_results: list[dict]) -> str:
    lines = ["# Relatorio de Simulacoes Avancadas - Funil Bidirecional\n"]
    lines.append(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append("Metodologia: agentes empresariais com atributos realistas avaliam oferta em 5 estagios; fase de boca a boca atualiza decisoes.\n\n")

    # DevinCriator
    lines.append("## DevinCriator / Owl Regent Studio\n\n")
    lines.append("| Cenario | Segmento | Awareness | Interest | Consideration | Intent | Compra | Conversao geral | Sentimento | Impacto budget | Principal rejeicao |\n")
    lines.append("|---------|----------|-----------|----------|---------------|--------|--------|-----------------|------------|----------------|---------------------|\n")
    for res in all_results:
        s = res["scenario"]
        if s["project"] != "devincriator":
            continue
        f = res["funnel"]
        main_rejection = max(res["rejection_counts"].items(), key=lambda x: x[1])[0] if res["rejection_counts"] else "-"
        lines.append(
            f"| {s['code']} | {s['target_segment']} | {f['awareness']} | {f['interest']} | {f['consideration']} | {f['intent']} | {f['purchased']} | "
            f"{f['overall_conversion']:.1%} | {res['avg_sentiment']:+.2f} | {res['avg_budget_impact_pct']:.1f}% | {main_rejection} |\n"
        )

    # SLZ
    lines.append("\n## SLZ N8N Stack\n\n")
    lines.append("| Cenario | Segmento | Awareness | Interest | Consideration | Intent | Agendamento/Compra | Conversao geral | Sentimento | Impacto budget | Principal rejeicao |\n")
    lines.append("|---------|----------|-----------|----------|---------------|--------|--------------------|-----------------|------------|----------------|---------------------|\n")
    for res in all_results:
        s = res["scenario"]
        if s["project"] != "slz_n8n":
            continue
        f = res["funnel"]
        main_rejection = max(res["rejection_counts"].items(), key=lambda x: x[1])[0] if res["rejection_counts"] else "-"
        lines.append(
            f"| {s['code']} | {s['target_segment']} | {f['awareness']} | {f['interest']} | {f['consideration']} | {f['intent']} | {f['purchased']} | "
            f"{f['overall_conversion']:.1%} | {res['avg_sentiment']:+.2f} | {res['avg_budget_impact_pct']:.1f}% | {main_rejection} |\n"
        )

    # Detalhes por cenario
    for res in all_results:
        s = res["scenario"]
        lines.append(f"\n### {s['code']} - {s['name']}\n")
        lines.append(f"- Produto: {s['product_name']}\n")
        lines.append(f"- Preco: R$ {s['price_brl']:,.2f} ({s['price_model']})\n")
        lines.append(f"- Conversao geral: {res['funnel']['overall_conversion']:.1%}\n")
        lines.append(f"- Sentimento medio: {res['avg_sentiment']:+.2f}\n")
        lines.append(f"- Impacto medio no budget: {res['avg_budget_impact_pct']:.1f}%\n")
        lines.append(f"- Distribuicao de rejeicoes: {res['rejection_counts']}\n")
        lines.append("\n**Exemplos de agentes:**\n")
        for agent in res["agents"][:3]:
            lines.append(
                f"- {agent['owner_name']} ({agent['segment']}): renda R$ {agent['monthly_revenue_brl']:,.2f}, "
                f"seguranca existente: {agent['has_existing_security']}, perfil: {agent['risk_profile']}, "
                f"decidiu: {'comprou/agendou' if agent['funnel']['purchased'] else 'nao comprou'} - {agent['key_objection']}\n"
            )

    return "".join(lines)


# ---------------------------------------------------------------------------
# Entry point para uso via import
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Use run_advanced_scenarios.py para executar cenarios configurados.")
