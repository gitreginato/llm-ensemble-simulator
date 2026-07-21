"""Testes do ensemble.py (helpers e metricas)."""
import pytest

from simulation_army_v2.ensemble import _compute_concordancia, _format_respostas, _ic95
from simulation_army_v2.schema import DecisaoPersona


def _make_decisao(modelo, decisao):
    return DecisaoPersona(
        modelo=modelo, decisao=decisao, wtp=500.0, sentimento=0.5,
        objecoes=[], confianca=0.8, raciocinio="ok",
    )


def test_compute_concordancia_3_modelos_unanimes():
    d = [
        _make_decisao("a", "agendou"),
        _make_decisao("b", "agendou"),
        _make_decisao("c", "agendou"),
    ]
    pairs = _compute_concordancia(d)
    assert len(pairs) == 3
    assert all(p.concordam for p in pairs)


def test_compute_concordancia_3_modelos_split():
    d = [
        _make_decisao("a", "agendou"),
        _make_decisao("b", "visualizou"),
        _make_decisao("c", "agendou"),
    ]
    pairs = _compute_concordancia(d)
    assert len(pairs) == 3
    assert pairs[0].concordam is False  # a vs b
    assert pairs[1].concordam is True   # a vs c
    assert pairs[2].concordam is False  # b vs c


def test_compute_concordancia_2_modelos():
    d = [_make_decisao("a", "agendou"), _make_decisao("b", "visualizou")]
    pairs = _compute_concordancia(d)
    assert len(pairs) == 1
    assert pairs[0].concordam is False


def test_ic95_n_zero():
    lo, hi = _ic95(0.0, 0)
    assert lo == 0.0 and hi == 1.0


def test_ic95_n_30_conversao_0():
    lo, hi = _ic95(0.0, 30)
    assert 0.0 <= lo <= 0.1
    assert hi <= 0.2


def test_ic95_n_30_conversao_50():
    lo, hi = _ic95(0.5, 30)
    assert 0.2 < lo < 0.5
    assert 0.5 < hi < 0.8


def test_ic95_n_30_conversao_100():
    lo, hi = _ic95(1.0, 30)
    assert lo > 0.8
    assert hi > 0.99


def test_ic95_nao_retorna_nan():
    """Bug fix: beta.ppf pode retornar NaN. Garantir que nao acontece."""
    import math
    for conv in [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]:
        for n in [1, 3, 9, 10, 30, 100]:
            lo, hi = _ic95(conv, n)
            assert not math.isnan(lo), f"lo is NaN for conv={conv} n={n}"
            assert not math.isnan(hi), f"hi is NaN for conv={conv} n={n}"
            assert 0.0 <= lo <= hi <= 1.0


def test_format_respostas_3_decisoes():
    d = [
        _make_decisao("gpt-4o-mini", "agendou"),
        _make_decisao("command-r", "visualizou"),
        _make_decisao("llama", "agendou"),
    ]
    out = _format_respostas(d)
    assert "gpt-4o-mini" in out
    assert "command-r" in out
    assert "llama" in out
    assert "agendou" in out
    assert "visualizou" in out


def test_format_respostas_empty():
    out = _format_respostas([])
    assert out == ""
