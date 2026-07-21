"""Edge case tests for pitch_templates.py.

Audits 9 edge cases that could cause crashes, wrong results, or undefined behavior:
1. gerar_pitch with unknown nicho (segment not in DOR_POR_NICHO)
2. gerar_pitch with canal="" (empty string)
3. gerar_pitch with mercado="" (empty string, not in SCRIPTS_ABORDAGEM)
4. gerar_objecao_resposta with objection="" (empty string)
5. avaliar_competencias with pitch="" (empty string)
6. avaliar_competencias with objecoes=None (instead of list)
7. gerar_pitch with a persona that has None bio
8. SCRIPTS_ABORDAGEM format string missing a key (KeyError on format)
9. DOR_POR_NICHO and SEGMENT_BASELINES_V5 key sync
"""
from simulation_army_v2.pitch_templates import (
    DOR_POR_NICHO,
    OBJECAO_RESPOSTA,
    SCRIPTS_ABORDAGEM,
    avaliar_competencias,
    gerar_objecao_resposta,
    gerar_pitch,
)
from simulation_army_v2.personas_v5 import (
    SEGMENT_BASELINES_V5,
    PersonaV5,
    generate_personas_v5,
)


def _make_persona(**overrides) -> PersonaV5:
    """Create a persona with optional field overrides for testing."""
    personas = generate_personas_v5(n=1, seed=42)
    p = personas[0]
    defaults = p.__dict__.copy()
    defaults.update(overrides)
    return PersonaV5(**defaults)


# --- Edge case 1: unknown nicho ---

def test_gerar_pitch_unknown_nicho_does_not_leak_raw_segment():
    """Pitch with unknown segment should use generic term, not raw segment name."""
    p = _make_persona(segment="unknown_nicho")
    pitch = gerar_pitch(p)
    assert "unknown nicho" not in pitch.lower()
    assert "unknown_nicho" not in pitch
    assert len(pitch) > 50


# --- Edge case 2: canal="" ---

def test_gerar_pitch_empty_canal_does_not_crash():
    """Empty canal should produce a valid pitch (defaults to phone_call)."""
    p = _make_persona()
    pitch = gerar_pitch(p, canal="")
    assert len(pitch) > 50
    assert "15 a 20 minutos" in pitch


# --- Edge case 3: mercado="" ---

def test_gerar_pitch_empty_mercado_does_not_crash():
    """Empty mercado should use default script without crashing."""
    p = _make_persona()
    pitch = gerar_pitch(p, mercado="")
    assert len(pitch) > 50
    assert "15 a 20 minutos" in pitch


# --- Edge case 4: objection="" ---

def test_gerar_objecao_resposta_empty_string_no_double_article():
    """Empty objection should return a valid default response without double article.

    The skepticism template has 'O {recomendante}' and the default recomendante
    was 'o recomendante', producing 'O o recomendante' (wrong).
    """
    resposta = gerar_objecao_resposta("")
    assert len(resposta) > 10
    assert "{" not in resposta
    assert "O o " not in resposta


# --- Edge case 5: pitch="" ---

def test_avaliar_competencias_empty_pitch_does_not_crash():
    """Empty pitch should return low scores without crashing."""
    scores = avaliar_competencias("", "ignorou", [])
    assert all(0 <= v <= 10 for v in scores.values())
    assert scores["foco_agendamento"] <= 5
    assert scores["geracao_curiosidade"] <= 5


# --- Edge case 6: objecoes=None ---

def test_avaliar_competencias_objecoes_none_does_not_crash():
    """None objecoes should be treated as no objections without crashing."""
    scores = avaliar_competencias("some pitch text", "ignorou", None)
    assert "contorno_objecoes" in scores
    assert all(0 <= v <= 10 for v in scores.values())


# --- Edge case 7: None bio ---

def test_gerar_pitch_none_bio_does_not_crash():
    """None bio should not crash gerar_pitch (bio is not used in pitch generation)."""
    p = _make_persona(bio=None)
    pitch = gerar_pitch(p)
    assert len(pitch) > 50


# --- Edge case 8: format string missing key ---

def test_gerar_pitch_script_with_missing_placeholder_does_not_crash(monkeypatch):
    """Script with unsupported placeholder should not crash (SafeDict prevents KeyError)."""
    monkeypatch.setitem(
        SCRIPTS_ABORDAGEM,
        "test_mercado",
        "Hello {nome}, {unsupported_key} here",
    )
    p = _make_persona()
    pitch = gerar_pitch(p, mercado="test_mercado")
    assert "Hello" in pitch
    # Missing placeholder should be replaced with empty string, not left as-is
    assert "{unsupported_key}" not in pitch


# --- Edge case 9: DOR_POR_NICHO and SEGMENT_BASELINES_V5 in sync ---

def test_dor_por_nicho_and_segment_baselines_in_sync():
    """DOR_POR_NICHO and SEGMENT_BASELINES_V5 must have identical key sets."""
    dor_keys = set(DOR_POR_NICHO.keys())
    seg_keys = set(SEGMENT_BASELINES_V5.keys())
    assert dor_keys == seg_keys
    assert len(dor_keys) == 26
