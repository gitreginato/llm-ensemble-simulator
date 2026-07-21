"""Testes para scripts.dashboard_observability."""
import json
from pathlib import Path

import pytest

from scripts.dashboard_observability import aggregate_metrics, load_results, generate_html


@pytest.fixture
def sample_results(tmp_path):
    """Cria 1 result JSON de exemplo no tmp_path."""
    data = {
        "cenario": "TEST",
        "n": 2,
        "seed": 42,
        "modelos": ["model-a", "model-b"],
        "sintetizador": "synth",
        "taxa_conversao": 0.5,
        "agendaram": 1,
        "sucessos": 2,
        "falhas": 1,
        "ic95": [0.01, 0.99],
        "divergence_score_medio": 0.5,
        "custo_total_usd": 0.001,
        "custo_por_modelo": {"model-a": 0.001},
        "personas": [
            {
                "persona": {"owner_name": "Test"},
                "decisoes_modelos": [],
                "metadados_modelos": [
                    {"modelo": "model-a", "source": "gocat", "latency_ms": 100, "total_tokens": 50, "cost_usd": 0.001},
                    {"modelo": "model-b", "source": "kilocode", "erro": "timeout"},
                ],
                "decisao_agregada": {"decisao_final": "agendou", "divergence_score": 0.5},
            }
        ],
    }
    (tmp_path / "test_run.json").write_text(json.dumps(data), encoding="utf-8")
    return tmp_path


def test_load_results(sample_results):
    results = load_results(str(sample_results))
    assert len(results) == 1
    assert results[0]["cenario"] == "TEST"


def test_load_results_empty(tmp_path):
    results = load_results(str(tmp_path))
    assert results == []


def test_aggregate_metrics(sample_results):
    results = load_results(str(sample_results))
    metrics = aggregate_metrics(results)
    by_model = metrics["by_model"]
    assert "model-a" in by_model
    assert by_model["model-a"]["total"] == 1
    assert by_model["model-a"]["ok"] == 1
    assert by_model["model-a"]["fail"] == 0
    assert by_model["model-a"]["latencies"] == [100]
    assert by_model["model-a"]["tokens"] == [50]
    assert "model-b" in by_model
    assert by_model["model-b"]["fail"] == 1
    by_source = metrics["by_source"]
    assert by_source["gocat"]["ok"] == 1
    assert by_source["kilocode"]["fail"] == 1


def test_generate_html(sample_results, tmp_path):
    results = load_results(str(sample_results))
    metrics = aggregate_metrics(results)
    output = str(tmp_path / "dashboard.html")
    generate_html(results, metrics, output)
    html = Path(output).read_text(encoding="utf-8")
    assert "Dashboard" in html
    assert "model-a" in html
    assert "model-b" in html
    assert "gocat" in html
    assert "kilocode" in html
    assert "<svg" in html
    assert "</svg>" in html
    assert "<table" in html
