"""Testes para informacao.py."""
from simulation_army_v2.informacao import (
    analise_completa,
    chi_quadrado,
    divergencia_entre_nichos,
    divergencia_jensen_shannon,
    entropia_maxima,
    entropia_normalizada,
    entropia_por_grupo,
    entropia_shannon,
    informacao_mutua,
    ranquear_features_por_mi,
)


def test_entropia_deterministica():
    """Distribuicao com 1 categoria tem entropia 0."""
    assert entropia_shannon({"a": 100}) == 0.0


def test_entropia_uniforme_2_categorias():
    """Distribuicao uniforme com 2 categorias tem H = 1 bit."""
    h = entropia_shannon({"a": 50, "b": 50})
    assert abs(h - 1.0) < 0.001


def test_entropia_uniforme_4_categorias():
    """Distribuicao uniforme com 4 categorias tem H = 2 bits."""
    h = entropia_shannon({"a": 25, "b": 25, "c": 25, "d": 25})
    assert abs(h - 2.0) < 0.001


def test_entropia_maxima():
    assert entropia_maxima(1) == 0.0
    assert abs(entropia_maxima(2) - 1.0) < 0.001
    assert abs(entropia_maxima(4) - 2.0) < 0.001


def test_entropia_normalizada_deterministica():
    assert entropia_normalizada({"a": 100}) == 0.0


def test_entropia_normalizada_uniforme():
    assert abs(entropia_normalizada({"a": 50, "b": 50}) - 1.0) < 0.001


def test_entropia_vazia():
    assert entropia_shannon({}) == 0.0


def test_informacao_mutua_independente():
    """Features independentes tem MI ~ 0."""
    feature = {str(i): "A" if i < 50 else "B" for i in range(100)}
    target = {str(i): "X" if i % 2 == 0 else "Y" for i in range(100)}
    mi = informacao_mutua(feature, target)
    assert mi < 0.01, f"Features independentes deveriam ter MI ~ 0, got {mi}"


def test_informacao_mutua_perfeitamente_correlacionada():
    """Features identicas tem MI = H(X)."""
    feature = {str(i): "A" if i < 50 else "B" for i in range(100)}
    target = {str(i): "A" if i < 50 else "B" for i in range(100)}
    mi = informacao_mutua(feature, target)
    assert abs(mi - 1.0) < 0.01, f"Features identicas deveriam ter MI = 1, got {mi}"


def test_informacao_mutua_correlacionada_parcial():
    """Feature parcialmente correlacionada tem 0 < MI < H."""
    feature = {str(i): "A" if i < 50 else "B" for i in range(100)}
    target = {str(i): "X" if i < 40 else ("Y" if i < 50 else "X") for i in range(100)}
    mi = informacao_mutua(feature, target)
    assert 0 < mi < 1.0


def test_divergencia_js_identicas():
    """Distribuicoes identicas tem JSD = 0."""
    dist = {"a": 0.5, "b": 0.5}
    jsd = divergencia_jensen_shannon(dist, dist)
    assert jsd < 0.001


def test_divergencia_js_diferentes():
    """Distribuicoes totalmente diferentes tem JSD alta."""
    d1 = {"a": 1.0, "b": 0.0}
    d2 = {"a": 0.0, "b": 1.0}
    jsd = divergencia_jensen_shannon(d1, d2)
    assert jsd > 0.5


def test_chi_quadrado_independente():
    """Tabela com distribuicao proporcional tem chi2 baixo."""
    tabela = {
        "A": {"X": 50, "Y": 50},
        "B": {"X": 50, "Y": 50},
    }
    result = chi_quadrado(tabela)
    assert result["chi2"] < 1.0
    assert result["gl"] == 1


def test_chi_quadrado_dependente():
    """Tabela com dependencia forte tem chi2 alto."""
    tabela = {
        "A": {"X": 100, "Y": 0},
        "B": {"X": 0, "Y": 100},
    }
    result = chi_quadrado(tabela)
    assert result["chi2"] > 100
    assert "0.001" in result["p_value_approx"]


def test_ranquear_features_por_mi():
    """MI deve ranquear features."""
    personas = [
        {"recent_event": "theft", "has_existing_security": "none",
         "risk_profile": "crisis", "segment": "loja_roupas", "decisao": "agendou"}
        for _ in range(10)
    ] + [
        {"recent_event": "none", "has_existing_security": "full_system",
         "risk_profile": "pragmatic", "segment": "farmacia", "decisao": "visualizou"}
        for _ in range(10)
    ]
    ranking = ranquear_features_por_mi(personas)
    assert len(ranking) == 4
    # Todas tem MI > 0 pois sao perfeitamente correlacionadas
    for feat, mi in ranking:
        assert mi > 0.5


def test_entropia_por_grupo():
    personas = [
        {"segment": "A", "decisao": "agendou"},
        {"segment": "A", "decisao": "visualizou"},
        {"segment": "B", "decisao": "agendou"},
        {"segment": "B", "decisao": "agendou"},
    ]
    result = entropia_por_grupo(personas, "segment")
    assert result["A"]["h_bits"] == 1.0  # 50/50
    assert result["B"]["h_bits"] == 0.0  # deterministico


def test_divergencia_entre_nichos():
    personas = [
        {"segment": "A", "decisao": "agendou"},
        {"segment": "A", "decisao": "visualizou"},
        {"segment": "B", "decisao": "agendou"},
        {"segment": "B", "decisao": "agendou"},
    ]
    result = divergencia_entre_nichos(personas)
    assert "A vs B" in result
    assert result["A vs B"]["jsd"] > 0


def test_analise_completa_rodar():
    """Analise completa deve rodar sem erro no dataset real."""
    resultado = analise_completa()
    assert resultado["n_personas"] > 0
    assert "entropia_global" in resultado
    assert "informacao_mutua_features" in resultado
    assert len(resultado["informacao_mutua_features"]) > 0
