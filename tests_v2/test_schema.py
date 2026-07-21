"""Testes do schema pydantic do Simulation Army v2."""
import pytest
from pydantic import ValidationError

from simulation_army_v2.schema import (
    ConcordanciaPar,
    DecisaoAggregada,
    DecisaoPersona,
    divergence_score_from_decisoes,
)


def _valid_persona(**overrides) -> dict:
    base = {
        "decisao": "agendou",
        "wtp": 500.0,
        "sentimento": 0.7,
        "objecoes": ["budget"],
        "confianca": 0.8,
        "raciocinio": "Bom negocio para o estoque",
        "modelo": "gpt-4o",
    }
    base.update(overrides)
    return base


def test_decisao_persona_valida():
    d = DecisaoPersona(**_valid_persona())
    assert d.decisao == "agendou"
    assert d.wtp == 500.0
    assert d.modelo == "gpt-4o"


def test_decisao_persona_rejeita_decisao_invalida():
    with pytest.raises(ValidationError):
        DecisaoPersona(**_valid_persona(decisao="invalido"))


def test_decisao_persona_rejeita_wtp_negativo():
    with pytest.raises(ValidationError):
        DecisaoPersona(**_valid_persona(wtp=-1))


def test_decisao_persona_rejeita_sentimento_acima_1():
    with pytest.raises(ValidationError):
        DecisaoPersona(**_valid_persona(sentimento=2.0))


def test_decisao_persona_rejeita_sentimento_abaixo_menos1():
    with pytest.raises(ValidationError):
        DecisaoPersona(**_valid_persona(sentimento=-2.0))


def test_decisao_persona_rejeita_confianca_acima_1():
    with pytest.raises(ValidationError):
        DecisaoPersona(**_valid_persona(confianca=1.5))


def test_decisao_persona_rejeita_raciocinio_vazio():
    with pytest.raises(ValidationError):
        DecisaoPersona(**_valid_persona(raciocinio=""))


def test_decisao_persona_rejeita_objecao_invalida():
    with pytest.raises(ValidationError):
        DecisaoPersona(**_valid_persona(objecoes=["categoria_inexistente"]))


def test_decisao_aggregada_valida():
    agg = DecisaoAggregada(
        decisao_final="agendou",
        wtp_medio=316.67,
        sentimento_medio=0.3,
        objecoes_consolidadas=["budget", "need_lack"],
        divergence_score=0.5,
        concordancia=[
            ConcordanciaPar(modelo_a="gpt-4o", modelo_b="DeepSeek-V3.1", concordam=False),
        ],
        confianca_agregada=0.8,
        raciocinio_sintese="Maioria agendou",
    )
    assert agg.decisao_final == "agendou"
    assert len(agg.concordancia) == 1


def test_divergence_score_unanime():
    d = DecisaoPersona(**_valid_persona())
    assert divergence_score_from_decisoes([d, d, d]) == 0.0


def test_divergence_score_split_total():
    d1 = DecisaoPersona(**_valid_persona(decisao="agendou"))
    d2 = DecisaoPersona(**_valid_persona(decisao="ignorou"))
    assert divergence_score_from_decisoes([d1, d2]) == 1.0


def test_divergence_score_parcial_3_modelos_2_distintas():
    d1 = DecisaoPersona(**_valid_persona(decisao="agendou"))
    d2 = DecisaoPersona(**_valid_persona(decisao="ignorou"))
    d3 = DecisaoPersona(**_valid_persona(decisao="agendou"))
    assert divergence_score_from_decisoes([d1, d2, d3]) == 0.5


def test_divergence_score_single():
    d = DecisaoPersona(**_valid_persona())
    assert divergence_score_from_decisoes([d]) == 0.0


def test_divergence_score_empty_raises():
    with pytest.raises(ValueError, match="vazia"):
        divergence_score_from_decisoes([])


def test_decisao_persona_dedup_objecoes():
    d = DecisaoPersona(**_valid_persona(objecoes=["budget", "budget", "timing"]))
    assert d.objecoes == ["budget", "timing"]


def test_decisao_persona_rejeita_objecao_none():
    with pytest.raises(ValidationError):
        DecisaoPersona(**_valid_persona(objecoes=["none"]))


def test_concordancia_par_rejeita_modelos_iguais():
    with pytest.raises(ValidationError, match="distintos"):
        ConcordanciaPar(modelo_a="gpt-4o", modelo_b="gpt-4o", concordam=True)
