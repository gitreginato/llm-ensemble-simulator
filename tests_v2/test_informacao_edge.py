"""Testes de edge cases para informacao.py.

Cobre situacoes extremas: entradas vazias, dados degenerados, arquivos ausentes.
Cada teste verifica um cenario que poderia causar crash, resultado errado, ou
comportamento indefinido.
"""
import pytest

from simulation_army_v2.informacao import (
    analise_completa,
    chi_quadrado,
    divergencia_jensen_shannon,
    entropia_por_grupo,
    entropia_shannon,
    informacao_mutua,
    ranquear_features_por_mi,
)


# ---------------------------------------------------------------------------
# 1. entropia_shannon com distribuicao vazia
# ---------------------------------------------------------------------------
def test_entropia_shannon_vazia():
    """Distribuicao vazia deve retornar 0.0, nao crashar."""
    assert entropia_shannon({}) == 0.0


# ---------------------------------------------------------------------------
# 2. entropia_shannon com categoria unica (deterministico)
# ---------------------------------------------------------------------------
def test_entropia_shannon_categoria_unica():
    """Distribuicao com uma categoria tem entropia 0."""
    assert entropia_shannon({"a": 4}) == 0.0
    assert entropia_shannon({"x": 100}) == 0.0


# ---------------------------------------------------------------------------
# 3. entropia_shannon com todos valores unicos (maxima incerteza)
# ---------------------------------------------------------------------------
def test_entropia_shannon_todos_unicos():
    """Distribuicao uniforme com n categorias tem H = log2(n)."""
    import math

    dist = {"a": 1, "b": 1, "c": 1, "d": 1}
    h = entropia_shannon(dist)
    assert abs(h - math.log2(4)) < 0.001


# ---------------------------------------------------------------------------
# 4. informacao_mutua com personas vazias
# ---------------------------------------------------------------------------
def test_informacao_mutua_vazia():
    """MI de conjuntos vazios deve ser 0.0, nao crashar."""
    assert informacao_mutua({}, {}) == 0.0


# ---------------------------------------------------------------------------
# 5. informacao_mutua onde todas as decisoes sao iguais (sem entropia no target)
# ---------------------------------------------------------------------------
def test_informacao_mutua_target_constante():
    """Target sem entropia (constante) deve ter MI = 0."""
    feature = {str(i): "A" if i < 50 else "B" for i in range(100)}
    target = {str(i): "X" for i in range(100)}
    mi = informacao_mutua(feature, target)
    assert mi == 0.0


def test_informacao_mutua_nunca_negativa():
    """MI nunca deve ser negativa. Floating point pode produzir -1e-16.

    MI >= 0 e uma propriedade matematica. Sem clamp (max(0, ...)),
    floating point pode violar isso em casos independentes.
    Testa muitos casos aleatorios para garantir robustez.
    """
    import random

    random.seed(0)
    for _ in range(5000):
        n = random.randint(2, 50)
        nc1 = random.randint(2, 10)
        nc2 = random.randint(2, 10)
        cats1 = [chr(65 + i) for i in range(nc1)]
        cats2 = [chr(97 + i) for i in range(nc2)]
        feature = {str(i): random.choice(cats1) for i in range(n)}
        target = {str(i): random.choice(cats2) for i in range(n)}
        mi = informacao_mutua(feature, target)
        assert mi >= 0.0, f"MI nao deve ser negativa, got {mi} (n={n})"


# ---------------------------------------------------------------------------
# 6. divergencia_jensen_shannon com distribuicoes vazias
# ---------------------------------------------------------------------------
def test_divergencia_js_ambas_vazias():
    """JSD de duas distribuicoes vazias deve ser 0.0, nao crashar."""
    jsd = divergencia_jensen_shannon({}, {})
    assert jsd == 0.0


def test_divergencia_js_uma_vazia():
    """JSD de uma vazia e uma nao-vazia nao deve crashar."""
    jsd = divergencia_jensen_shannon({"a": 1.0}, {})
    assert jsd >= 0.0
    assert not isinstance(jsd, complex)


# ---------------------------------------------------------------------------
# 7. chi_quadrado com tabela toda zerada
# ---------------------------------------------------------------------------
def test_chi_quadrado_todos_zeros():
    """Tabela com todos zeros deve retornar chi2=0, gl=0, N/A."""
    tabela = {"A": {"X": 0, "Y": 0}, "B": {"X": 0, "Y": 0}}
    result = chi_quadrado(tabela)
    assert result["chi2"] == 0.0
    assert result["gl"] == 0
    assert result["p_value_approx"] == "N/A"


def test_chi_quadrado_tabela_vazia():
    """Tabela vazia (sem linhas) deve retornar N/A."""
    result = chi_quadrado({})
    assert result["chi2"] == 0.0
    assert result["gl"] == 0


# ---------------------------------------------------------------------------
# 8. entropia_por_grupo com grupo que tem 0 personas (key ausente)
# ---------------------------------------------------------------------------
def test_entropia_por_grupo_personas_vazias():
    """Lista de personas vazia deve retornar dict vazio."""
    result = entropia_por_grupo([], "segment")
    assert result == {}


def test_entropia_por_grupo_key_inexistente():
    """grupo_key que nao existe nos personas nao deve crashar (KeyError).

    Personas sem a chave grupo_key devem ser puladas, nao causar crash.
    """
    personas = [
        {"segment": "A", "decisao": "agendou"},
        {"segment": "A", "decisao": "visualizou"},
    ]
    # key inexistente: nenhum persona tem "bairro"
    result = entropia_por_grupo(personas, "bairro")
    assert result == {}


def test_entropia_por_grupo_decisao_ausente():
    """Persona sem 'decisao' nao deve crashar."""
    personas = [
        {"segment": "A", "decisao": "agendou"},
        {"segment": "A"},  # sem decisao
    ]
    result = entropia_por_grupo(personas, "segment")
    assert "A" in result
    assert result["A"]["n"] == 1  # so 1 persona com decisao


# ---------------------------------------------------------------------------
# 9. ranquear_features_por_mi com lista de features vazia / personas vazias
# ---------------------------------------------------------------------------
def test_ranquear_features_por_mi_personas_vazias():
    """Personas vazias deve retornar lista vazia, nao 4 tuples com 0.0."""
    result = ranquear_features_por_mi([])
    assert result == []


def test_ranquear_features_por_mi_features_vazias():
    """Lista de features vazia deve retornar lista vazia."""
    personas = [
        {"recent_event": "theft", "has_existing_security": "none",
         "risk_profile": "crisis", "segment": "loja", "decisao": "agendou"},
    ]
    result = ranquear_features_por_mi(personas, features=[])
    assert result == []


# ---------------------------------------------------------------------------
# 10. analise_completa com arquivo de dataset ausente
# ---------------------------------------------------------------------------
def test_analise_completa_arquivo_inexistente():
    """Dataset ausente deve retornar dict de erro, nao crashar."""
    result = analise_completa("caminho/inexistente/dataset.json")
    assert "erro" in result
    assert result["n_personas"] == 0
