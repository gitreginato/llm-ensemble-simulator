"""Gera relatorio FASE 1: comparativo LLM ensemble vs modelo probabilistico FASE 0.

Le results_v2/ensemble_v5_fast_n128_s42.json e results_v2/mapa_prospeccao.json
e gera results_v2/fase1_relatorio.md + results_v2/fase1_vs_fase0_comparativo.json.
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def load_ensemble(path: str) -> dict:
    return json.loads(Path(path).read_text())


def load_fase0(path: str) -> dict:
    return json.loads(Path(path).read_text())


def analyze_ensemble(data: dict) -> dict:
    """Analisa resultados do ensemble V5."""
    personas = data.get("personas", [])
    n = len(personas)

    # Decisoes do sintetizador.
    synth_decisoes = []
    model_decisoes = []
    source_stats = defaultdict(lambda: {"ok": 0, "fail": 0, "latencies": [], "tokens": []})
    bairro_stats = defaultdict(lambda: {"total": 0, "agendou": 0, "clicou": 0, "visualizou": 0, "ignorou": 0})
    nicho_stats = defaultdict(lambda: {"total": 0, "agendou": 0, "clicou": 0, "visualizou": 0, "ignorou": 0})
    objecoes_counter = Counter()
    divergence_scores = []

    for r in personas:
        p = r["persona"]
        agg = r["decisao_agregada"]
        if agg:
            synth_decisoes.append(agg["decisao_final"])
            divergence_scores.append(agg.get("divergence_score", 0))
            for obj in agg.get("objecoes_consolidadas", []):
                objecoes_counter[obj] += 1
            bairro_stats[p["bairro"]]["total"] += 1
            bairro_stats[p["bairro"]][agg["decisao_final"]] += 1
            nicho_stats[p["segment"]]["total"] += 1
            nicho_stats[p["segment"]][agg["decisao_final"]] += 1

        for dm in r["decisoes_modelos"]:
            model_decisoes.append(dm["decisao"])

        for m in r["metadados_modelos"]:
            s = m.get("source", "unknown")
            if "erro" in m:
                source_stats[s]["fail"] += 1
            else:
                source_stats[s]["ok"] += 1
                if m.get("latency_ms"):
                    source_stats[s]["latencies"].append(m["latency_ms"])
                if m.get("total_tokens"):
                    source_stats[s]["tokens"].append(m["total_tokens"])

    # Taxa de conversao.
    agendaram = sum(1 for d in synth_decisoes if d == "agendou")
    taxa_conversao = agendaram / len(synth_decisoes) if synth_decisoes else 0

    # Divergence score medio.
    div_medio = sum(divergence_scores) / len(divergence_scores) if divergence_scores else 0

    # Distribuicao de decisoes.
    dist_synth = Counter(synth_decisoes)
    dist_models = Counter(model_decisoes)

    return {
        "n_personas": n,
        "n_sinteses_ok": len(synth_decisoes),
        "taxa_conversao": taxa_conversao,
        "agendaram": agendaram,
        "divergence_score_medio": div_medio,
        "dist_sintetizador": dict(dist_synth),
        "dist_modelos": dict(dist_models),
        "objecoes_consolidadas": dict(objecoes_counter.most_common()),
        "source_stats": {s: {
            "ok": v["ok"], "fail": v["fail"],
            "avg_latency_ms": sum(v["latencies"]) / len(v["latencies"]) if v["latencies"] else 0,
            "avg_tokens": sum(v["tokens"]) / len(v["tokens"]) if v["tokens"] else 0,
        } for s, v in source_stats.items()},
        "bairro_stats": dict(bairro_stats),
        "nicho_stats": dict(nicho_stats),
    }


def generate_report(ensemble_data: dict, analysis: dict, fase0_map: list | None = None) -> str:
    """Gera relatorio markdown."""
    lines = []
    lines.append("# Relatorio FASE 1: Ensemble LLM vs Modelo Probabilistico FASE 0\n")
    lines.append(f"Cenario: {ensemble_data.get('cenario', 'N/A')}\n")
    lines.append(f"N: {analysis['n_personas']} personas\n")
    lines.append(f"Sinteses OK: {analysis['n_sinteses_ok']}\n")
    lines.append(f"Custo: ${ensemble_data.get('custo_total_usd', 0):.4f}\n\n")

    lines.append("## Resultados Gerais\n")
    lines.append(f"- Taxa de conversao (sintetizador): {analysis['taxa_conversao']:.1%}\n")
    lines.append(f"- Agendaram: {analysis['agendaram']}/{analysis['n_sinteses_ok']}\n")
    lines.append(f"- Divergence score medio: {analysis['divergence_score_medio']:.3f}\n\n")

    lines.append("## Distribuicao de Decisoes\n")
    lines.append("### Sintetizador\n")
    for dec, count in sorted(analysis["dist_sintetizador"].items(), key=lambda x: -x[1]):
        pct = count / analysis["n_sinteses_ok"] * 100 if analysis["n_sinteses_ok"] else 0
        lines.append(f"- {dec}: {count} ({pct:.1f}%)\n")
    lines.append("\n### Modelos individuais\n")
    total_models = sum(analysis["dist_modelos"].values())
    for dec, count in sorted(analysis["dist_modelos"].items(), key=lambda x: -x[1]):
        pct = count / total_models * 100 if total_models else 0
        lines.append(f"- {dec}: {count} ({pct:.1f}%)\n")
    lines.append("\n")

    lines.append("## Objecoes Consolidadas\n")
    for obj, count in analysis["objecoes_consolidadas"].items():
        lines.append(f"- {obj}: {count}\n")
    lines.append("\n")

    lines.append("## Por Source\n")
    lines.append("| Source | OK | Fail | Avg Latency | Avg Tokens |\n")
    lines.append("|---|---|---|---|---|\n")
    for s, stats in sorted(analysis["source_stats"].items()):
        lines.append(f"| {s} | {stats['ok']} | {stats['fail']} | {stats['avg_latency_ms']:.0f}ms | {stats['avg_tokens']:.0f} |\n")
    lines.append("\n")

    lines.append("## Por Bairro\n")
    lines.append("| Bairro | Total | Agendou | Clicou | Visualizou | Ignorou | Conv % |\n")
    lines.append("|---|---|---|---|---|---|---|\n")
    for b, stats in sorted(analysis["bairro_stats"].items(), key=lambda x: -x[1]["total"]):
        conv = stats["agendou"] / stats["total"] * 100 if stats["total"] else 0
        lines.append(f"| {b} | {stats['total']} | {stats['agendou']} | {stats['clicou']} | {stats['visualizou']} | {stats['ignorou']} | {conv:.1f}% |\n")
    lines.append("\n")

    lines.append("## Por Nicho\n")
    lines.append("| Nicho | Total | Agendou | Clicou | Visualizou | Ignorou | Conv % |\n")
    lines.append("|---|---|---|---|---|---|---|\n")
    for n, stats in sorted(analysis["nicho_stats"].items(), key=lambda x: -x[1]["total"]):
        conv = stats["agendou"] / stats["total"] * 100 if stats["total"] else 0
        lines.append(f"| {n} | {stats['total']} | {stats['agendou']} | {stats['clicou']} | {stats['visualizou']} | {stats['ignorou']} | {conv:.1f}% |\n")
    lines.append("\n")

    if fase0_map:
        lines.append("## Comparativo FASE 0 vs FASE 1\n")
        lines.append("FASE 0 (modelo probabilistico): conversao ~16%, 275 combos bairro x nicho\n")
        lines.append(f"FASE 1 (ensemble LLM): conversao {analysis['taxa_conversao']:.1%}, {analysis['n_sinteses_ok']} personas\n\n")
        lines.append("Top 8 combos FASE 0 (mapa de prospeccao):\n")
        for item in fase0_map[:8]:
            lines.append(f"- {item['bairro']}/{item['nicho']}: conv={item['conversao']:.1%} pot={item['potencial_agendamentos']}\n")

    return "".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ensemble", default="results_v2/ensemble_v5_fast_n128_s42.json")
    parser.add_argument("--fase0", default="results_v2/mapa_prospeccao.json")
    parser.add_argument("--output", default="results_v2/fase1_relatorio.md")
    args = parser.parse_args()

    ensemble_data = load_ensemble(args.ensemble)
    analysis = analyze_ensemble(ensemble_data)

    fase0_map = None
    try:
        fase0_data = load_fase0(args.fase0)
        fase0_map = fase0_data if isinstance(fase0_data, list) else fase0_data.get("mapa", [])
    except FileNotFoundError:
        print(f"Aviso: {args.fase0} nao encontrado, comparativo FASE 0 omitido")

    report = generate_report(ensemble_data, analysis, fase0_map)
    Path(args.output).write_text(report)
    print(f"Relatorio salvo em {args.output}")

    # Salvar analise em JSON.
    json_path = args.output.replace(".md", "_stats.json")
    Path(json_path).write_text(json.dumps(analysis, ensure_ascii=False, indent=2, default=str))
    print(f"Stats salvas em {json_path}")


if __name__ == "__main__":
    main()
