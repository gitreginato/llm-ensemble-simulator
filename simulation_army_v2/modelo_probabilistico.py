"""Modelo probabilistico de decisao de compra calibrado nos 142 personas reais.

P(agendou) = sigmoid(w . x + bias)

Features (x):
  x_theft:          1 se recent_event == 'theft', else 0
  x_renovation:     1 se recent_event == 'renovation', else 0
  x_no_security:    1 se has_existing_security == 'none', else 0
  x_diy_cameras:    1 se has_existing_security == 'diy_cameras', else 0
  x_crisis:         1 se risk_profile == 'crisis_driven', else 0
  x_innovator:      1 se risk_profile == 'innovator', else 0
  x_budget_ok:      1 se budget_mensal >= mensalidade, else 0
  x_nicho_perene:   1 se segment e perene, else 0 (perene = mais estavel, mais propenso a contratar)
  x_bairro_risco:   p_theft_base do bairro (0.05 a 0.25)
  x_ticket_adequado: 1 se WTP >= ticket_medio_36m, else 0 (cliente aguenta compromisso 3 anos)

Pesos (w) calibrados manualmente a partir dos crosstabs reais (142 personas):

Crosstab real (evidencia S):
  theft:           11/12 = 92% agendou  -> w_theft = +3.0 (sigmoid(3) = 0.95)
  renovation:       4/32 = 12% agendou  -> w_renovation = +0.5
  none (event):     2/49 = 4% agendou   -> baseline
  no_security:      8/24 = 33% agendou  -> w_no_security = +1.0
  diy_cameras:      5/48 = 10% agendou  -> w_diy = +0.3
  full_system:      2/37 = 5% agendou   -> baseline (negativo)
  crisis_driven:    7/34 = 21% agendou  -> w_crisis = +0.5
  innovator:        2/14 = 14% agendou  -> w_innovator = +0.3
  pragmatic:        5/58 = 9% agendou   -> baseline
  budget_ok:        92% podem pagar     -> w_budget_ok = +0.1
  nicho_perene:     perenes convertem mais (estabilidade) -> w_perene = +0.4
  bairro_risco:     continuo 0.05-0.25  -> w_bairro = +1.0
  ticket_adequado:  WTP >= ticket 36m   -> w_ticket = +0.3

Bias: -3.2 (baseline P(agendou) ~ 4% sem nenhum driver positivo)
"""
from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

# Pesos calibrados manualmente a partir dos crosstabs reais (142 personas)
PESOS = {
    "bias": -3.2,
    "x_theft": 3.0,
    "x_renovation": 0.5,
    "x_no_security": 1.0,
    "x_diy_cameras": 0.3,
    "x_crisis": 0.5,
    "x_innovator": 0.3,
    "x_budget_ok": 0.1,
    "x_nicho_perene": 0.4,
    "x_bairro_risco": 1.0,
    "x_ticket_adequado": 0.3,
    # Limitacoes EMIVE (pesos negativos = reduzem P(agendou))
    "x_precisa_externa": -0.8,      # cliente quer camera externa, EMIVE nao tem
    "x_concorrencia_local": -0.5,   # instalador local ja atua na regiao
}

# Nichos perenes: derivado de SEGMENT_BASELINES_V5["perene"] (unica fonte de verdade)
# Import lazy para evitar circular import
def _carregar_nichos_perenes() -> set[str]:
    from simulation_army_v2.personas_v5 import SEGMENT_BASELINES_V5
    return {seg for seg, base in SEGMENT_BASELINES_V5.items() if base.get("perene", False)}

NICHOS_PERENES = _carregar_nichos_perenes()


@dataclass
class PersonaInput:
    """Input do modelo probabilistico para uma persona."""
    segment: str
    risk_profile: str
    recent_event: str
    has_existing_security: str
    wtp_brl: float
    bairro: str = "unknown"
    bairro_p_theft: float = 0.10
    budget_mensal: float = 0.0
    mensalidade: float = 294.0
    ticket_medio_36m: float = 10584.0  # 294 * 36
    precisa_area_externa: bool = False
    concorrencia_local_instalada: bool = False


