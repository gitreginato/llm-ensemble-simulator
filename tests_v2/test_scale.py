"""Testes do scale.py (bootstrap e power analysis)."""
import pytest

from simulation_army_v2.scale import (
    agregar_seeds,
    bootstrap_ic95,
    power_analysis,
)


def test_bootstrap_ic95_basico():
    data = [0, 0, 0, 1, 0, 1, 0, 0, 0, 0]
    r = bootstrap_ic95(data, n_resamples=1000, seed=42)
    assert r["n"] == 10
    assert 0.0 <= r["media"] <= 1.0
    assert r["ic_lo"] <= r["media"] <= r["ic_hi"]
    assert r["n_resamples"] == 1000


def test_bootstrap_ic95_vazio():
    r = bootstrap_ic95([])
    assert r["media"] == 0.0
    assert r["n"] == 0


def test_bootstrap_ic95_todos_zeros():
    r = bootstrap_ic95([0, 0, 0, 0, 0], n_resamples=100, seed=42)
    assert r["media"] == 0.0
    assert r["ic_lo"] == 0.0
    assert r["ic_hi"] == 0.0


def test_bootstrap_ic95_todos_uns():
    r = bootstrap_ic95([1, 1, 1, 1, 1], n_resamples=100, seed=42)
    assert r["media"] == 1.0
    assert r["ic_lo"] == 1.0
    assert r["ic_hi"] == 1.0


def test_bootstrap_ic95_reprodutivel():
    data = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
    r1 = bootstrap_ic95(data, n_resamples=500, seed=42)
    r2 = bootstrap_ic95(data, n_resamples=500, seed=42)
    assert r1 == r2  # mesma seed = mesmo resultado


def test_power_analysis_diferenca_grande():
    """Diff 26.7pp com N=30 -> poder moderado, N necessario baixo."""
    r = power_analysis(0.167, 0.433, 30)
    assert r["poder"] > 0.5
    assert r["n_necessario_80pct"] < 20
    assert r["diff_observada"] == pytest.approx(0.266, abs=0.01)


def test_power_analysis_diferenca_pequena():
    """Diff 3.3pp com N=30 -> poder muito baixo, N necessario alto."""
    r = power_analysis(0.167, 0.200, 30)
    assert r["poder"] < 0.1
    assert r["n_necessario_80pct"] > 100


def test_power_analysis_sem_diferenca():
    r = power_analysis(0.5, 0.5, 30)
    assert r["poder"] == 0.0
    assert r["diff"] == 0.0


def test_agregar_seeds_vazio():
    r = agregar_seeds([])
    assert r["n_total"] == 0
    assert r["personas"] == []


def test_agregar_seeds_arquivo_inexistente():
    r = agregar_seeds(["/tmp/nao_existe.json"])
    assert r["n_total"] == 0
