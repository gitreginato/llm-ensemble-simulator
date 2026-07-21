"""Testes para personas_v5.py."""
from simulation_army_v2.bairros_slz import BAIRROS_SLZ
from simulation_army_v2.personas_v5 import (
    MENSALIDADE_MIN,
    PersonaV5,
    generate_personas_v5,
    persona_to_dict,
)


def test_gerar_10_personas():
    personas = generate_personas_v5(n=10, seed=42)
    assert len(personas) == 10
    assert all(isinstance(p, PersonaV5) for p in personas)


def test_persona_tem_bairro_real():
    personas = generate_personas_v5(n=50, seed=42)
    for p in personas:
        assert p.bairro in BAIRROS_SLZ, f"Bairro {p.bairro} nao esta em BAIRROS_SLZ"


def test_persona_tem_budget_mensal():
    personas = generate_personas_v5(n=10, seed=42)
    for p in personas:
        assert p.budget_mensal_seguranca > 0
        assert p.wtp_brl > 0


def test_pode_pagar_mensalidade_calculado():
    personas = generate_personas_v5(n=100, seed=42)
    # Pelo menos alguns podem pagar
    podem = sum(1 for p in personas if p.pode_pagar_mensalidade)
    assert podem > 0
    # Verifica consistencia: pode_pagar = budget >= mensalidade_da_persona
    for p in personas:
        assert p.pode_pagar_mensalidade == (p.budget_mensal_seguranca >= p.mensalidade_emive)


def test_sazonalidade_junho_aumenta_revenue():
    personas_junho = generate_personas_v5(n=50, mes=6, segment="loja_roupas", seed=42)
    personas_julho = generate_personas_v5(n=50, mes=7, segment="loja_roupas", seed=42)
    rev_junho = sum(p.revenue_mensal for p in personas_junho) / 50
    rev_julho = sum(p.revenue_mensal for p in personas_julho) / 50
    assert rev_junho > rev_julho, f"Junho deveria ter revenue maior: {rev_junho} vs {rev_julho}"


def test_sazonalidade_label():
    personas_junho = generate_personas_v5(n=10, mes=6, seed=42)
    assert personas_junho[0].season == "alta"
    personas_julho = generate_personas_v5(n=10, mes=7, seed=42)
    assert personas_julho[0].season == "media"


def test_bairro_perigoso_tem_mais_theft():
    """Bairros muito_alto devem ter mais theft que bairros baixo."""
    from collections import Counter
    # Gera muitas personas para ter amostra significativa
    personas = generate_personas_v5(n=500, seed=42)
    # Agrupa por risco do bairro
    por_risco = {}
    for p in personas:
        if p.bairro_risco not in por_risco:
            por_risco[p.bairro_risco] = {"total": 0, "theft": 0}
        por_risco[p.bairro_risco]["total"] += 1
        if p.recent_event == "theft":
            por_risco[p.bairro_risco]["theft"] += 1
    # Calcula taxa de theft por risco
    taxas = {r: d["theft"] / d["total"] for r, d in por_risco.items()}
    # Muito alto deve ter taxa maior que baixo (se ambos existem)
    if "muito_alto" in taxas and "baixo" in taxas:
        assert taxas["muito_alto"] > taxas["baixo"], \
            f"muito_alto deveria ter mais theft: {taxas}"


def test_segment_especifico():
    personas = generate_personas_v5(n=10, segment="bar", seed=42)
    assert all(p.segment == "bar" for p in personas)


def test_segment_distribuido():
    personas = generate_personas_v5(n=100, seed=42)
    segments = set(p.segment for p in personas)
    assert len(segments) > 1  # Mais de um nicho


def test_bio_nao_vazio():
    personas = generate_personas_v5(n=10, seed=42)
    for p in personas:
        assert len(p.bio) > 20
        assert p.segment.replace("_", " ") in p.bio


