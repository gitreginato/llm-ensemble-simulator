"""Testes para integracao de personas V5 no ensemble.

Testa _profile_v5_to_prompt_kwargs, USER_PROMPT_TEMPLATE_V5, e deteccao de
persona_version no run_ensemble.
"""
from unittest.mock import MagicMock

from simulation_army_v2.baseline import USER_PROMPT_TEMPLATE_V5, _profile_v5_to_prompt_kwargs
from simulation_army_v2.personas_v5 import generate_personas_v5


def _mock_cfg():
    """Cfg mockado com scenario minimo para testar _profile_v5_to_prompt_kwargs."""
    cfg = MagicMock()
    cfg.scenario.product_name = "Sistema EMIVE"
    cfg.scenario.description = "Monitoramento 24h"
    cfg.scenario.price_brl = 1.0
    cfg.scenario.channel = "word_of_mouth"
    cfg.scenario.value_proposition = "Protecao do estoque"
    cfg.scenario.pain_focus = "Arrombamento"
    return cfg


def test_profile_v5_to_prompt_kwargs_returns_all_fields():
    """_profile_v5_to_prompt_kwargs retorna dict com 25+ campos."""
    personas = generate_personas_v5(n=1, seed=42)
    p = personas[0]
    cfg = _mock_cfg()
    kwargs = _profile_v5_to_prompt_kwargs(p, cfg)
    assert len(kwargs) >= 25
    assert "owner_name" in kwargs
    assert "bairro" in kwargs
    assert "mensalidade_emive" in kwargs
    assert "ticket_medio_36m" in kwargs
    assert "area_externa_nota" in kwargs
    assert "concorrencia_nota" in kwargs
    assert "segment_perene" in kwargs


def test_profile_v5_to_prompt_kwargs_area_externa_nota():
    """area_externa_nota menciona PRECISA quando precisa_area_externa=True."""
    personas = generate_personas_v5(n=50, seed=42)
    cfg = _mock_cfg()
    # Encontrar persona com precisa_area_externa=True.
    p_externa = next((p for p in personas if p.precisa_area_externa), None)
    if p_externa:
        kwargs = _profile_v5_to_prompt_kwargs(p_externa, cfg)
        assert "PRECISA" in kwargs["area_externa_nota"]
    # Encontrar persona com precisa_area_externa=False.
    p_interna = next((p for p in personas if not p.precisa_area_externa), None)
    if p_interna:
        kwargs = _profile_v5_to_prompt_kwargs(p_interna, cfg)
        assert "nao precisa" in kwargs["area_externa_nota"]


def test_profile_v5_to_prompt_kwargs_concorrencia_nota():
    """concorrencia_nota menciona 20-30 quando concorrencia_local_instalada=True."""
    personas = generate_personas_v5(n=50, seed=42)
    cfg = _mock_cfg()
    p_conc = next((p for p in personas if p.concorrencia_local_instalada), None)
    if p_conc:
        kwargs = _profile_v5_to_prompt_kwargs(p_conc, cfg)
        assert "20-30" in kwargs["concorrencia_nota"]
    p_sem = next((p for p in personas if not p.concorrencia_local_instalada), None)
    if p_sem:
        kwargs = _profile_v5_to_prompt_kwargs(p_sem, cfg)
        assert "baixa" in kwargs["concorrencia_nota"]


def test_user_prompt_template_v5_mentions_mensalidade():
    """USER_PROMPT_TEMPLATE_V5 menciona mensalidade e contrato."""
    assert "mensalidade" in USER_PROMPT_TEMPLATE_V5.lower()
    assert "contrato" in USER_PROMPT_TEMPLATE_V5.lower()
    assert "area interna" in USER_PROMPT_TEMPLATE_V5.lower()


def test_user_prompt_template_v5_mentions_area_externa_objection():
    """USER_PROMPT_TEMPLATE_V5 menciona objecao area_externa."""
    assert "area_externa" in USER_PROMPT_TEMPLATE_V5
    assert "concorrencia_local" in USER_PROMPT_TEMPLATE_V5
    assert "contract_fear" in USER_PROMPT_TEMPLATE_V5
    assert "ticket_alto" in USER_PROMPT_TEMPLATE_V5


def test_user_prompt_template_v5_formats_without_error():
    """USER_PROMPT_TEMPLATE_V5 formata sem erro com kwargs de persona V5."""
    personas = generate_personas_v5(n=1, seed=42)
    p = personas[0]
    cfg = _mock_cfg()
    kwargs = _profile_v5_to_prompt_kwargs(p, cfg)
    # Nao deve levantar KeyError.
    prompt = USER_PROMPT_TEMPLATE_V5.format(**kwargs)
    assert "mensalidade" in prompt.lower()
    assert p.owner_name in prompt
    assert p.bairro in prompt


def test_user_prompt_template_v5_has_bairro_real():
    """Prompt gerado menciona bairro real de Sao Luis."""
    personas = generate_personas_v5(n=1, seed=42)
    p = personas[0]
    cfg = _mock_cfg()
    kwargs = _profile_v5_to_prompt_kwargs(p, cfg)
    prompt = USER_PROMPT_TEMPLATE_V5.format(**kwargs)
    # Bairro deve aparecer no prompt.
    assert p.bairro in prompt
    assert p.bairro_risco in prompt


def test_config_supports_persona_version():
    """ScenarioConfig aceita persona_version=v5."""
    from simulation_army_v2.config import ScenarioConfig
    sc = ScenarioConfig(
        code="TEST", name="test", project="test",
        product_name="test", description="test",
        price_brl=1.0, price_model="visit",
        target_segment="all", channel="whatsapp",
        value_proposition="test", pain_focus="test",
        persona_version="v5",
    )
    assert sc.persona_version == "v5"


def test_config_default_persona_version_is_v4():
    """ScenarioConfig default persona_version e v4."""
    from simulation_army_v2.config import ScenarioConfig
    sc = ScenarioConfig(
        code="TEST", name="test", project="test",
        product_name="test", description="test",
        price_brl=1.0, price_model="visit",
        target_segment="all", channel="whatsapp",
        value_proposition="test", pain_focus="test",
    )
    assert sc.persona_version == "v4"


def test_config_supports_mes():
    """ExecutionConfig aceita mes."""
    from simulation_army_v2.config import ExecutionConfig
    ec = ExecutionConfig(mes=6)
    assert ec.mes == 6


def test_config_default_mes_is_7():
    """ExecutionConfig default mes e 7."""
    from simulation_army_v2.config import ExecutionConfig
    ec = ExecutionConfig()
    assert ec.mes == 7
