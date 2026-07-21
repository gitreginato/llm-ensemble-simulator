#!/usr/bin/env python3
"""Testa um unico cenario com 10 agentes."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.advanced_simulation import ScenarioConfig, run_scenario

scenario = ScenarioConfig(
    project="slz_n8n",
    code="SLZ-AUTO-02",
    name="SLZ Seguranca Inteligente para Oficinas Mecanicas",
    product_name="SLZ Seguranca Inteligente - Oficinas Mecanicas",
    description="Sistema de seguranca inteligente para oficinas mecanicas em Sao Luis. Protege ferramentas, estoque de pecas, caixa e area de estacionamento. Cameras com analytics, alarme monitorado, alertas no WhatsApp. Visita tecnica R$ 0,20.",
    price_brl=0.20,
    price_model="visit",
    target_segment="oficina",
    channel="word_of_mouth",
    value_proposition="Evita perda de ferramentas caras e pecas do estoque, com monitoramento que realmente aciona resposta.",
    pain_focus="Oficinas tem ferramentas caras, pecas no estoque e pouca protecao fora do horario comercial.",
    num_agents=10,
)

import time
start = time.time()
result = run_scenario(scenario)
print(f"Tempo total: {time.time() - start:.1f}s")
print(json.dumps(result["funnel"], indent=2, ensure_ascii=False))
print("Rejeicoes:", result["rejection_counts"])
