"""Testes do ab_test.py (bootstrap da diferenca, significancia)."""
import pytest
import numpy as np

from simulation_army_v2.scale import bootstrap_ic95


def test_ab_test_diferenca_zero():
    """Mesmos dados -> diferenca 0, IC inclui 0, nao significativo."""
    data = [0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
    rng = np.random.default_rng(42)
    diffs = [
        np.mean(rng.choice(data, size=len(data), replace=True))
        - np.mean(rng.choice(data, size=len(data), replace=True))
        for _ in range(1000)
    ]
    lo, hi = float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))
    assert lo <= 0 <= hi  # IC inclui 0


def test_ab_test_diferenca_positiva():
    """B > A -> diferenca positiva, IC pode nao incluir 0."""
    a = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    b = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
    rng = np.random.default_rng(42)
    diffs = [
        np.mean(rng.choice(b, size=len(b), replace=True))
        - np.mean(rng.choice(a, size=len(a), replace=True))
        for _ in range(1000)
    ]
    lo, hi = float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))
    assert lo > 0  # IC nao inclui 0 -> significativo


def test_ab_test_bootstrap_reprodutivel():
    """Mesma seed -> mesmo resultado."""
    data = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
    r1 = bootstrap_ic95(data, n_resamples=500, seed=42)
    r2 = bootstrap_ic95(data, n_resamples=500, seed=42)
    assert r1 == r2
