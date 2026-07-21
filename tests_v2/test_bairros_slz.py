"""Testes para bairros_slz.py."""
from simulation_army_v2.bairros_slz import (
    BAIRROS_SLZ,
    SAZONALIDADE_SLZ,
    get_bairro,
    get_sazonalidade,
    listar_bairros_por_perfil,
    listar_bairros_por_risco,
)


def test_bairros_cadastrados():
    assert len(BAIRROS_SLZ) >= 13
    assert "Calhau" in BAIRROS_SLZ
    assert "Cidade Operaria" in BAIRROS_SLZ
    assert "Renascenca" in BAIRROS_SLZ


def test_bairro_tem_campos_obrigatorios():
    for nome, dados in BAIRROS_SLZ.items():
        assert "empresas" in dados, f"{nome} sem empresas"
        assert "risco" in dados, f"{nome} sem risco"
        assert "perfil" in dados, f"{nome} sem perfil"
        assert "p_theft_base" in dados, f"{nome} sem p_theft_base"
        assert "wtp_multiplier" in dados, f"{nome} sem wtp_multiplier"
        assert 0 < dados["p_theft_base"] <= 0.30
        assert 0.5 < dados["wtp_multiplier"] <= 1.30


def test_bairros_periferia_tem_risco_alto():
    periferia = listar_bairros_por_perfil("periferia")
    for bairro in periferia:
        assert BAIRROS_SLZ[bairro]["risco"] == "muito_alto"
        assert BAIRROS_SLZ[bairro]["p_theft_base"] >= 0.20


def test_bairros_comerciais_alto_tem_wtp_alto():
    comercial_alto = listar_bairros_por_perfil("comercial_alto")
    for bairro in comercial_alto:
        assert BAIRROS_SLZ[bairro]["wtp_multiplier"] >= 1.10


def test_get_bairro_existente():
    bairro = get_bairro("Calhau")
    assert bairro["risco"] == "medio"
    assert bairro["empresas"] == 3789


def test_get_bairro_inexistente_default():
    bairro = get_bairro("Bairro Inexistente")
    assert bairro["risco"] == "medio"
    assert bairro["empresas"] == 1000


def test_sazonalidade_alta_junho_dezembro():
    assert 6 in SAZONALIDADE_SLZ["alta"]["meses"]
    assert 12 in SAZONALIDADE_SLZ["alta"]["meses"]
    assert SAZONALIDADE_SLZ["alta"]["revenue_multiplier"] > 1.0


def test_get_sazonalidade_junho():
    saz = get_sazonalidade(6)
    assert saz["revenue_multiplier"] == 1.30
    assert saz["p_theft_multiplier"] == 1.20


def test_get_sazonalidade_mes_normal():
    saz = get_sazonalidade(3)
    assert saz["revenue_multiplier"] == 1.00


def test_get_sazonalidade_black_friday():
    saz = get_sazonalidade(11)
    assert saz["revenue_multiplier"] == 1.15


def test_listar_por_risco():
    muito_alto = listar_bairros_por_risco("muito_alto")
    assert "Cidade Operaria" in muito_alto
    assert "Coroadinho" in muito_alto
    assert "Vila Embratel" in muito_alto


def test_listar_por_perfil():
    comercial_alto = listar_bairros_por_perfil("comercial_alto")
    assert "Calhau" in comercial_alto
    assert "Renascenca" in comercial_alto
