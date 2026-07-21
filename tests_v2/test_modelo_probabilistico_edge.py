"""Edge case tests for modelo_probabilistico.py.

Covers: sigmoid overflow, unknown segment, all-zero features,
p_agendou > 0.98, unknown has_existing_security, ic_bayesiano n=0,
empty personas, beta_posterior 0/0, missing dataset file.
"""
import math
import random

import numpy as np
import pytest

from simulation_army_v2.modelo_probabilistico import (
    NICHOS_PERENES,
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


# 1. sigmoid overflow with extreme z values
def test_sigmoid_overflow_z_positivo_100():
    """sigmoid(+100) must not overflow and must return a valid probability."""
    result = sigmoid(100)
    assert 0.0 <= result <= 1.0
    assert math.isfinite(result)
    assert result == pytest.approx(1.0, abs=1e-10)


def test_sigmoid_overflow_z_negativo_100():
    """sigmoid(-100) must not overflow and must return a valid probability."""
    result = sigmoid(-100)
    assert 0.0 <= result <= 1.0
    assert math.isfinite(result)
    assert result < 1e-30


def test_sigmoid_overflow_z_1000():
    """sigmoid(+1000) and sigmoid(-1000) must not overflow."""
    assert math.isfinite(sigmoid(1000))
    assert math.isfinite(sigmoid(-1000))
    assert 0.0 <= sigmoid(1000) <= 1.0
    assert 0.0 <= sigmoid(-1000) <= 1.0


# 2. extrair_features with unknown segment
def test_extrair_features_segmento_desconhecido():
    """Unknown segment (not in NICHOS_PERENES) must produce x_nicho_perene=0.0."""
    p = PersonaInput(
        segment="segmento_inexistente_xyz",
        risk_profile="pragmatic",
        recent_event="none",
        has_existing_security="full_system",
        wtp_brl=500,
        bairro_p_theft=0.10,
    )
    feats = extrair_features(p)
    assert feats["x_nicho_perene"] == 0.0
    # All expected feature keys must be present
    expected_keys = {
        "x_theft", "x_renovation", "x_no_security", "x_diy_cameras",
        "x_crisis", "x_innovator", "x_budget_ok", "x_nicho_perene",
        "x_bairro_risco", "x_ticket_adequado", "x_precisa_externa",
        "x_concorrencia_local",
    }
    assert set(feats.keys()) == expected_keys


# 3. calcular_prob_agendou with all features zero
def test_calcular_prob_agendou_todas_features_zero():
    """All features zero must still return a valid probability in [0, 1]."""
    p = PersonaInput(
        segment="restaurante",  # not perene
        risk_profile="pragmatic",  # not crisis/innovator
        recent_event="none",  # not theft/renovation
        has_existing_security="full_system",  # not none/diy
        wtp_brl=100,  # < ticket_medio_36m
        bairro_p_theft=0.0,
        budget_mensal=0.0,  # < mensalidade
        mensalidade=294.0,
        ticket_medio_36m=10584.0,
    )
    feats = extrair_features(p)
    # Confirm all features are zero (except x_bairro_risco which is continuous)
    assert all(v == 0.0 for k, v in feats.items() if k != "x_bairro_risco")
    assert feats["x_bairro_risco"] == 0.0
    prob = calcular_prob_agendou(p)
    assert 0.0 <= prob <= 1.0
    assert math.isfinite(prob)
    # With bias=-3.2 and no positive drivers, prob should be low
    assert prob < 0.10


# 4. amostrar_decisao with p_agendou > 0.98
def test_amostrar_decisao_p_agendou_muito_alta():
    """When p_agendou > 0.98, probabilities must still sum to <= 1.0
    and 'ignorou' must remain reachable (1% probability)."""
    p = PersonaInput(
        segment="farmacia",
        risk_profile="crisis_driven",
        recent_event="theft",
        has_existing_security="none",
        wtp_brl=50000,
        bairro_p_theft=10.0,  # extreme value, forces p_agendou > 0.98
        budget_mensal=1000,
        mensalidade=294,
        ticket_medio_36m=10584,
    )
    prob = calcular_prob_agendou(p)
    assert prob > 0.98, f"Test setup: expected p_agendou > 0.98, got {prob}"
    rng = random.Random(42)
    decisions = [amostrar_decisao(p, rng) for _ in range(10000)]
    # ignorou has 1% probability and must be reachable
    assert "ignorou" in decisions, \
        "ignorou must be reachable even when p_agendou > 0.98"
    # All decisions must be valid outcomes
    valid = {"agendou", "clicou", "ignorou", "visualizou"}
    assert set(decisions).issubset(valid)


# 5. gerar_objecoes with empty/unknown has_existing_security
def test_gerar_objecoes_has_existing_security_vazio():
    """Empty string has_existing_security must not crash."""
    p = PersonaInput(
        segment="farmacia",
        risk_profile="pragmatic",
        recent_event="none",
        has_existing_security="",
        wtp_brl=500,
        bairro_p_theft=0.10,
        budget_mensal=500,
        mensalidade=294,
    )
    rng = random.Random(42)
    objecoes = gerar_objecoes(p, "visualizou", rng)
    assert isinstance(objecoes, list)


def test_gerar_objecoes_has_existing_security_desconhecido():
    """Unknown has_existing_security value must not crash."""
    p = PersonaInput(
        segment="farmacia",
        risk_profile="pragmatic",
        recent_event="none",
        has_existing_security="unknown_system_type",
        wtp_brl=500,
        bairro_p_theft=0.10,
        budget_mensal=500,
        mensalidade=294,
    )
    rng = random.Random(42)
    objecoes = gerar_objecoes(p, "visualizou", rng)
    assert isinstance(objecoes, list)


# 6. ic_bayesiano with n=0
def test_ic_bayesiano_n_zero():
    """ic_bayesiano with total=0 must not crash and must return valid bounds."""
    lo, hi = ic_bayesiano(0, 0)
    assert 0.0 <= lo <= hi <= 1.0
    assert math.isfinite(lo)
    assert math.isfinite(hi)


def test_ic_bayesiano_n_zero_retorna_max_incerteza():
    """With 0 trials, CI should represent maximum uncertainty: (0.0, 1.0)."""
    lo, hi = ic_bayesiano(0, 0)
    assert lo == 0.0
    assert hi == 1.0


# 7. monte_carlo with empty personas list
def test_monte_carlo_personas_vazio():
    """monte_carlo with empty personas must not crash and return 0 conversion."""
    resultado = monte_carlo([], n_seeds=10)
    assert resultado["n_personas"] == 0
    assert resultado["conversao_mediana"] == 0.0
    assert resultado["conversao_media"] == 0.0
    assert resultado["conversao_p5"] == 0.0
    assert resultado["conversao_p95"] == 0.0
    assert math.isfinite(resultado["conversao_std"])


# 8. beta_posterior with sucessos=0, falhas=0
def test_beta_posterior_zero_zero():
    """beta_posterior(0, 0) must not crash and return valid samples in [0, 1]."""
    amostras = beta_posterior(0, 0, n_amostras=1000)
    assert len(amostras) == 1000
    assert np.all(amostras >= 0.0)
    assert np.all(amostras <= 1.0)
    assert np.all(np.isfinite(amostras))


# 9. validar_modelo with missing dataset file
def test_validar_modelo_arquivo_inexistente():
    """validar_modelo with missing file must raise FileNotFoundError with clear message."""
    with pytest.raises(FileNotFoundError, match="Dataset nao encontrado"):
        validar_modelo("caminho/inexistente/dataset_fake.json")