def sigmoid(x: float) -> float:
    """Funcao sigmoid estavel numericamente."""
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def extrair_features(p: PersonaInput) -> dict[str, float]:
    """Extrai vetor de features da persona."""
    return {
        "x_theft": 1.0 if p.recent_event == "theft" else 0.0,
        "x_renovation": 1.0 if p.recent_event == "renovation" else 0.0,
        "x_no_security": 1.0 if p.has_existing_security == "none" else 0.0,
        "x_diy_cameras": 1.0 if p.has_existing_security == "diy_cameras" else 0.0,
        "x_crisis": 1.0 if p.risk_profile == "crisis_driven" else 0.0,
        "x_innovator": 1.0 if p.risk_profile == "innovator" else 0.0,
        "x_budget_ok": 1.0 if p.budget_mensal >= p.mensalidade else 0.0,
        "x_nicho_perene": 1.0 if p.segment in NICHOS_PERENES else 0.0,
        "x_bairro_risco": p.bairro_p_theft,
        "x_ticket_adequado": 1.0 if p.wtp_brl >= p.ticket_medio_36m else 0.0,
        "x_precisa_externa": 1.0 if p.precisa_area_externa else 0.0,
        "x_concorrencia_local": 1.0 if p.concorrencia_local_instalada else 0.0,
    }


def calcular_prob_agendou(p: PersonaInput) -> float:
    """Calcula P(agendou) com sigmoid."""
    features = extrair_features(p)
    z = PESOS["bias"]
    for feat, value in features.items():
        z += PESOS[feat] * value
    return sigmoid(z)


def amostrar_decisao(p: PersonaInput, rng: random.Random) -> str:
    """Amostra decisao da distribuicao probabilistica."""
    p_agendou = calcular_prob_agendou(p)
    p_clicou = 0.02
    p_ignorou = 0.01
    # Cap p_agendou so that all probabilities sum to <= 1.0.
    # Without this, when p_agendou > 0.97, p_clicou and p_ignorou
    # get squeezed and "ignorou"/"visualizou" become unreachable.
    p_agendou = min(p_agendou, 1.0 - p_clicou - p_ignorou)
    p_visualizou = max(0.0, 1.0 - p_agendou - p_clicou - p_ignorou)
    r = rng.random()
    if r < p_agendou:
        return "agendou"
    elif r < p_agendou + p_clicou:
        return "clicou"
    elif r < p_agendou + p_clicou + p_ignorou:
        return "ignorou"
    return "visualizou"


def gerar_objecoes(p: PersonaInput, decisao: str, rng: random.Random) -> list[str]:
    """Gera objecoes baseadas no perfil e na decisao.
    Calibrado nos dados reais: existing_solution (111/142=78%), skepticism (44=31%),
    budget (42=30%), need_lack (29=20%), timing (17=12%), complexity (8=6%).
    Novas objecoes: contract_fear (medo de fidelidade 3 anos), ticket_alto (compromisso total alto).
    """
    objecoes = []
    # existing_solution: se tem seguranca e nao agendou
    if p.has_existing_security in ("full_system", "alarm_monitored") and decisao != "agendou":
        objecoes.append("existing_solution")
    elif p.has_existing_security == "diy_cameras" and decisao != "agendou" and rng.random() < 0.5:
        objecoes.append("existing_solution")
    # budget: se budget mensal < mensalidade
    if p.budget_mensal < p.mensalidade:
        objecoes.append("budget")
    elif p.budget_mensal < p.mensalidade * 1.5 and rng.random() < 0.3:
        objecoes.append("budget")
    # ticket_alto: se WTP < ticket medio 36 meses (nao aguenta compromisso total)
    if p.wtp_brl < p.ticket_medio_36m and decisao != "agendou":
        objecoes.append("ticket_alto")
    # contract_fear: medo de fidelidade 3 anos com multa
    # Mais forte em volateis e pragmatic/conservative
    if p.segment not in NICHOS_PERENES and rng.random() < 0.4:
        objecoes.append("contract_fear")
    elif p.risk_profile in ("pragmatic", "conservative") and rng.random() < 0.3:
        objecoes.append("contract_fear")
    # skepticism: se risk_profile pragmatic ou conservative sem theft
    if p.risk_profile in ("pragmatic", "conservative") and p.recent_event != "theft":
        if rng.random() < 0.4:
            objecoes.append("skepticism")
    # need_lack: se nicho volatil e sem theft
    if p.segment not in NICHOS_PERENES and p.recent_event != "theft":
        if rng.random() < 0.3:
            objecoes.append("need_lack")
    # timing: se slow_month ou competitor_new
    if p.recent_event in ("slow_month", "competitor_new"):
        objecoes.append("timing")
    # complexity: raro
    if rng.random() < 0.06:
        objecoes.append("complexity")
    # area_externa: cliente precisa de camera externa, EMIVE so tem interno
    if p.precisa_area_externa and decisao != "agendou":
        objecoes.append("area_externa")
    # concorrencia_local: instalador local ja atua
    if p.concorrencia_local_instalada and decisao != "agendou" and rng.random() < 0.5:
        objecoes.append("concorrencia_local")
    return objecoes if objecoes else (["existing_solution"] if decisao != "agendou" else [])