def test_persona_to_dict():
    personas = generate_personas_v5(n=5, seed=42)
    d = persona_to_dict(personas[0])
    assert "id" in d
    assert "bairro" in d
    assert "budget_mensal_seguranca" in d
    assert "pode_pagar_mensalidade" in d
    assert "mensalidade_emive" in d
    assert d["mensalidade_emive"] >= MENSALIDADE_MIN


def test_reproducibilidade_seed():
    p1 = generate_personas_v5(n=10, seed=42)
    p2 = generate_personas_v5(n=10, seed=42)
    assert [p.owner_name for p in p1] == [p.owner_name for p in p2]


def test_ids_sequenciais():
    personas = generate_personas_v5(n=10, seed=42)
    assert [p.id for p in personas] == list(range(1, 11))


def test_ticket_medio_36m_calculado():
    """Ticket medio = mensalidade * 36 meses."""
    personas = generate_personas_v5(n=10, seed=42)
    for p in personas:
        assert p.ticket_medio_36m > 0
        assert abs(p.ticket_medio_36m - p.mensalidade_emive * 36) < 0.01


def test_contrato_36_meses():
    from simulation_army_v2.personas_v5 import CONTRATO_MESES
    assert CONTRATO_MESES == 36


def test_mensalidade_por_porte():
    """Pequeno paga R$ 294, medio/grande pagam mais."""
    from simulation_army_v2.personas_v5 import SEGMENT_BASELINES_V5, MENSALIDADE_MIN, MENSALIDADE_MAX
    # Nicho de porte pequeno
    personas_peq = generate_personas_v5(n=20, segment="oficina", seed=42)
    for p in personas_peq:
        assert p.mensalidade_emive == MENSALIDADE_MIN, f"Pequeno deveria pagar R$ {MENSALIDADE_MIN}"
    # Nicho de porte grande
    personas_grd = generate_personas_v5(n=20, segment="farmacia", seed=42)
    for p in personas_grd:
        assert p.mensalidade_emive >= 400, f"Grande deveria pagar >= R$ 400"


def test_segmento_perene_vs_volatil():
    """Farmacia e perene, loja_roupas nao e."""
    personas_farm = generate_personas_v5(n=10, segment="farmacia", seed=42)
    for p in personas_farm:
        assert p.segment_perene is True
    personas_roupas = generate_personas_v5(n=10, segment="loja_roupas", seed=42)
    for p in personas_roupas:
        assert p.segment_perene is False


def test_novos_nichos_disponiveis():
    """Novos nichos adicionados devem estar disponiveis."""
    from simulation_army_v2.personas_v5 import SEGMENT_BASELINES_V5
    # Originais
    for n in ["loja_roupas", "bar", "farmacia", "oficina", "autopecas"]:
        assert n in SEGMENT_BASELINES_V5
    # Primeira leva de novos
    for n in ["clinica", "consultorio_odonto", "pet_shop", "mercadinho",
              "barbearia", "salao", "academia", "restaurante"]:
        assert n in SEGMENT_BASELINES_V5
    # Segunda leva: automotivo
    for n in ["estacionamento", "mecanica_diesel", "lava_jato", "borracharia"]:
        assert n in SEGMENT_BASELINES_V5
    # Segunda leva: saude
    for n in ["laboratorio", "clinica_veterinaria", "fisioterapia", "optica"]:
        assert n in SEGMENT_BASELINES_V5
    # Segunda leva: servicos pessoais
    for n in ["estetica", "estudio_tatuagem"]:
        assert n in SEGMENT_BASELINES_V5
    # 26 nichos total
    assert len(SEGMENT_BASELINES_V5) == 26


