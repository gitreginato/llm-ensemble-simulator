"""Medidas de informacao: entropia de Shannon, informacao mutua, divergencia Jensen-Shannon.

Calcula sobre o dataset real (142 personas) e sobre resultados de simulacao.
Usa apenas math + collections da stdlib. numpy so para operacoes vetoriais simples.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np


def entropia_shannon(distribuicao: dict[str, int]) -> float:
    """Entropia de Shannon H(X) em bits.

    H(X) = -sum p(x) * log2(p(x))

    Args:
        distribuicao: {categoria: contagem}

    Returns:
        Entropia em bits. 0 = deterministico. log2(n) = maxima incerteza.
    """
    total = sum(distribuicao.values())
    if total == 0:
        return 0.0
    h = 0.0
    for count in distribuicao.values():
        if count > 0:
            p = count / total
            h -= p * math.log2(p)
    return h


def entropia_maxima(n_categorias: int) -> float:
    """Entropia maxima para n categorias (distribuicao uniforme)."""
    if n_categorias <= 1:
        return 0.0
    return math.log2(n_categorias)


def entropia_normalizada(distribuicao: dict[str, int]) -> float:
    """Entropia normalizada: H / H_max. 0 = deterministico, 1 = maxima incerteza."""
    h = entropia_shannon(distribuicao)
    n = len([v for v in distribuicao.values() if v > 0])
    h_max = entropia_maxima(n)
    if h_max == 0:
        return 0.0
    return h / h_max


def informacao_mutua(feature: dict[str, str], target: dict[str, str]) -> float:
    """Informacao mutua I(X ; Y) em bits.

    I(X;Y) = H(X) + H(Y) - H(X,Y)

    Args:
        feature: {id_persona: valor_feature}
        target: {id_persona: valor_target}

    Returns:
        MI em bits. 0 = independente. Alto = feature carrega info sobre target.
    """
    ids = set(feature.keys()) & set(target.keys())
    if not ids:
        return 0.0

    # Distribuicoes marginais
    dist_x = defaultdict(int)
    dist_y = defaultdict(int)
    dist_xy = defaultdict(int)
    for id_ in ids:
        dist_x[feature[id_]] += 1
        dist_y[target[id_]] += 1
        dist_xy[(feature[id_], target[id_])] += 1

    h_x = entropia_shannon(dist_x)
    h_y = entropia_shannon(dist_y)
    h_xy = entropia_shannon(dist_xy)

    # ponytail: MI >= 0 sempre. Floating point pode produzir -1e-16.
    return max(0.0, h_x + h_y - h_xy)


def divergencia_jensen_shannon(dist1: dict[str, float], dist2: dict[str, float]) -> float:
    """Divergencia Jensen-Shannon entre duas distribuicoes.

    JSD(P || Q) = 0.5 * KL(P || M) + 0.5 * KL(Q || M)
    onde M = 0.5 * (P + Q)

    Args:
        dist1: {categoria: probabilidade}
        dist2: {categoria: probabilidade}

    Returns:
        JSD em bits. 0 = distribuicoes identicas. ~1 = totalmente diferentes.
    """
    if not dist1 and not dist2:
        return 0.0
    categorias = set(dist1.keys()) | set(dist2.keys())
    p = np.array([dist1.get(c, 0.0) for c in categorias])
    q = np.array([dist2.get(c, 0.0) for c in categorias])

    # Normalizar (caso nao somem 1)
    if p.sum() > 0:
        p = p / p.sum()
    if q.sum() > 0:
        q = q / q.sum()

    m = 0.5 * (p + q)

    def kl(a: np.ndarray, b: np.ndarray) -> float:
        mask = a > 0
        return float(np.sum(a[mask] * np.log2(a[mask] / np.maximum(b[mask], 1e-300))))

    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def chi_quadrado(tabela: dict[str, dict[str, int]]) -> dict[str, Any]:
    """Teste chi-quadrado de independencia entre duas variaveis categoricas.

    Args:
        tabela: {categoria_linha: {categoria_coluna: contagem}}

    Returns:
        {"chi2": float, "gl": int, "p_value_approx": str}
    """
    linhas = list(tabela.keys())
    colunas = list(set(c for linha in tabela.values() for c in linha.keys()))

    # Totais
    total_geral = sum(sum(linha.values()) for linha in tabela.values())
    if total_geral == 0:
        return {"chi2": 0.0, "gl": 0, "p_value_approx": "N/A"}

    total_linhas = {l: sum(tabela[l].values()) for l in linhas}
    total_colunas = {c: sum(tabela[l].get(c, 0) for l in linhas) for c in colunas}

    # Chi-quadrado
    chi2 = 0.0
    for l in linhas:
        for c in colunas:
            observado = tabela[l].get(c, 0)
            esperado = (total_linhas[l] * total_colunas[c]) / total_geral
            if esperado > 0:
                chi2 += (observado - esperado) ** 2 / esperado

    gl = (len(linhas) - 1) * (len(colunas) - 1)

    # Aproximacao p-value (tabela chi-quadrado simplificada)
    if gl == 0:
        p_value = "N/A"
    elif chi2 < 0.004:
        p_value = "> 0.95"
    elif chi2 < 0.10:
        p_value = "> 0.75"
    elif chi2 < 3.84:
        p_value = "> 0.05"
    elif chi2 < 6.63:
        p_value = "< 0.05"
    elif chi2 < 10.83:
        p_value = "< 0.01"
    else:
        p_value = "< 0.001"

    return {"chi2": round(chi2, 2), "gl": gl, "p_value_approx": p_value}


def ranquear_features_por_mi(personas: list[dict], features: list[str] | None = None) -> list[tuple[str, float]]:
    """Ranqueia features por informacao mutua com a decisao.

    Args:
        personas: lista de dicts com features e "decisao"
        features: lista de nomes de features para calcular MI. Default: 4 features padrao.

    Returns:
        Lista de (feature_name, MI_bits) ordenada por MI decrescente.
    """
    if not personas:
        return []
    if features is None:
        features = ["recent_event", "has_existing_security", "risk_profile", "segment"]
    if not features:
        return []
    target = {str(i): p["decisao"] for i, p in enumerate(personas)}

    resultados = []
    for feat in features:
        feat_map = {str(i): p[feat] for i, p in enumerate(personas) if feat in p}
        mi = informacao_mutua(feat_map, target)
        resultados.append((feat, mi))

    resultados.sort(key=lambda x: -x[1])
    return resultados


def entropia_por_grupo(personas: list[dict], grupo_key: str) -> dict[str, dict]:
    """Calcula entropia de Shannon da decisao para cada grupo.

    Args:
        personas: lista de dicts
        grupo_key: chave para agrupar (ex: "segment", "bairro")

    Returns:
        {grupo: {"h": float, "h_norm": float, "distribuicao": dict, "n": int}}
    """
    grupos = defaultdict(lambda: defaultdict(int))
    for p in personas:
        if grupo_key not in p or "decisao" not in p:
            continue
        grupos[p[grupo_key]][p["decisao"]] += 1

    resultados = {}
    for grupo, dist in grupos.items():
        total = sum(dist.values())
        h = entropia_shannon(dist)
        h_norm = entropia_normalizada(dist)
        resultados[grupo] = {
            "h_bits": round(h, 3),
            "h_norm": round(h_norm, 3),
            "distribuicao": dict(dist),
            "n": total,
        }
    return resultados


def divergencia_entre_nichos(personas: list[dict]) -> dict[str, dict]:
    """Calcula divergencia Jensen-Shannon entre todos os pares de nichos.

    Args:
        personas: lista de dicts com "segment" e "decisao"

    Returns:
        {f"{nicho1} vs {nicho2}": {"jsd": float, "interpretacao": str}}
    """
    # Distribuicao de decisao por nicho
    dist_por_nicho = defaultdict(lambda: defaultdict(int))
    for p in personas:
        dist_por_nicho[p["segment"]][p["decisao"]] += 1

    # Normalizar para probabilidades
    dist_norm = {}
    for nicho, dist in dist_por_nicho.items():
        total = sum(dist.values())
        dist_norm[nicho] = {k: v / total for k, v in dist.items()} if total > 0 else {}

    # JSD para todos os pares
    resultados = {}
    nichos = list(dist_norm.keys())
    for n1, n2 in combinations(nichos, 2):
        jsd = divergencia_jensen_shannon(dist_norm[n1], dist_norm[n2])
        if jsd < 0.05:
            interp = "muito similares"
        elif jsd < 0.15:
            interp = "moderadamente diferentes"
        elif jsd < 0.30:
            interp = "diferentes"
        else:
            interp = "muito diferentes"
        resultados[f"{n1} vs {n2}"] = {"jsd": round(jsd, 4), "interpretacao": interp}

    return resultados


def analise_completa(dataset_path: str = "results_v2/dataset_real.json") -> dict[str, Any]:
    """Executa analise completa de informacao sobre o dataset real.

    Returns:
        Dicionario com todas as medidas. Se arquivo nao existe, retorna {"erro": ..., "n_personas": 0}.
    """
    path = Path(dataset_path)
    if not path.exists():
        return {"erro": f"Dataset nao encontrado: {dataset_path}", "n_personas": 0}
    data = json.loads(path.read_text(encoding="utf-8"))
    personas = data["personas"]

    # Entropia global da decisao
    dist_decisao = defaultdict(int)
    for p in personas:
        dist_decisao[p["decisao"]] += 1
    h_global = entropia_shannon(dist_decisao)
    h_global_norm = entropia_normalizada(dist_decisao)

    # Entropia por nicho
    entropia_nichos = entropia_por_grupo(personas, "segment")

    # Entropia por risk_profile
    entropia_risk = entropia_por_grupo(personas, "risk_profile")

    # MI das features com decisao
    mi_features = ranquear_features_por_mi(personas)

    # JSD entre nichos
    jsd_nichos = divergencia_entre_nichos(personas)

    # Chi-quadrado: nicho vs decisao
    tabela_nicho = defaultdict(lambda: defaultdict(int))
    for p in personas:
        tabela_nicho[p["segment"]][p["decisao"]] += 1
    chi2_nicho = chi_quadrado({k: dict(v) for k, v in tabela_nicho.items()})

    # Chi-quadrado: recent_event vs decisao
    tabela_event = defaultdict(lambda: defaultdict(int))
    for p in personas:
        tabela_event[p["recent_event"]][p["decisao"]] += 1
    chi2_event = chi_quadrado({k: dict(v) for k, v in tabela_event.items()})

    return {
        "n_personas": len(personas),
        "entropia_global": {
            "h_bits": round(h_global, 3),
            "h_norm": round(h_global_norm, 3),
            "distribuicao": dict(dist_decisao),
        },
        "entropia_por_nicho": entropia_nichos,
        "entropia_por_risk_profile": entropia_risk,
        "informacao_mutua_features": [(f, round(mi, 4)) for f, mi in mi_features],
        "divergencia_jensen_shannon_nichos": jsd_nichos,
        "chi_quadrado_nicho_decisao": chi2_nicho,
        "chi_quadrado_event_decisao": chi2_event,
    }
