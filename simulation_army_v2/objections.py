"""Mapa de objecoes ponderado: frequencia x impacto (phi coefficient).

Para cada categoria de objecao:
1. Frequencia: % de personas que citaram
2. Correlacao phi com nao-converter (decisao != agendou)
3. Score = frequencia * abs(phi) * sinal(phi)

Priorizar objecao com maior frequencia x correlacao_negativa.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np

RESULTS_DIR = Path(__file__).parent.parent / "results_v2"


def phi_coefficient(x: list[bool], y: list[bool]) -> float:
    """Coeficiente phi: correlacao entre duas variaveis binarias.

    phi = (n11*n00 - n10*n01) / sqrt(n1.*n0.*n.1*n.0)
    """
    n = len(x)
    if n == 0:
        return 0.0
    n11 = sum(1 for i in range(n) if x[i] and y[i])
    n00 = sum(1 for i in range(n) if not x[i] and not y[i])
    n10 = sum(1 for i in range(n) if x[i] and not y[i])
    n01 = sum(1 for i in range(n) if not x[i] and y[i])
    n1x = n11 + n10
    n0x = n01 + n00
    nx1 = n11 + n01
    nx0 = n10 + n00
    denom = np.sqrt(n1x * n0x * nx1 * nx0)
    if denom == 0:
        return 0.0
    return (n11 * n00 - n10 * n01) / denom


def analisar_objecoes(ensemble_path: str = None) -> dict:
    """Analisa objecoes do ensemble: frequencia x impacto."""
    if ensemble_path is None:
        ensemble_path = str(RESULTS_DIR / "ensemble_n30_s42.json")

    with open(ensemble_path, encoding="utf-8") as f:
        ens = json.load(f)

    # Coletar objecoes e decisao por persona (usar decisao agregada).
    personas_data = []
    for p in ens["personas"]:
        if not p.get("decisao_agregada"):
            continue
        agg = p["decisao_agregada"]
        objecoes = agg.get("objecoes_consolidadas", [])
        converteu = agg["decisao_final"] == "agendou"
        personas_data.append({"objecoes": objecoes, "converteu": converteu})

    n = len(personas_data)
    if n == 0:
        return {"erro": "sem dados", "n": 0}

    # Para cada categoria: frequencia e phi com nao-converter.
    nao_converteu = [not pd["converteu"] for pd in personas_data]
    categorias = set()
    for pd in personas_data:
        categorias.update(pd["objecoes"])
    categorias = sorted(categorias)

    mapa = []
    for cat in categorias:
        citou = [cat in pd["objecoes"] for pd in personas_data]
        freq = sum(citou) / n
        phi = phi_coefficient(citou, nao_converteu)
        # Score: frequencia * abs(phi). phi negativo = objecao associada a nao-converter.
        score = freq * abs(phi)
        mapa.append({
            "categoria": cat,
            "frequencia": round(freq, 4),
            "n_citacoes": sum(citou),
            "phi_coefficient": round(phi, 4),
            "score": round(score, 4),
            "interpretacao": (
                "associada a nao-converter" if phi > 0.1
                else "associada a converter" if phi < -0.1
                else "sem correlacao clara"
            ),
        })

    # Ordenar por score (maior impacto primeiro).
    mapa.sort(key=lambda x: x["score"], reverse=True)

    # Tambem analisar objecoes por modelo individual.
    por_modelo = {}
    for p in ens["personas"]:
        for d in p.get("decisoes_modelos", []):
            modelo = d.get("modelo", "?")
            obj = d.get("objecoes", [])
            por_modelo.setdefault(modelo, []).extend(obj)

    freq_modelo = {
        m: dict(Counter(objs))
        for m, objs in por_modelo.items()
    }

    return {
        "n_personas": n,
        "mapa_objecoes": mapa,
        "frequencia_por_modelo": freq_modelo,
        "top_objecao": mapa[0]["categoria"] if mapa else None,
        "top_objecao_score": mapa[0]["score"] if mapa else 0,
    }


def main():
    parser = argparse.ArgumentParser(description="Mapa de objecoes ponderado")
    parser.add_argument("--ensemble", default="results_v2/ensemble_n30_s42.json")
    parser.add_argument("--output", default="results_v2/mapa_objecoes.json")
    args = parser.parse_args()
    result = analisar_objecoes(args.ensemble)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
