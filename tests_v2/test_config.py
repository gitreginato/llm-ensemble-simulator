"""Testes do config YAML do Simulation Army v2."""
import pytest
from pydantic import ValidationError

from simulation_army_v2.config import ArmyConfig, load_config

CONFIG_PATH = "scenarios_v2/slz-c-army.yaml"


def test_config_carrega():
    c = load_config(CONFIG_PATH)
    assert isinstance(c, ArmyConfig)
    assert c.scenario.code == "SLZ-C-ARMY"


def test_config_ensemble_3_modelos():
    c = load_config(CONFIG_PATH)
    assert len(c.ensemble.models) == 3
    modelos = [m.model for m in c.ensemble.models]
    assert "gpt-4o-mini" in modelos
    assert "command-r-plus-08-2024" in modelos
    assert "llama-3.3-70b-versatile" in modelos


def test_config_papeis_distintos():
    c = load_config(CONFIG_PATH)
    papeis = [m.role for m in c.ensemble.models]
    assert len(set(papeis)) == 3, "papeis devem ser distintos"


def test_config_providers_distintos():
    c = load_config(CONFIG_PATH)
    providers = [m.provider for m in c.ensemble.models]
    assert len(set(providers)) == 3, "providers devem ser distintos (heterogeneidade)"


def test_config_sintetizador_definido():
    c = load_config(CONFIG_PATH)
    assert c.synthesizer.model == "gpt-4o-mini"


def test_config_benchmark_ranges_validos():
    c = load_config(CONFIG_PATH)
    assert 0 < c.benchmark.conversao_geral_min < c.benchmark.conversao_geral_max < 1
    assert 0 < c.benchmark.agendamento_min < c.benchmark.agendamento_max < 1
    assert 0 < c.benchmark.whatsapp_reply_min < c.benchmark.whatsapp_reply_max < 1


def test_config_benchmark_conversao_2_a_8_pct():
    c = load_config(CONFIG_PATH)
    assert c.benchmark.conversao_geral_min == 0.02
    assert c.benchmark.conversao_geral_max == 0.08


def test_config_benchmark_fontes_declaradas():
    c = load_config(CONFIG_PATH)
    assert len(c.benchmark.fontes) >= 3, "fontes devem ser declaradas para evidencia"


def test_config_gocat_default():
    c = load_config(CONFIG_PATH)
    assert c.gocat.base_url == "http://127.0.0.1:8080"
    assert c.gocat.timeout_seconds > 0


def test_config_execution_seeds():
    c = load_config(CONFIG_PATH)
    assert len(c.execution.seeds) >= 1
    assert all(isinstance(s, int) for s in c.execution.seeds)


def test_config_scenario_num_agents():
    c = load_config(CONFIG_PATH)
    assert c.scenario.num_agents == 30


def test_config_rejeita_benchmark_min_maior_que_max():
    with pytest.raises(ValidationError):
        ArmyConfig(
            scenario={
                "code": "X", "name": "X", "project": "X", "product_name": "X",
                "description": "X", "price_brl": 1, "price_model": "visit",
                "target_segment": "X", "channel": "X", "value_proposition": "X",
                "pain_focus": "X", "num_agents": 30,
            },
            ensemble={"models": [
                {"model": "a", "provider": "p1", "role": "r1"},
                {"model": "b", "provider": "p2", "role": "r2"},
                {"model": "c", "provider": "p3", "role": "r3"},
            ]},
            synthesizer={"model": "s", "provider": "p1"},
            benchmark={
                "conversao_geral_min": 0.08, "conversao_geral_max": 0.02,
                "agendamento_min": 0.01, "agendamento_max": 0.08,
                "whatsapp_reply_min": 0.10, "whatsapp_reply_max": 0.20,
            },
            gocat={},
            execution={},
        )


def test_config_rejeita_benchmark_min_igual_max():
    with pytest.raises(ValidationError, match=">="):
        ArmyConfig(
            scenario={
                "code": "X", "name": "X", "project": "X", "product_name": "X",
                "description": "X", "price_brl": 1, "price_model": "visit",
                "target_segment": "X", "channel": "X", "value_proposition": "X",
                "pain_focus": "X", "num_agents": 30,
            },
            ensemble={"models": [
                {"model": "a", "provider": "p1", "role": "r1"},
                {"model": "b", "provider": "p2", "role": "r2"},
                {"model": "c", "provider": "p3", "role": "r3"},
            ]},
            synthesizer={"model": "s", "provider": "p1"},
            benchmark={
                "conversao_geral_min": 0.05, "conversao_geral_max": 0.05,
                "agendamento_min": 0.01, "agendamento_max": 0.08,
                "whatsapp_reply_min": 0.10, "whatsapp_reply_max": 0.20,
            },
            gocat={},
            execution={},
        )


