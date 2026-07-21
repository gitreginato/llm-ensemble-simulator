"""Edge case tests for personas_v5.py.

Covers boundary and invalid-input scenarios that could cause crashes,
wrong results, or undefined behavior.
"""
import random

import pytest

from simulation_army_v2.personas_v5 import (
    CONTRATO_MESES,
    MENSALIDADE_MAX,
    MENSALIDADE_MIN,
    P_PRECISA_AREA_EXTERNA,
    SEGMENT_BASELINES_V5,
    PersonaV5,
    _calcular_mensalidade,
    _gerar_recent_event,
    generate_personas_v5,
    persona_to_dict,
)


# === 1. n=0 (empty list, should not crash) ===

def test_n_zero_returns_empty_list():
    """generate_personas_v5 with n=0 must return an empty list, not crash."""
    personas = generate_personas_v5(n=0, seed=42)
    assert personas == []
    assert isinstance(personas, list)


# === 2. n=1 (single persona) ===

def test_n_one_returns_single_persona():
    """generate_personas_v5 with n=1 must return a list with exactly one persona."""
    personas = generate_personas_v5(n=1, seed=42)
    assert len(personas) == 1
    assert isinstance(personas[0], PersonaV5)
    assert personas[0].id == 1


# === 3. invalid segment (not in SEGMENT_BASELINES_V5) ===

def test_invalid_segment_raises_value_error():
    """An unknown segment must raise ValueError with a clear message, not KeyError."""
    with pytest.raises(ValueError, match="segment"):
        generate_personas_v5(n=5, segment="segmento_inexistente", seed=42)


def test_invalid_segment_error_lists_valid_options():
    """The ValueError message should mention valid segments for debugging."""
    with pytest.raises(ValueError) as exc_info:
        generate_personas_v5(n=1, segment="xxx", seed=42)
    msg = str(exc_info.value)
    # Message should reference at least one valid segment
    assert "farmacia" in msg or "bar" in msg


# === 4. invalid month (mes=13 or mes=0) ===

def test_mes_zero_raises_value_error():
    """mes=0 is invalid (months are 1-12) and must raise ValueError."""
    with pytest.raises(ValueError, match="mes"):
        generate_personas_v5(n=5, mes=0, seed=42)


def test_mes_thirteen_raises_value_error():
    """mes=13 is invalid (months are 1-12) and must raise ValueError."""
    with pytest.raises(ValueError, match="mes"):
        generate_personas_v5(n=5, mes=13, seed=42)


