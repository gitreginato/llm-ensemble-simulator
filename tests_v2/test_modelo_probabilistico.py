"""Testes para modelo_probabilistico.py."""
import random

import numpy as np

from simulation_army_v2.modelo_probabilistico import (
    NICHOS_PERENES,
    PESOS,
    PersonaInput,
    amostrar_decisao,
    beta_posterior,
    calcular_prob_agendou,
    extrair_features,
    gerar_objecoes,
    ic_bayesiano,
    monte_carlo,
    sigmoid,
    validar_modelo,
)


def test_sigmoid_extremos():
    assert sigmoid(0) == 0.5
    assert sigmoid(10) > 0.9999
    assert sigmoid(-10) < 0.0001


def test_sigmoid_estavel_negativo():
    """Nao deve dar overflow para valores muito negativos."""
    assert 0.0 <= sigmoid(-100) <= 1.0
    assert sigmoid(-100) < 1e-30


def test_pesos_tem_bias():
    assert "bias" in PESOS
    assert PESOS["bias"] < 0  # baseline negativo


def test_persona_theft_tem_prob_alta():
    p = PersonaInput(
        segment="loja_roupas", risk_profile="crisis_driven",
        recent_event="theft", has_existing_security="none",
        wtp_brl=500, bairro_p_theft=0.20,
    )
    prob = calcular_prob_agendou(p)
    assert prob > 0.80, f"theft deveria ter P>80%, got {prob}"


def test_persona_full_system_sat_tem_prob_baixa():
    p = PersonaInput(
        segment="farmacia", risk_profile="pragmatic",
        recent_event="none", has_existing_security="full_system",
        wtp_brl=700, bairro_p_theft=0.05,
    )
    prob = calcular_prob_agendou(p)
    assert prob < 0.10, f"full_system sem theft deveria ter P<10%, got {prob}"


def test_persona_sem_drivers_tem_prob_baixa():
    p = PersonaInput(
        segment="loja_roupas", risk_profile="pragmatic",
        recent_event="none", has_existing_security="full_system",
        wtp_brl=400, bairro_p_theft=0.05,
    )
    prob = calcular_prob_agendou(p)
    assert prob < 0.05, f"sem drivers deveria ter P<5%, got {prob}"


def test_extrair_features_completo():
    p = PersonaInput(
        segment="farmacia", risk_profile="crisis_driven",
        recent_event="theft", has_existing_security="none",
        wtp_brl=15000, bairro_p_theft=0.20,
        budget_mensal=500, mensalidade=294, ticket_medio_36m=10584,
        precisa_area_externa=True, concorrencia_local_instalada=True,
    )
    feats = extrair_features(p)
    assert feats["x_theft"] == 1.0
    assert feats["x_no_security"] == 1.0
    assert feats["x_crisis"] == 1.0
    assert feats["x_budget_ok"] == 1.0  # 500 >= 294
    assert feats["x_nicho_perene"] == 1.0  # farmacia e perene
    assert feats["x_bairro_risco"] == 0.20
    assert feats["x_ticket_adequado"] == 1.0  # 15000 >= 10584
    assert feats["x_precisa_externa"] == 1.0
    assert feats["x_concorrencia_local"] == 1.0


def test_area_externa_reduz_prob():
    """Persona que precisa de area externa tem P menor que sem area externa."""
    p_sem_externa = PersonaInput(
        segment="farmacia", risk_profile="pragmatic",
        recent_event="none", has_existing_security="none",
        wtp_brl=15000, bairro_p_theft=0.10,
        budget_mensal=500, mensalidade=294, ticket_medio_36m=10584,
        precisa_area_externa=False, concorrencia_local_instalada=False,
    )
    p_com_externa = PersonaInput(
        segment="farmacia", risk_profile="pragmatic",
        recent_event="none", has_existing_security="none",
        wtp_brl=15000, bairro_p_theft=0.10,
        budget_mensal=500, mensalidade=294, ticket_medio_36m=10584,
        precisa_area_externa=True, concorrencia_local_instalada=False,
    )
    prob_sem = calcular_prob_agendou(p_sem_externa)
    prob_com = calcular_prob_agendou(p_com_externa)
    assert prob_com < prob_sem, \
        f"Area externa deveria reduzir P: sem={prob_sem:.3f} com={prob_com:.3f}"