def test_config_rejeita_ensemble_vazio():
    with pytest.raises(ValidationError):
        ArmyConfig(
            scenario={
                "code": "X", "name": "X", "project": "X", "product_name": "X",
                "description": "X", "price_brl": 1, "price_model": "visit",
                "target_segment": "X", "channel": "X", "value_proposition": "X",
                "pain_focus": "X", "num_agents": 30,
            },
            ensemble={"models": []},
            synthesizer={"model": "s", "provider": "p1"},
            benchmark={
                "conversao_geral_min": 0.02, "conversao_geral_max": 0.08,
                "agendamento_min": 0.01, "agendamento_max": 0.08,
                "whatsapp_reply_min": 0.10, "whatsapp_reply_max": 0.20,
            },
            gocat={},
            execution={},
        )


def test_config_rejeita_modelo_duplicado():
    with pytest.raises(ValidationError, match="duplicado"):
        ArmyConfig(
            scenario={
                "code": "X", "name": "X", "project": "X", "product_name": "X",
                "description": "X", "price_brl": 1, "price_model": "visit",
                "target_segment": "X", "channel": "X", "value_proposition": "X",
                "pain_focus": "X", "num_agents": 30,
            },
            ensemble={"models": [
                {"model": "a", "provider": "p1", "role": "r1"},
                {"model": "a", "provider": "p1", "role": "r2"},
            ]},
            synthesizer={"model": "s", "provider": "p1"},
            benchmark={
                "conversao_geral_min": 0.02, "conversao_geral_max": 0.08,
                "agendamento_min": 0.01, "agendamento_max": 0.08,
                "whatsapp_reply_min": 0.10, "whatsapp_reply_max": 0.20,
            },
            gocat={},
            execution={},
        )


def test_config_rejeita_price_brl_negativo():
    with pytest.raises(ValidationError):
        ArmyConfig(
            scenario={
                "code": "X", "name": "X", "project": "X", "product_name": "X",
                "description": "X", "price_brl": -1, "price_model": "visit",
                "target_segment": "X", "channel": "X", "value_proposition": "X",
                "pain_focus": "X", "num_agents": 30,
            },
            ensemble={"models": [{"model": "a", "provider": "p1", "role": "r1"}]},
            synthesizer={"model": "s", "provider": "p1"},
            benchmark={
                "conversao_geral_min": 0.02, "conversao_geral_max": 0.08,
                "agendamento_min": 0.01, "agendamento_max": 0.08,
                "whatsapp_reply_min": 0.10, "whatsapp_reply_max": 0.20,
            },
            gocat={},
            execution={},
        )


def test_config_rejeita_timeout_negativo():
    with pytest.raises(ValidationError):
        ArmyConfig(
            scenario={
                "code": "X", "name": "X", "project": "X", "product_name": "X",
                "description": "X", "price_brl": 1, "price_model": "visit",
                "target_segment": "X", "channel": "X", "value_proposition": "X",
                "pain_focus": "X", "num_agents": 30,
            },
            ensemble={"models": [{"model": "a", "provider": "p1", "role": "r1"}]},
            synthesizer={"model": "s", "provider": "p1"},
            benchmark={
                "conversao_geral_min": 0.02, "conversao_geral_max": 0.08,
                "agendamento_min": 0.01, "agendamento_max": 0.08,
                "whatsapp_reply_min": 0.10, "whatsapp_reply_max": 0.20,
            },
            gocat={"timeout_seconds": -5},
            execution={},
        )


def test_config_rejeita_seeds_vazio():
    with pytest.raises(ValidationError):
        ArmyConfig(
            scenario={
                "code": "X", "name": "X", "project": "X", "product_name": "X",
                "description": "X", "price_brl": 1, "price_model": "visit",
                "target_segment": "X", "channel": "X", "value_proposition": "X",
                "pain_focus": "X", "num_agents": 30,
            },
            ensemble={"models": [{"model": "a", "provider": "p1", "role": "r1"}]},
            synthesizer={"model": "s", "provider": "p1"},
            benchmark={
                "conversao_geral_min": 0.02, "conversao_geral_max": 0.08,
                "agendamento_min": 0.01, "agendamento_max": 0.08,
                "whatsapp_reply_min": 0.10, "whatsapp_reply_max": 0.20,
            },
            gocat={},
            execution={"seeds": []},
        )