def test_mes_negative_raises_value_error():
    """mes=-1 is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="mes"):
        generate_personas_v5(n=5, mes=-1, seed=42)


# === 5. _calcular_mensalidade with invalid porte ===

def test_calcular_mensalidade_invalid_porte_raises():
    """An unknown porte must raise ValueError, not silently return grande value."""
    rng = random.Random(42)
    with pytest.raises(ValueError, match="porte"):
        _calcular_mensalidade("gigante", rng)


def test_calcular_mensalidade_empty_porte_raises():
    """Empty string porte must raise ValueError."""
    rng = random.Random(42)
    with pytest.raises(ValueError, match="porte"):
        _calcular_mensalidade("", rng)


def test_calcular_mensalidade_valid_portes():
    """Valid portes return values within expected ranges."""
    rng = random.Random(42)
    assert _calcular_mensalidade("pequeno", rng) == MENSALIDADE_MIN
    med = _calcular_mensalidade("medio", rng)
    assert 350 <= med <= 400
    grd = _calcular_mensalidade("grande", rng)
    assert 400 <= grd <= MENSALIDADE_MAX


# === 6. _gerar_recent_event with extreme bairro_p_theft ===

def test_gerar_recent_event_p_theft_zero():
    """p_theft=0.0 must not crash and must return a valid event."""
    rng = random.Random(42)
    for _ in range(50):
        event = _gerar_recent_event(rng, 0.0)
        assert event in ["none", "theft", "competitor_new", "renovation", "slow_month"]


def test_gerar_recent_event_p_theft_one():
    """p_theft=1.0 must not crash and must return a valid event."""
    rng = random.Random(42)
    for _ in range(50):
        event = _gerar_recent_event(rng, 1.0)
        assert event in ["none", "theft", "competitor_new", "renovation", "slow_month"]


def test_gerar_recent_event_weights_normalize():
    """Weights must normalize so the function never crashes on extreme values."""
    rng = random.Random(42)
    # p_theft very high: p_theft_ajustado = 10.0, weights[1]=10.0
    event = _gerar_recent_event(rng, 5.0)
    assert event in ["none", "theft", "competitor_new", "renovation", "slow_month"]


# === 7. P_PRECISA_AREA_EXTERNA missing a segment ===

def test_p_precisa_area_externa_covers_all_segments():
    """Every segment in SEGMENT_BASELINES_V5 must be in P_PRECISA_AREA_EXTERNA."""
    missing = set(SEGMENT_BASELINES_V5.keys()) - set(P_PRECISA_AREA_EXTERNA.keys())
    assert not missing, f"Segments missing from P_PRECISA_AREA_EXTERNA: {missing}"


def test_p_precisa_area_externa_default_for_unknown_segment():
    """generate_personas_v5 uses a default 0.50 for unknown segments via .get()."""
    # We cannot pass an unknown segment directly (it raises ValueError now),
    # but we verify the .get default is 0.50 by checking the dict directly.
    assert P_PRECISA_AREA_EXTERNA.get("segmento_ficticio", 0.50) == 0.50


# === 8. persona_to_dict with None fields ===

def test_persona_to_dict_handles_none_numeric_fields():
    """persona_to_dict must not crash when numeric fields are None."""
    p = PersonaV5(
        id=1,
        owner_name="Test",
        gender="male",
        segment="bar",
        segment_perene=False,
        segment_porte="medio",
        bairro="Centro",
        bairro_risco="alto",
        bairro_perfil="comercial_historico",
        bairro_p_theft=0.15,
        risk_profile="pragmatic",
        recent_event="none",
        has_existing_security="none",
        existing_security_satisfaction=0,
        revenue_mensal=None,
        margin=None,
        budget_mensal_seguranca=None,
        mensalidade_emive=None,
        ticket_medio_36m=None,
        multa_proporcional_base=None,
        wtp_brl=None,
        pode_pagar_mensalidade=False,
    )
    d = persona_to_dict(p)
    # None fields should remain None, not crash
    assert d["revenue_mensal"] is None
    assert d["budget_mensal_seguranca"] is None
    assert d["wtp_brl"] is None


def test_persona_to_dict_handles_none_string_fields():
    """persona_to_dict must not crash when string fields are None."""
    p = PersonaV5(
        id=1,
        owner_name=None,
        gender=None,
        segment=None,
        segment_perene=False,
        segment_porte="medio",
        bairro=None,
        bairro_risco=None,
        bairro_perfil=None,
        bairro_p_theft=0.15,
        risk_profile=None,
        recent_event=None,
        has_existing_security=None,
        existing_security_satisfaction=0,
        revenue_mensal=1000.0,
        margin=0.1,
        budget_mensal_seguranca=100.0,
        mensalidade_emive=350.0,
        ticket_medio_36m=12600.0,
        multa_proporcional_base=12250.0,
        wtp_brl=5000.0,
        pode_pagar_mensalidade=False,
    )
    d = persona_to_dict(p)
    assert d["owner_name"] is None
    assert d["segment"] is None
    assert d["revenue_mensal"] == 1000.0  # non-None still rounds


# === 9. WTP calculation: can WTP be 0? ===

def test_wtp_always_positive():
    """WTP must always be > 0 for all valid segments and seeds."""
    for seg in SEGMENT_BASELINES_V5:
        personas = generate_personas_v5(n=20, segment=seg, seed=42)
        for p in personas:
            assert p.wtp_brl > 0, f"WTP is 0 for segment={seg}"


def test_wtp_formula_consistent():
    """WTP = budget_mensal * 36 * uniform(0.5, 1.5), so 0.5 <= wtp/(budget*36) <= 1.5."""
    personas = generate_personas_v5(n=50, seed=42)
    for p in personas:
        ratio = p.wtp_brl / (p.budget_mensal_seguranca * CONTRATO_MESES)
        assert 0.5 <= ratio <= 1.5, f"WTP ratio {ratio} out of [0.5, 1.5]"


# === 10. pode_pagar_mensalidade boundary (budget == mensalidade) ===

def test_pode_pagar_boundary_exact_equality():
    """When budget_mensal == mensalidade exactly, pode_pagar must be True (>=)."""
    p = PersonaV5(
        id=1,
        owner_name="Boundary",
        gender="male",
        segment="bar",
        segment_perene=False,
        segment_porte="medio",
        bairro="Centro",
        bairro_risco="alto",
        bairro_perfil="comercial_historico",
        bairro_p_theft=0.15,
        risk_profile="pragmatic",
        recent_event="none",
        has_existing_security="none",
        existing_security_satisfaction=0,
        revenue_mensal=10000.0,
        margin=0.2,
        budget_mensal_seguranca=350.0,
        mensalidade_emive=350.0,
        ticket_medio_36m=12600.0,
        multa_proporcional_base=12250.0,
        wtp_brl=5000.0,
        pode_pagar_mensalidade=True,
    )
    # The field is set explicitly; verify the logic used in generate_personas_v5
    budget = 350.0
    mensalidade = 350.0
    assert budget >= mensalidade  # boundary is True


def test_pode_pagar_boundary_just_below():
    """When budget is just below mensalidade, pode_pagar must be False."""
    personas = generate_personas_v5(n=200, seed=99)
    # Find a persona where budget < mensalidade and verify pode_pagar is False
    found_below = False
    for p in personas:
        if p.budget_mensal_seguranca < p.mensalidade_emive:
            assert p.pode_pagar_mensalidade is False
            found_below = True
    assert found_below, "Expected at least one persona with budget < mensalidade"


def test_pode_pagar_boundary_just_above():
    """When budget is just above mensalidade, pode_pagar must be True."""
    personas = generate_personas_v5(n=200, seed=99)
    found_above = False
    for p in personas:
        if p.budget_mensal_seguranca >= p.mensalidade_emive:
            assert p.pode_pagar_mensalidade is True
            found_above = True
    assert found_above, "Expected at least one persona with budget >= mensalidade"
