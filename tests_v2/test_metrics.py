"""Testes do metrics.py (entropia, KL, pairwise, permutacao)."""
import pytest

from simulation_army_v2.metrics import (
    _distribuicao,
    entropia_shannon,
    kl_divergence,
    pairwise_disagreement_rate,
)
from simulation_army_v2.metrics import teste_permutacao as permutacao_test


def test_distribuicao_uniforme():
    p = _distribuicao(["visualizou", "clicou", "agendou", "ignorou"])
    assert all(abs(x - 0.25) < 1e-10 for x in p)


def test_distribuicao_concentrada():
    p = _distribuicao(["agendou", "agendou", "agendou", "agendou"])
    assert p[2] == 1.0  # agendou
    assert all(p[i] == 0.0 for i in range(4) if i != 2)


def test_distribuicao_vazia():
    p = _distribuicao([])
    assert all(abs(x - 0.25) < 1e-10 for x in p)


def test_entropia_maxima():
    h = entropia_shannon(["visualizou", "clicou", "agendou", "ignorou"])
    assert abs(h - 2.0) < 1e-10  # log2(4) = 2.0


def test_entropia_zero():
    h = entropia_shannon(["agendou", "agendou", "agendou"])
    assert h == 0.0


def test_entropia_parcial():
    h = entropia_shannon(["agendou", "agendou", "visualizou", "visualizou"])
    assert abs(h - 1.0) < 1e-10  # 2 categorias iguais = 1 bit


def test_kl_divergence_zero():
    p = [0.25, 0.25, 0.25, 0.25]
    kl = kl_divergence(p, p)
    assert kl < 0.001  # ~0


def test_kl_divergence_positiva():
    p = [0.5, 0.3, 0.1, 0.1]
    q = [0.1, 0.1, 0.3, 0.5]
    kl = kl_divergence(p, q)
    assert kl > 0.1


def test_kl_divergence_nao_simetrica():
    """KL nao e simetrica: KL(P||Q) != KL(Q||P) em geral."""
    p = [0.7, 0.1, 0.1, 0.1]
    q = [0.25, 0.25, 0.25, 0.25]
    kl_pq = kl_divergence(p, q)
    kl_qp = kl_divergence(q, p)
    assert abs(kl_pq - kl_qp) > 0.01


def test_pairwise_disagreement_all_concordam():
    c = [
        {"modelo_a": "a", "modelo_b": "b", "concordam": True},
        {"modelo_a": "a", "modelo_b": "c", "concordam": True},
        {"modelo_a": "b", "modelo_b": "c", "concordam": True},
    ]
    assert pairwise_disagreement_rate(c) == 0.0


def test_pairwise_disagreement_all_discordam():
    c = [
        {"modelo_a": "a", "modelo_b": "b", "concordam": False},
        {"modelo_a": "a", "modelo_b": "c", "concordam": False},
        {"modelo_a": "b", "modelo_b": "c", "concordam": False},
    ]
    assert pairwise_disagreement_rate(c) == 1.0


def test_pairwise_disagreement_parcial():
    c = [
        {"modelo_a": "a", "modelo_b": "b", "concordam": False},
        {"modelo_a": "a", "modelo_b": "c", "concordam": True},
        {"modelo_a": "b", "modelo_b": "c", "concordam": False},
    ]
    assert abs(pairwise_disagreement_rate(c) - 2 / 3) < 1e-10


def test_pairwise_disagreement_vazio():
    assert pairwise_disagreement_rate([]) == 0.0


def test_permutacao_diferenca_significativa():
    """Ensemble com divergence alto vs baseline 0 -> p < 0.05."""
    ens = [0.5, 0.6, 0.7, 0.8, 0.4, 0.5, 0.6, 0.7, 0.8, 0.4]
    base = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    p = permutacao_test(ens, base, n_permutacoes=500, seed=42)
    assert p < 0.05


def test_permutacao_sem_diferenca():
    """Mesma distribuicao -> p alto."""
    ens = [0.5, 0.6, 0.4, 0.5, 0.6, 0.4, 0.5, 0.6, 0.4, 0.5]
    base = [0.5, 0.6, 0.4, 0.5, 0.6, 0.4, 0.5, 0.6, 0.4, 0.5]
    p = permutacao_test(ens, base, n_permutacoes=500, seed=42)
    assert p > 0.3  # alta probabilidade de nao rejeitar H0
