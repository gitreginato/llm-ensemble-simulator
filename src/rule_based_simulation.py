#!/usr/bin/env python3
"""
Simulacao de mercado baseada em regras com ruído realista.

Nao usa LLM (evita instabilidade de APIs). Utiliza personas geradas por
advanced_simulation.generate_personas e aplica um modelo economico-behavioral
com parametros calibrados a partir da pesquisa de mercado.
"""

import json
import random
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.advanced_simulation import (
    ScenarioConfig,
    BusinessProfile,
    FunnelResult,
    generate_personas,
    apply_word_of_mouth,
)

ROOT = Path(__file__).parent.parent
OUTPUT_DIR = ROOT / "rule_based_results"
OUTPUT_DIR.mkdir(exist_ok=True)


@dataclass
class SegmentCalibration:
    """Parametros de calibracao por segmento."""
    awareness_base: float = 0.85
    interest_base: float = 0.55
    consideration_base: float = 0.45
    intent_base: float = 0.40
    purchase_base: float = 0.35
    price_sensitivity: float = 1.0  # multiplicador de impacto de preco
    security_need: float = 0.5      # 0-1
    branding_need: float = 0.5      # 0-1
    trust_local_need: float = 0.5   # bonus para trust_local_providers


# Calibracao baseada nos achados da pesquisa
SEGMENT_CALIBRATION = {
    # DevinCriator segments
    "padaria": SegmentCalibration(
        awareness_base=0.88, interest_base=0.60, consideration_base=0.48,
        intent_base=0.42, purchase_base=0.38, price_sensitivity=1.1,
        security_need=0.2, branding_need=0.75, trust_local_need=0.55
    ),
    "confeitaria": SegmentCalibration(
        awareness_base=0.86, interest_base=0.58, consideration_base=0.50,
        intent_base=0.45, purchase_base=0.40, price_sensitivity=1.0,
        security_need=0.2, branding_need=0.78, trust_local_need=0.55
    ),
    "food_truck": SegmentCalibration(
        awareness_base=0.82, interest_base=0.68, consideration_base=0.55,
        intent_base=0.50, purchase_base=0.45, price_sensitivity=0.95,
        security_need=0.1, branding_need=0.85, trust_local_need=0.45
    ),
    "lava_jato": SegmentCalibration(
        awareness_base=0.78, interest_base=0.48, consideration_base=0.38,
        intent_base=0.32, purchase_base=0.28, price_sensitivity=1.05,
        security_need=0.3, branding_need=0.55, trust_local_need=0.50
    ),
    "oficina": SegmentCalibration(
        awareness_base=0.78, interest_base=0.55, consideration_base=0.45,
        intent_base=0.40, purchase_base=0.35, price_sensitivity=1.0,
        security_need=0.85, branding_need=0.55, trust_local_need=0.60
    ),
    "bar": SegmentCalibration(
        awareness_base=0.80, interest_base=0.50, consideration_base=0.40,
        intent_base=0.35, purchase_base=0.30, price_sensitivity=1.0,
        security_need=0.6, branding_need=0.60, trust_local_need=0.50
    ),
    "lanchonete": SegmentCalibration(
        awareness_base=0.82, interest_base=0.52, consideration_base=0.42,
        intent_base=0.36, purchase_base=0.32, price_sensitivity=1.0,
        security_need=0.4, branding_need=0.65, trust_local_need=0.50
    ),
    "hamburgueria": SegmentCalibration(
        awareness_base=0.85, interest_base=0.62, consideration_base=0.52,
        intent_base=0.46, purchase_base=0.42, price_sensitivity=0.95,
        security_need=0.3, branding_need=0.80, trust_local_need=0.50
    ),
    "salao": SegmentCalibration(
        awareness_base=0.83, interest_base=0.50, consideration_base=0.40,
        intent_base=0.35, purchase_base=0.30, price_sensitivity=1.1,
        security_need=0.3, branding_need=0.70, trust_local_need=0.55
    ),
    "barbearia": SegmentCalibration(
        awareness_base=0.80, interest_base=0.52, consideration_base=0.42,
        intent_base=0.36, purchase_base=0.32, price_sensitivity=1.0,
        security_need=0.2, branding_need=0.65, trust_local_need=0.55
    ),
    "loja_roupas": SegmentCalibration(
        awareness_base=0.85, interest_base=0.55, consideration_base=0.45,
        intent_base=0.40, purchase_base=0.35, price_sensitivity=1.05,
        security_need=0.6, branding_need=0.75, trust_local_need=0.50
    ),
    "loja_calcados": SegmentCalibration(
        awareness_base=0.84, interest_base=0.53, consideration_base=0.43,
        intent_base=0.38, purchase_base=0.33, price_sensitivity=1.05,
        security_need=0.55, branding_need=0.72, trust_local_need=0.50
    ),

    # SLZ N8N segments
    "carros_usados": SegmentCalibration(
        awareness_base=0.86, interest_base=0.72, consideration_base=0.60,
        intent_base=0.55, purchase_base=0.50, price_sensitivity=0.6,
        security_need=0.98, branding_need=0.10, trust_local_need=0.55
    ),
    "autopecas": SegmentCalibration(
        awareness_base=0.80, interest_base=0.55, consideration_base=0.45,
        intent_base=0.40, purchase_base=0.35, price_sensitivity=0.7,
        security_need=0.80, branding_need=0.15, trust_local_need=0.55
    ),
    "concessionaria": SegmentCalibration(
        awareness_base=0.82, interest_base=0.60, consideration_base=0.50,
        intent_base=0.45, purchase_base=0.40, price_sensitivity=0.5,
        security_need=0.95, branding_need=0.20, trust_local_need=0.50
    ),
    "residencia": SegmentCalibration(
        awareness_base=0.70, interest_base=0.45, consideration_base=0.35,
        intent_base=0.30, purchase_base=0.25, price_sensitivity=0.9,
        security_need=0.75, branding_need=0.0, trust_local_need=0.45
    ),
    "farmacia": SegmentCalibration(
        awareness_base=0.78, interest_base=0.48, consideration_base=0.38,
        intent_base=0.32, purchase_base=0.28, price_sensitivity=0.8,
        security_need=0.70, branding_need=0.25, trust_local_need=0.55
    ),
    "mercearia": SegmentCalibration(
        awareness_base=0.72, interest_base=0.40, consideration_base=0.30,
        intent_base=0.25, purchase_base=0.22, price_sensitivity=1.0,
        security_need=0.55, branding_need=0.30, trust_local_need=0.55
    ),
    "lava_jato": SegmentCalibration(
        awareness_base=0.80, interest_base=0.60, consideration_base=0.50,
        intent_base=0.44, purchase_base=0.38, price_sensitivity=0.8,
        security_need=0.80, branding_need=0.55, trust_local_need=0.55
    ),
}


