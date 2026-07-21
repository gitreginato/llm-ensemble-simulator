"""Testes do objections.py (phi coefficient e mapa)."""
import pytest

from simulation_army_v2.objections import phi_coefficient, analisar_objecoes


def test_phi_perfect_positive():
    """x e y identicos -> phi = 1.0."""
    x = [True, True, False, False, True, False]
    y = [True, True, False, False, True, False]
    assert phi_coefficient(x, y) == pytest.approx(1.0, abs=0.01)


def test_phi_perfect_negative():
    """x e y opostos -> phi = -1.0."""
    x = [True, True, False, False]
    y = [False, False, True, True]
    assert phi_coefficient(x, y) == pytest.approx(-1.0, abs=0.01)


def test_phi_no_correlation():
    """x e y independentes -> phi ~= 0."""
    x = [True, False, True, False, True, False, True, False]
    y = [True, True, False, False, True, True, False, False]
    assert abs(phi_coefficient(x, y)) < 0.3


def test_phi_empty():
    assert phi_coefficient([], []) == 0.0


def test_phi_all_same():
    """Todos True -> denom = 0 -> phi = 0."""
    x = [True, True, True, True]
    y = [True, True, True, True]
    assert phi_coefficient(x, y) == 0.0


def test_analisar_objecoes_estrutura():
    """analisar_objecoes retorna estrutura valida."""
    result = analisar_objecoes()
    assert "n_personas" in result
    assert "mapa_objecoes" in result
    assert "frequencia_por_modelo" in result
    assert isinstance(result["mapa_objecoes"], list)
    if result["mapa_objecoes"]:
        item = result["mapa_objecoes"][0]
        assert "categoria" in item
        assert "frequencia" in item
        assert "phi_coefficient" in item
        assert "score" in item


def test_analisar_objecoes_ordenado_por_score():
    """Mapa deve estar ordenado por score (maior primeiro)."""
    result = analisar_objecoes()
    scores = [m["score"] for m in result["mapa_objecoes"]]
    assert scores == sorted(scores, reverse=True)


def test_analisar_objecoes_top_existing_solution():
    """existing_solution deve ser a top objecao (73.3% freq, phi=0.74)."""
    result = analisar_objecoes()
    if result["mapa_objecoes"]:
        assert result["top_objecao"] == "existing_solution"
        assert result["top_objecao_score"] > 0.3
