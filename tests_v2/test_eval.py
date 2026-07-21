"""Testes do eval.py (3 checks: calibracao, diversidade, coerencia)."""
import pytest

from simulation_army_v2.eval import (
    check_calibracao,
    check_coerencia,
    check_diversidade,
    run_eval,
)


def test_check_calibracao_dentro_range():
    data = {"taxa_conversao": 0.05}
    r = check_calibracao(data)
    assert r["pass"] is True
    assert r["score"] == 1.0


def test_check_calibracao_abaixo_range():
    data = {"taxa_conversao": 0.01}
    r = check_calibracao(data)
    assert r["pass"] is False
    assert 0 < r["score"] < 1.0


def test_check_calibracao_acima_range():
    data = {"taxa_conversao": 0.15}
    r = check_calibracao(data)
    assert r["pass"] is False
    assert 0 < r["score"] < 1.0


def test_check_calibracao_sem_data():
    r = check_calibracao(None)
    assert r["pass"] is False
    assert r["score"] == 0.0


def test_check_diversidade_pass():
    data = {"pairwise_disagreement_rate": 0.62, "teste_permutacao_p_valor": 0.0}
    r = check_diversidade(data)
    assert r["pass"] is True
    assert r["score"] == 1.0


def test_check_diversidade_pdr_baixo():
    data = {"pairwise_disagreement_rate": 0.1, "teste_permutacao_p_valor": 0.0}
    r = check_diversidade(data)
    assert r["pass"] is False
    assert r["score"] == 0.5  # p ok, pdr fail


def test_check_diversidade_p_alto():
    data = {"pairwise_disagreement_rate": 0.62, "teste_permutacao_p_valor": 0.3}
    r = check_diversidade(data)
    assert r["pass"] is False
    assert r["score"] == 0.5  # pdr ok, p fail


def test_check_diversidade_sem_data():
    r = check_diversidade(None)
    assert r["pass"] is False
    assert r["score"] == 0.0


def test_check_coerencia_pass():
    data = {
        "personas": [
            {"decisao_agregada": {"confianca_agregada": 0.8, "raciocinio_sintese": "ok"}},
            {"decisao_agregada": {"confianca_agregada": 0.7, "raciocinio_sintese": "ok"}},
            {"decisao_agregada": {"confianca_agregada": 0.9, "raciocinio_sintese": "ok"}},
        ]
    }
    r = check_coerencia(data)
    assert r["pass"] is True
    assert r["score"] == 1.0


def test_check_coerencia_fail_confianca_baixa():
    data = {
        "personas": [
            {"decisao_agregada": {"confianca_agregada": 0.3, "raciocinio_sintese": "ok"}},
            {"decisao_agregada": {"confianca_agregada": 0.8, "raciocinio_sintese": "ok"}},
        ]
    }
    r = check_coerencia(data)
    assert r["pass"] is False
    assert r["score"] < 1.0


def test_check_coerencia_fail_raciocinio_vazio():
    data = {
        "personas": [
            {"decisao_agregada": {"confianca_agregada": 0.8, "raciocinio_sintese": ""}},
            {"decisao_agregada": {"confianca_agregada": 0.8, "raciocinio_sintese": "ok"}},
        ]
    }
    r = check_coerencia(data)
    assert r["pass"] is False


def test_check_coerencia_sem_agregadas():
    data = {"personas": [{"decisao_agregada": None}, {"decisao_agregada": None}]}
    r = check_coerencia(data)
    assert r["pass"] is False
    assert r["score"] == 0.0


def test_run_eval_estrutura():
    """run_eval retorna score, passed, threshold, checks."""
    r = run_eval()
    assert "score" in r
    assert "passed" in r
    assert "threshold" in r
    assert "checks" in r
    assert "calibracao" in r["checks"]
    assert "diversidade" in r["checks"]
    assert "coerencia" in r["checks"]
    assert 0.0 <= r["score"] <= 1.0