def _clip(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _noise(std: float = 0.08) -> float:
    return random.gauss(0, std)


def evaluate_rule_based(profile: BusinessProfile, scenario: ScenarioConfig) -> FunnelResult:
    """Avalia o funil usando regras calibradas + ruido realista."""
    cal = SEGMENT_CALIBRATION.get(profile.segment, SegmentCalibration())
    relevant_budget = profile.marketing_budget_brl if scenario.project == "devincriator" else profile.security_budget_brl
    budget_impact = (scenario.price_brl / relevant_budget * 100) if relevant_budget > 0 else 999.0

    # ----- Awareness -----
    # Alguns ignoram por distração; channel e dia do mês afetam levemente
    awareness_score = cal.awareness_base
    awareness_score -= 0.10 if scenario.channel == "word_of_mouth" else 0.0  # menos alcance
    awareness_score -= 0.05 if profile.day_of_month > 25 else 0.0
    awareness_score += _noise(0.10)
    awareness = random.random() < _clip(awareness_score)

    if not awareness:
        return _make_result(awareness, False, False, False, False, "awareness", "need_lack", budget_impact, profile, scenario)

    # ----- Interest -----
    # Match entre oferta e necessidade do segmento
    need = cal.branding_need if scenario.project == "devincriator" else cal.security_need
    interest_score = cal.interest_base
    interest_score += 0.15 * need
    interest_score -= 0.20 * cal.price_sensitivity * max(0, budget_impact - 50) / 100
    interest_score += 0.08 * (profile.tech_savviness - 5) / 5
    interest_score += 0.05 * (profile.trust_local_providers - 5) / 5 * cal.trust_local_need
    interest_score += _noise(0.10)
    interest = random.random() < _clip(interest_score)

    if not interest:
        return _make_result(True, interest, False, False, False, "interest", "need_lack", budget_impact, profile, scenario)

    # ----- Consideration -----
    # Avaliacao seria: preço <= WTP, budget impact aceitavel, solucao existente nao é boa
    existing_ok = False
    if scenario.project == "slz_n8n":
        if profile.has_existing_security == "full_system" and profile.existing_security_satisfaction >= 7:
            existing_ok = True
        elif profile.has_existing_security == "alarm_monitored" and profile.existing_security_satisfaction >= 8:
            existing_ok = True
    else:
        # branding: existing solution nao aplica diretamente, mas falta de necessidade sim
        existing_ok = False

    consideration_score = cal.consideration_base
    consideration_score += 0.20 * need
    consideration_score -= 0.25 * cal.price_sensitivity * max(0, budget_impact - 40) / 100
    consideration_score -= 0.30 if existing_ok else 0.0
    consideration_score += 0.10 if profile.recent_event in ("theft", "competitor_new") else 0.0
    consideration_score += 0.08 if profile.risk_profile == "crisis_driven" and profile.recent_event == "theft" else 0.0
    consideration_score += _noise(0.10)
    consideration = random.random() < _clip(consideration_score)

    if not consideration:
        reason = "existing_solution" if existing_ok else ("budget" if budget_impact > 120 else "timing")
        return _make_result(True, True, consideration, False, False, "consideration", reason, budget_impact, profile, scenario)

    # ----- Intent -----
    # Decisao de querer, antes do check final
    intent_score = cal.intent_base
    intent_score += 0.15 * need
    intent_score -= 0.15 * cal.price_sensitivity * max(0, budget_impact - 50) / 100
    intent_score -= 0.10 if profile.day_of_month > 25 and profile.season != "high" else 0.0
    intent_score += 0.12 if profile.recent_event == "theft" else 0.0
    intent_score += 0.08 if profile.risk_profile == "innovator" else 0.0
    intent_score += 0.06 * (profile.trust_local_providers - 5) / 5
    intent_score += _noise(0.10)
    intent = random.random() < _clip(intent_score)

    if not intent:
        reason = "budget" if budget_impact > 120 else ("timing" if profile.day_of_month > 20 else "skepticism")
        return _make_result(True, True, True, intent, False, "intent", reason, budget_impact, profile, scenario)

    # ----- Purchased -----
    # Check final: preço, budget, timing, solucao existente
    if scenario.price_brl > profile.wtp_brl:
        return _make_result(True, True, True, True, False, "intent", "budget", budget_impact, profile, scenario)
    if budget_impact > 130:
        return _make_result(True, True, True, True, False, "intent", "budget", budget_impact, profile, scenario)
    if existing_ok:
        return _make_result(True, True, True, True, False, "intent", "existing_solution", budget_impact, profile, scenario)
    if profile.day_of_month > 28 and profile.season == "low":
        return _make_result(True, True, True, True, False, "intent", "timing", budget_impact, profile, scenario)

    purchase_score = cal.purchase_base
    purchase_score += 0.10 * need
    purchase_score += 0.08 if profile.recent_event == "theft" else 0.0
    purchase_score += 0.06 if profile.risk_profile in ("innovator", "crisis_driven") else 0.0
    purchase_score -= 0.08 if profile.risk_profile == "conservative" else 0.0
    purchase_score += _noise(0.08)
    purchased = random.random() < _clip(purchase_score)

    if not purchased:
        reason = "skepticism" if profile.trust_local_providers < 5 else "timing"
        return _make_result(True, True, True, True, False, "intent", reason, budget_impact, profile, scenario)

    return _make_result(True, True, True, True, True, "none", "none", budget_impact, profile, scenario)


def _make_result(
    awareness: bool,
    interest: bool,
    consideration: bool,
    intent: bool,
    purchased: bool,
    rejection_stage: str,
    rejection_reason: str,
    budget_impact_pct: float,
    profile: BusinessProfile,
    scenario: ScenarioConfig,
) -> FunnelResult:
    key_objection, social_post, sentiment = _generate_text(
        awareness, interest, consideration, intent, purchased, rejection_reason,
        budget_impact_pct, profile, scenario
    )
    return FunnelResult(
        awareness=awareness,
        interest=interest,
        consideration=consideration,
        intent=intent,
        purchased=purchased,
        rejection_stage=rejection_stage,
        rejection_reason=rejection_reason,
        budget_impact_pct=budget_impact_pct,
        key_objection=key_objection,
        social_post=social_post,
        sentiment=sentiment,
    )


def _generate_text(
    awareness: bool,
    interest: bool,
    consideration: bool,
    intent: bool,
    purchased: bool,
    rejection_reason: str,
    budget_impact_pct: float,
    profile: BusinessProfile,
    scenario: ScenarioConfig,
) -> tuple[str, str, float]:
    """Gera objeto, post e sentimento via templates."""
    sentiment = 0.0
    if purchased:
        sentiment = random.uniform(0.3, 0.8)
    elif intent:
        sentiment = random.uniform(0.0, 0.3)
    elif consideration:
        sentiment = random.uniform(-0.1, 0.2)
    elif interest:
        sentiment = random.uniform(-0.2, 0.1)
    else:
        sentiment = random.uniform(-0.4, 0.0)

    # Objeções por motivo
    objections = {
        "budget": [
            "Preço alto para meu orçamento",
            "Não cabe no budget deste mês",
            "Vou precisar parcelar ou adiar",
            "Investimento maior do que posso fazer agora",
        ],
        "timing": [
            "Não é o momento certo para investir",
            "Estou fechando o mês, depois eu vejo",
            "Agora estou com fluxo apertado",
            "Vou esperar a alta temporada",
        ],
        "existing_solution": [
            "Já tenho uma solução que me atende",
            "Não vejo vantagem em trocar agora",
            "Meu sistema atual é suficiente",
            "Já resolvi isso com outro fornecedor",
        ],
        "skepticism": [
            "Não sei se é confiável",
            "Preciso ver cases de quem já usou",
            "Parece bom demais para ser verdade",
            "Quero recomendação de alguém da área",
        ],
        "complexity": [
            "Parece complicado de operar",
            "Não tenho tempo para aprender",
            "Vai dar muito trabalho implementar",
        ],
        "need_lack": [
            "Não vejo necessidade agora",
            "Não é prioridade para meu negócio",
            "Estou bem assim",
        ],
    }

    key_objection = random.choice(objections.get(rejection_reason, ["Não se aplicou"]))
    if purchased:
        key_objection = ""

    # Posts sociais
    post_templates = {
        "purchased": [
            "Vou testar essa proposta, parece fazer sentido para o meu negocio.",
            "Agendei a visita, vamos ver no que da.",
            "Interessante, vou dar uma chance.",
        ],
        "intent": [
            "Gostei da ideia, mas preciso pensar no custo total.",
            "Parece util, vou comparar opcoes.",
        ],
        "consideration": [
            "Vi o anuncio, mas nao sei se vale o investimento.",
            "Interessante, mas tenho que verificar meu budget.",
        ],
        "interest": [
            "Recebi uma procura sobre isso hoje.",
            "Vi passando, mas nao parei para analisar.",
        ],
        "default": [
            "Nao vi ainda, muita coisa para fazer.",
            "Nao chama minha atencao.",
        ],
    }

    if purchased:
        social_post = random.choice(post_templates["purchased"])
    elif intent:
        social_post = random.choice(post_templates["intent"])
    elif consideration:
        social_post = random.choice(post_templates["consideration"])
    elif interest:
        social_post = random.choice(post_templates["interest"])
    else:
        social_post = random.choice(post_templates["default"])

    return key_objection, social_post, sentiment


def run_scenario_rule_based(scenario: ScenarioConfig, seed: Optional[int] = None) -> dict:
    if seed is not None:
        random.seed(seed)

    personas = generate_personas(scenario.target_segment, scenario.num_agents)
    results = []
    for p in personas:
        r = evaluate_rule_based(p, scenario)
        results.append(r)

    results = apply_word_of_mouth(personas, results)

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
                "existing_security_satisfaction": p.existing_security_satisfaction,
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


if __name__ == "__main__":
    print("Use run_rule_based_scenarios.py para executar cenarios configurados.")