def test_autopecas_revenue_maior_que_loja_roupas():
    """Autopecas tem revenue maior que loja de roupas (realista)."""
    from simulation_army_v2.personas_v5 import SEGMENT_BASELINES_V5
    auto_min = SEGMENT_BASELINES_V5["autopecas"]["revenue"][0]
    roupa_max = SEGMENT_BASELINES_V5["loja_roupas"]["revenue"][1]
    assert auto_min > roupa_max, \
        f"autopecas min ({auto_min}) deveria ser > loja_roupas max ({roupa_max})"


def test_multa_proporcional_base():
    """Multa base = 35 * mensalidade (36 meses - 1)."""
    personas = generate_personas_v5(n=10, seed=42)
    for p in personas:
        expected = (36 - 1) * p.mensalidade_emive
        assert abs(p.multa_proporcional_base - expected) < 0.01


def test_revenue_perene_menos_afetado_sazonalidade():
    """Segmentos perenes sao menos afetados pela sazonalidade."""
    # Farmacia (perene) em junho vs julho
    farm_junho = generate_personas_v5(n=50, mes=6, segment="farmacia", seed=42)
    farm_julho = generate_personas_v5(n=50, mes=7, segment="farmacia", seed=42)
    rev_junho = sum(p.revenue_mensal for p in farm_junho) / 50
    rev_julho = sum(p.revenue_mensal for p in farm_julho) / 50
    # Perene: aumento menor que volatil
    aumento_pct = (rev_junho - rev_julho) / rev_julho
    assert aumento_pct < 0.30, f"Perene nao deveria aumentar mais que 30%: {aumento_pct:.0%}"

    # Loja de roupas (volatil) em junho vs julho
    roupas_junho = generate_personas_v5(n=50, mes=6, segment="loja_roupas", seed=42)
    roupas_julho = generate_personas_v5(n=50, mes=7, segment="loja_roupas", seed=42)
    rev_rj = sum(p.revenue_mensal for p in roupas_junho) / 50
    rev_rjl = sum(p.revenue_mensal for p in roupas_julho) / 50
    aumento_volatil = (rev_rj - rev_rjl) / rev_rjl
    # Volatil aumenta mais que perene
    assert aumento_volatil > aumento_pct, \
        f"Volatil deveria aumentar mais que perene: volatil={aumento_volatil:.0%} perene={aumento_pct:.0%}"


def test_precisa_area_externa_gerado():
    """Toda persona tem o campo precisa_area_externa."""
    personas = generate_personas_v5(n=50, seed=42)
    for p in personas:
        assert isinstance(p.precisa_area_externa, bool)


def test_estacionamento_precisa_mais_area_externa_que_clinica():
    """Estacionamento tem p=0.95 de precisar externa, clinica 0.45."""
    est = generate_personas_v5(n=200, segment="estacionamento", seed=42)
    cli = generate_personas_v5(n=200, segment="clinica", seed=42)
    pct_est = sum(1 for p in est if p.precisa_area_externa) / 200
    pct_cli = sum(1 for p in cli if p.precisa_area_externa) / 200
    assert pct_est > pct_cli, \
        f"Estacionamento ({pct_est:.0%}) deveria precisar mais de area externa que clinica ({pct_cli:.0%})"


def test_concorrencia_local_gerado():
    """Toda persona tem o campo concorrencia_local_instalada."""
    personas = generate_personas_v5(n=50, seed=42)
    for p in personas:
        assert isinstance(p.concorrencia_local_instalada, bool)


def test_concorrencia_local_presente():
    """Pelo menos 20% das personas tem concorrencia local instalada."""
    personas = generate_personas_v5(n=200, seed=42)
    pct = sum(1 for p in personas if p.concorrencia_local_instalada) / 200
    assert pct > 0.20, f"Esperado >20% com concorrencia local, got {pct:.0%}"


def test_area_externa_no_dict():
    """persona_to_dict inclui os novos campos."""
    personas = generate_personas_v5(n=5, seed=42)
    d = persona_to_dict(personas[0])
    assert "precisa_area_externa" in d
    assert "concorrencia_local_instalada" in d
