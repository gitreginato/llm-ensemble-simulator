"""Consolida todos os resultados existentes em um dataset unico para calibrar o modelo.

Fontes: results_v2/*.json (ensemble + nicho_analysis)
Output: results_v2/dataset_real.json + results_v2/dataset_real.csv
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results_v2"


def extract_personas():
    personas = []
    for f in sorted(RESULTS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        if "detalhes" in data:
            # nicho_analysis.json
            for nicho, results in data["detalhes"].items():
                for r in results:
                    if r.get("decisao") == "erro":
                        continue
                    personas.append({
                        "source_file": f.name,
                        "source_type": "nicho_baseline",
                        "model": data.get("model", "?"),
                        "nome": r.get("nome", "?"),
                        "segment": r.get("segment", nicho),
                        "risk_profile": r.get("risk_profile", "?"),
                        "recent_event": r.get("recent_event", "?"),
                        "has_existing_security": r.get("has_existing_security", "?"),
                        "wtp_brl": r.get("wtp_brl", r.get("wtp", 0)),
                        "decisao": r.get("decisao", "?"),
                        "objecoes": r.get("objecoes", []),
                        "sentimento": r.get("sentimento", 0),
                        "confianca": r.get("confianca", 0),
                        "bairro": "unknown",
                    })
        elif "personas" in data:
            # ensemble runs
            for p in data["personas"]:
                synth = p.get("decisao_agregada") or {}
                persona = p.get("persona", {})
                if not synth or not persona:
                    continue
                personas.append({
                    "source_file": f.name,
                    "source_type": "ensemble",
                    "model": data.get("sintetizador", "?"),
                    "nome": persona.get("owner_name", "?"),
                    "segment": persona.get("segment", "?"),
                    "risk_profile": persona.get("risk_profile", "?"),
                    "recent_event": persona.get("recent_event", "?"),
                    "has_existing_security": persona.get("has_existing_security", "?"),
                    "wtp_brl": persona.get("wtp_brl", 0),
                    "decisao": synth.get("decisao_final", "?"),
                    "objecoes": synth.get("objecoes_consolidadas", []),
                    "sentimento": synth.get("sentimento_medio", 0),
                    "confianca": synth.get("confianca_agregada", 0),
                    "bairro": persona.get("bairro", "unknown"),
                })
    return personas


def compute_stats(personas):
    stats = {}
    # Total
    stats["total"] = len(personas)
    stats["por_source"] = dict(defaultdict(int, (
        (s, sum(1 for p in personas if p["source_type"] == s))
        for s in set(p["source_type"] for p in personas)
    )))

    # Cross-tabs
    for feature in ["recent_event", "has_existing_security", "risk_profile", "segment"]:
        ct = defaultdict(lambda: defaultdict(int))
        for p in personas:
            ct[p[feature]][p["decisao"]] += 1
        stats[f"crosstab_{feature}"] = {
            k: dict(v) for k, v in ct.items()
        }

    # WTP por decisao
    by_dec = defaultdict(list)
    for p in personas:
        if p["wtp_brl"] > 0:
            by_dec[p["decisao"]].append(p["wtp_brl"])
    stats["wtp_por_decisao"] = {}
    for dec, wtps in by_dec.items():
        import statistics
        stats["wtp_por_decisao"][dec] = {
            "n": len(wtps),
            "mediana": statistics.median(wtps),
            "media": statistics.mean(wtps),
            "min": min(wtps),
            "max": max(wtps),
        }

    # Budget vs mensalidade
    pode = sum(1 for p in personas if p["wtp_brl"] >= 294)
    nao_pode = sum(1 for p in personas if 0 < p["wtp_brl"] < 294)
    stats["budget_vs_mensalidade_294"] = {
        "pode_pagar": pode,
        "nao_pode_pagar": nao_pode,
        "pct_pode": pode / (pode + nao_pode) if (pode + nao_pode) > 0 else 0,
    }

    # Objeções
    by_obj = defaultdict(int)
    for p in personas:
        for o in p["objecoes"]:
            by_obj[o] += 1
    stats["objecoes"] = dict(by_obj)

    return stats


def main():
    personas = extract_personas()
    print(f"Extraidas {len(personas)} personas de {len(set(p['source_file'] for p in personas))} arquivos")

    stats = compute_stats(personas)

    # JSON
    output_json = RESULTS_DIR / "dataset_real.json"
    output_json.write_text(
        json.dumps({"personas": personas, "stats": stats}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"JSON: {output_json}")

    # CSV
    output_csv = RESULTS_DIR / "dataset_real.csv"
    fields = ["source_type", "model", "nome", "segment", "risk_profile",
              "recent_event", "has_existing_security", "wtp_brl", "decisao",
              "objecoes", "sentimento", "confianca", "bairro"]
    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for p in personas:
            row = {k: p.get(k, "") for k in fields}
            row["objecoes"] = "|".join(p.get("objecoes", []))
            writer.writerow(row)
    print(f"CSV: {output_csv}")

    # Resumo
    print(f"\n=== RESUMO ===")
    print(f"Total: {stats['total']}")
    print(f"Por source: {stats['por_source']}")
    print(f"Pode pagar R$ 294: {stats['budget_vs_mensalidade_294']['pct_pode']:.0%}")
    print(f"\nCrosstab recent_event x decisao:")
    for event, decs in sorted(stats["crosstab_recent_event"].items()):
        total = sum(decs.values())
        conv = decs.get("agendou", 0) / total if total > 0 else 0
        print(f"  {event}: {decs} conv={conv:.0%}")
    print(f"\nCrosstab has_existing_security x decisao:")
    for sec, decs in sorted(stats["crosstab_has_existing_security"].items()):
        total = sum(decs.values())
        conv = decs.get("agendou", 0) / total if total > 0 else 0
        print(f"  {sec}: {decs} conv={conv:.0%}")
    print(f"\nCrosstab risk_profile x decisao:")
    for risk, decs in sorted(stats["crosstab_risk_profile"].items()):
        total = sum(decs.values())
        conv = decs.get("agendou", 0) / total if total > 0 else 0
        print(f"  {risk}: {decs} conv={conv:.0%}")
    print(f"\nCrosstab segment x decisao:")
    for seg, decs in sorted(stats["crosstab_segment"].items()):
        total = sum(decs.values())
        conv = decs.get("agendou", 0) / total if total > 0 else 0
        print(f"  {seg}: {decs} conv={conv:.0%}")


if __name__ == "__main__":
    main()