def test_concorrencia_reduz_prob():
    """Persona com concorrencia local tem P menor que sem."""
    p_sem = PersonaInput(
        segment="farmacia", risk_profile="pragmatic",
        recent_event="none", has_existing_security="none",
        wtp_brl=15000, bairro_p_theft=0.10,
        budget_mensal=500, mensalidade=294, ticket_medio_36m=10584,
        precisa_area_externa=False, concorrencia_local_instalada=False,
    )
    p_com = PersonaInput(
        segment="farmacia", risk_profile="pragmatic",
        recent_event="none", has_existing_security="none",
        wtp_brl=15000, bairro_p_theft=0.10,
        budget_mensal=500, mensalidade=294, ticket_medio_36m=10584,
        precisa_area_externa=False, concorrencia_local_instalada=True,
    )
    prob_sem = calcular_prob_agendou(p_sem)
    prob_com = calcular_prob_agendou(p_com)
    assert prob_com < prob_sem, \
        f"Concorrencia deveria reduzir P: sem={prob_sem:.3f} com={prob_com:.3f}"


def test_amostrar_decisao_distribuicao():
    """Persona com P alta deve agendar na maioria das amostras."""
    p = PersonaInput(
        segment="loja_roupas", risk_profile="crisis_driven",
        recent_event="theft", has_existing_security="none",
        wtp_brl=500, bairro_p_theft=0.20,
    )
    rng = random.Random(42)
    agendaram = sum(1 for _ in range(1000) if amostrar_decisao(p, rng) == "agendou")
    assert agendaram > 800, f"Esperado >800 agendamentos, got {agendaram}"


def test_amostrar_decisao_persona_fria():
    """Persona fria raramente agenda."""
    p = PersonaInput(
        segment="oficina", risk_profile="pragmatic",
        recent_event="none", has_existing_security="full_system",
        wtp_brl=400, bairro_p_theft=0.05,
    )
    rng = random.Random(42)
    agendaram = sum(1 for _ in range(1000) if amostrar_decisao(p, rng) == "agendou")
    assert agendaram < 50, f"Esperado <50 agendamentos, got {agendaram}"


def test_gerar_objecoes_budget():
    p = PersonaInput(
        segment="mercearia", risk_profile="pragmatic",
        recent_event="none", has_existing_security="full_system",
        wtp_brl=150, bairro_p_theft=0.05,
    )
    rng = random.Random(42)
    objecoes = gerar_objecoes(p, "visualizou", rng)
    assert "budget" in objecoes


def test_gerar_objecoes_existing_solution():
    p = PersonaInput(
        segment="farmacia", risk_profile="pragmatic",
        recent_event="none", has_existing_security="full_system",
        wtp_brl=700, bairro_p_theft=0.05,
    )
    rng = random.Random(42)
    objecoes = gerar_objecoes(p, "visualizou", rng)
    assert "existing_solution" in objecoes


def test_beta_posterior_shape():
    amostras = beta_posterior(5, 5, n_amostras=1000)
    assert len(amostras) == 1000
    assert 0 <= amostras.min() <= amostras.max() <= 1


def test_ic_bayesiano():
    lo, hi = ic_bayesiano(5, 10)
    assert 0 < lo < hi < 1
    assert lo < 0.5 < hi  # 5/10 = 50%, IC deve conter 0.5


def test_monte_carlo_distribuicao():
    personas = [
        PersonaInput(
            segment="loja_roupas", risk_profile="crisis_driven",
            recent_event="theft", has_existing_security="none",
            wtp_brl=500, bairro_p_theft=0.20,
        )
        for _ in range(100)
    ]
    resultado = monte_carlo(personas, n_seeds=50)
    assert resultado["conversao_mediana"] > 0.80
    assert resultado["conversao_p5"] > 0.70
    assert resultado["conversao_p95"] > 0.85


def test_validar_modelo_rodar():
    """Valida modelo contra dataset real. Deve rodar sem erro."""
    resultados = validar_modelo()
    assert len(resultados) > 0
    # Verifica que grupos com theft + no_security tem prob prevista alta
    for key, dados in resultados.items():
        if "theft" in key and "none" in key:
            assert dados["prob_prevista_media"] > 0.5, f"{key}: prob={dados['prob_prevista_media']}"
    # theft com full_system pode ser menor (cliente ja tem seguranca)
    for key, dados in resultados.items():
        if "theft" in key:
            assert dados["prob_prevista_media"] > 0.3, f"{key}: prob={dados['prob_prevista_media']}"


def test_nichos_perene_definido():
    assert "farmacia" in NICHOS_PERENES
    assert "autopecas" in NICHOS_PERENES
    assert "clinica" in NICHOS_PERENES
    assert "loja_roupas" not in NICHOS_PERENES
    assert "bar" not in NICHOS_PERENES
    # Novos nichos perenes
    assert "estacionamento" in NICHOS_PERENES
    assert "mecanica_diesel" in NICHOS_PERENES
    assert "laboratorio" in NICHOS_PERENES
    assert "clinica_veterinaria" in NICHOS_PERENES
    assert "estetica" in NICHOS_PERENES
    assert "estudio_tatuagem" in NICHOS_PERENES
