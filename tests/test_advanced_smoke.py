#!/usr/bin/env python3
"""Smoke test do framework avancado com 3 agentes."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.advanced_simulation import ScenarioConfig, run_scenario

scenario = ScenarioConfig(
    project="slz_n8n",
    code="SMOKE",
    name="Teste - Oficinas Mecanicas",
    product_name="SLZ Seguranca Inteligente para Oficinas",
    description="Sistema de seguranca com cameras, alarme e monitoramento 24h para oficinas em Sao Luis. Visita tecnica R$ 0,20.",
    price_brl=0.20,
    price_model="visit",
    target_segment="oficina",
    channel="word_of_mouth",
    value_proposition="Protege ferramentas e estoque da oficina.",
    pain_focus="Ferramentas caras desaparecem e oficinas ficam desprotegidas a noite.",
    num_agents=3,
)

result = run_scenario(scenario)
print(json.dumps(result["funnel"], indent=2, ensure_ascii=False))
print("Rejeicoes:", result["rejection_counts"])
for a in result["agents"]:
    print(f"{a['owner_name']}: renda {a['monthly_revenue_brl']:,.2f}, seg existente: {a['has_existing_security']}, comprou: {a['funnel']['purchased']}, motivo: {a['key_objection']}")