def beta_posterior(sucessos: int, falhas: int, n_amostras: int = 10000,
                   rng: random.Random | None = None) -> np.ndarray:
    """Amostra da posterior Beta(sucessos+1, falhas+1) para taxa de conversao.
    Retorna array de n_amostras da distribuicao.
    """
    if rng is None:
        rng = random.Random(42)
    # ponytail: numpy.random nao aceita random.Random diretamente.
    # Usamos rng para gerar a seed do np.random.default_rng (reprodutivel).
    np_rng = np.random.default_rng(rng.randint(0, 2**31 - 1))
    alpha = sucessos + 1
    beta = falhas + 1
    return np_rng.beta(alpha, beta, size=n_amostras)


def ic_bayesiano(sucessos: int, total: int, confianca: float = 0.95) -> tuple[float, float]:
    """Intervalo credivel bayesiano para taxa de conversao.
    Usa posterior Beta(sucessos+1, total-sucessos+1).
    Com total=0, retorna (0.0, 1.0) representando incerteza maxima.
    Clamp sucessos to [0, total] para evitar beta <= 0.
    """
    if total <= 0:
        return 0.0, 1.0
    sucessos = max(0, min(sucessos, total))
    amostras = beta_posterior(sucessos, total - sucessos)
    alpha = (1 - confianca) / 2
    lo = float(np.percentile(amostras, alpha * 100))
    hi = float(np.percentile(amostras, (1 - alpha) * 100))
    return lo, hi


def monte_carlo(personas: list[PersonaInput], n_seeds: int = 100,
                base_seed: int = 42) -> dict[str, Any]:
    """Roda Monte Carlo: para cada seed, amostra decisao de cada persona.
    Retorna distribuicao de taxa de conversao.
    """
    conversoes = []
    for seed_offset in range(n_seeds):
        rng = random.Random(base_seed + seed_offset)
        agendaram = 0
        for p in personas:
            decisao = amostrar_decisao(p, rng)
            if decisao == "agendou":
                agendaram += 1
        conv = agendaram / len(personas) if personas else 0
        conversoes.append(conv)
    conversoes_arr = np.array(conversoes)
    return {
        "n_seeds": n_seeds,
        "n_personas": len(personas),
        "conversao_mediana": float(np.median(conversoes_arr)),
        "conversao_media": float(np.mean(conversoes_arr)),
        "conversao_p5": float(np.percentile(conversoes_arr, 5)),
        "conversao_p95": float(np.percentile(conversoes_arr, 95)),
        "conversao_std": float(np.std(conversoes_arr)),
        "todas_conversoes": conversoes,
    }


def validar_modelo(dataset_path: str = "results_v2/dataset_real.json") -> dict:
    """Valida o modelo contra os 142 personas reais.
    Compara P(agendou) prevista vs taxa real por grupo.
    """
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset nao encontrado: {dataset_path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    personas_data = data["personas"]

    # Agrupar por (recent_event, has_existing_security) e comparar
    grupos = defaultdict(lambda: {"real_agendou": 0, "real_total": 0, "prob_prevista": []})
    for p in personas_data:
        key = (p["recent_event"], p["has_existing_security"])
        grupos[key]["real_total"] += 1
        if p["decisao"] == "agendou":
            grupos[key]["real_agendou"] += 1
        persona_input = PersonaInput(
            segment=p["segment"],
            risk_profile=p["risk_profile"],
            recent_event=p["recent_event"],
            has_existing_security=p["has_existing_security"],
            wtp_brl=p["wtp_brl"],
        )
        prob = calcular_prob_agendou(persona_input)
        grupos[key]["prob_prevista"].append(prob)

    resultados = {}
    for key, dados in grupos.items():
        taxa_real = dados["real_agendou"] / dados["real_total"] if dados["real_total"] > 0 else 0
        prob_media = sum(dados["prob_prevista"]) / len(dados["prob_prevista"]) if dados["prob_prevista"] else 0
        resultados[f"{key[0]}_{key[1]}"] = {
            "n": dados["real_total"],
            "taxa_real": taxa_real,
            "prob_prevista_media": prob_media,
            "erro_absoluto": abs(taxa_real - prob_media),
        }
    return resultados
