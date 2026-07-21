"""Dashboard de observabilidade da simulacao.

Le results_v2/*.json e gera dashboard.html com:
- Tokens por modelo (bar chart em SVG puro, sem deps)
- Latencia por modelo (bar chart)
- Custo por modelo (bar chart)
- Status HTTP por modelo (stacked bar)
- Provider reliability (% de 200 vs falhas)
- Resumo do run (conversao, IC95, divergence, custo total)

Ponytail: SVG puro gerado por string formatting. Sem plotly, sem matplotlib,
sem JS externo. HTML estatico abre em qualquer navegador.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_results(results_dir: str) -> list[dict]:
    """Carrega todos os results_v2/*.json."""
    results = []
    for p in sorted(Path(results_dir).glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if "personas" in data:  # ensemble output
                data["_filename"] = p.name
                results.append(data)
        except Exception:
            continue
    return results


def aggregate_metrics(results: list[dict]) -> dict:
    """Agrega metricas por modelo e por source de todos os runs."""
    by_model: dict[str, dict] = {}
    by_source: dict[str, dict] = {}
    for run in results:
        for persona in run.get("personas", []):
            for m in persona.get("metadados_modelos", []):
                model = m.get("modelo", "?")
                source = m.get("source", "?")
                is_ok = "erro" not in m
                # Por modelo
                if model not in by_model:
                    by_model[model] = {
                        "source": source,
                        "total": 0, "ok": 0, "fail": 0,
                        "latencies": [], "tokens": [], "costs": [],
                    }
                by_model[model]["total"] += 1
                if is_ok:
                    by_model[model]["ok"] += 1
                    if m.get("latency_ms") is not None:
                        by_model[model]["latencies"].append(m["latency_ms"])
                    if m.get("total_tokens") is not None:
                        by_model[model]["tokens"].append(m["total_tokens"])
                    if m.get("cost_usd") is not None:
                        by_model[model]["costs"].append(m["cost_usd"])
                else:
                    by_model[model]["fail"] += 1
                # Por source
                if source not in by_source:
                    by_source[source] = {"total": 0, "ok": 0, "fail": 0}
                by_source[source]["total"] += 1
                if is_ok:
                    by_source[source]["ok"] += 1
                else:
                    by_source[source]["fail"] += 1
    return {"by_model": by_model, "by_source": by_source}


def svg_bar_chart(
    title: str, data: list[tuple[str, float]], color: str, unit: str = ""
) -> str:
    """Gera 1 bar chart em SVG puro. data = [(label, value), ...]."""
    if not data:
        return f'<h3>{title}</h3><p>Sem dados</p>'
    max_val = max(v for _, v in data) or 1.0
    bar_h = 22
    label_w = 250
    chart_w = 500
    h = len(data) * (bar_h + 4) + 40
    svg = f'<svg width="{label_w + chart_w + 100}" height="{h}" xmlns="http://www.w3.org/2000/svg">'
    svg += f'<text x="10" y="20" font-size="14" font-weight="bold">{title}</text>'
    for i, (label, val) in enumerate(sorted(data, key=lambda x: -x[1])):
        y = 30 + i * (bar_h + 4)
        bar_w = int((val / max_val) * chart_w) if max_val > 0 else 0
        svg += f'<text x="10" y="{y + 15}" font-size="11" font-family="monospace">{label[:35]}</text>'
        svg += f'<rect x="{label_w}" y="{y}" width="{bar_w}" height="{bar_h}" fill="{color}" rx="2"/>'
        val_str = f"{val:.4f}{unit}" if val < 1 else f"{val:.1f}{unit}"
        svg += f'<text x="{label_w + bar_w + 5}" y="{y + 15}" font-size="11">{val_str}</text>'
    svg += '</svg>'
    return svg


def svg_stacked_bar(
    title: str, data: list[tuple[str, int, int]], color_ok: str, color_fail: str
) -> str:
    """Gira stacked bar chart (OK vs FAIL). data = [(label, ok_count, fail_count), ...]."""
    if not data:
        return f'<h3>{title}</h3><p>Sem dados</p>'
    max_total = max(o + f for _, o, f in data) or 1
    bar_h = 22
    label_w = 250
    chart_w = 500
    h = len(data) * (bar_h + 4) + 40
    svg = f'<svg width="{label_w + chart_w + 100}" height="{h}" xmlns="http://www.w3.org/2000/svg">'
    svg += f'<text x="10" y="20" font-size="14" font-weight="bold">{title}</text>'
    for i, (label, ok, fail) in enumerate(sorted(data, key=lambda x: -(x[1] + x[2]))):
        y = 30 + i * (bar_h + 4)
        ok_w = int((ok / max_total) * chart_w) if max_total > 0 else 0
        fail_w = int((fail / max_total) * chart_w) if max_total > 0 else 0
        svg += f'<text x="10" y="{y + 15}" font-size="11" font-family="monospace">{label[:35]}</text>'
        svg += f'<rect x="{label_w}" y="{y}" width="{ok_w}" height="{bar_h}" fill="{color_ok}" rx="2"/>'
        svg += f'<rect x="{label_w + ok_w}" y="{y}" width="{fail_w}" height="{bar_h}" fill="{color_fail}" rx="2"/>'
        pct = (ok / (ok + fail) * 100) if (ok + fail) > 0 else 0
        svg += f'<text x="{label_w + ok_w + fail_w + 5}" y="{y + 15}" font-size="11">{ok}/{ok + fail} ({pct:.0f}%)</text>'
    svg += '</svg>'
    return svg


def generate_html(results: list[dict], metrics: dict, output_path: str) -> None:
    """Gera dashboard.html completo."""
    # Resumo dos runs
    runs_summary = []
    for run in results:
        runs_summary.append({
            "file": run.get("_filename", "?"),
            "n": run.get("n", 0),
            "conversao": run.get("taxa_conversao", 0),
            "ic95": run.get("ic95", [0, 0]),
            "divergence": run.get("divergence_score_medio", 0),
            "custo_total": run.get("custo_total_usd", 0),
            "falhas": run.get("falhas", 0),
        })

    # Dados para graficos
    by_model = metrics["by_model"]
    tokens_data = [(m, sum(d["tokens"]) / len(d["tokens"]) if d["tokens"] else 0) for m, d in by_model.items()]
    latency_data = [(m, sum(d["latencies"]) / len(d["latencies"]) if d["latencies"] else 0) for m, d in by_model.items()]
    cost_data = [(m, sum(d["costs"])) for m, d in by_model.items()]
    status_data = [(m, d["ok"], d["fail"]) for m, d in by_model.items()]

    by_source = metrics["by_source"]
    source_status = [(s, d["ok"], d["fail"]) for s, d in by_source.items()]

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Dashboard Observabilidade - Simulation Army</title>
<style>
body {{ font-family: monospace; margin: 20px; background: #f5f5f5; }}
h1 {{ color: #333; }}
h2 {{ color: #555; margin-top: 30px; }}
.chart {{ background: white; padding: 15px; margin: 10px 0; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
table {{ border-collapse: collapse; width: 100%; background: white; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background: #4CAF50; color: white; }}
tr:nth-child(even) {{ background: #f9f9f9; }}
</style>
</head>
<body>
<h1>Dashboard de Observabilidade - Simulation Army</h1>
<p>Gerado de {len(results)} run(s) em results_v2/</p>

<h2>Resumo dos Runs</h2>
<table>
<tr><th>Arquivo</th><th>N</th><th>Conversao</th><th>IC95</th><th>Divergence</th><th>Custo USD</th><th>Falhas</th></tr>
"""
    for r in runs_summary:
        html += f"""<tr><td>{r['file']}</td><td>{r['n']}</td><td>{r['conversao']:.1%}</td>
<td>[{r['ic95'][0]:.1%}, {r['ic95'][1]:.1%}]</td><td>{r['divergence']:.2f}</td>
<td>${r['custo_total']:.4f}</td><td>{r['falhas']}</td></tr>
"""
    html += "</table>"

    html += '<h2>Metricas por Modelo</h2>'
    html += f'<div class="chart">{svg_bar_chart("Tokens medios por modelo", tokens_data, "#2196F3", "")}</div>'
    html += f'<div class="chart">{svg_bar_chart("Latencia media por modelo (ms)", latency_data, "#FF9800", "ms")}</div>'
    html += f'<div class="chart">{svg_bar_chart("Custo total por modelo (USD)", cost_data, "#4CAF50", "$")}</div>'
    html += f'<div class="chart">{svg_stacked_bar("Status: OK (verde) vs FAIL (vermelho)", status_data, "#4CAF50", "#F44336")}</div>'

    html += '<h2>Confiabilidade por Source</h2>'
    html += f'<div class="chart">{svg_stacked_bar("OK vs FAIL por source", source_status, "#4CAF50", "#F44336")}</div>'

    html += '<h2>Tabela Detalhada por Modelo</h2><table>'
    html += '<tr><th>Modelo</th><th>Source</th><th>Total</th><th>OK</th><th>FAIL</th><th>Reliability</th><th>Latencia avg (ms)</th><th>Tokens avg</th><th>Custo total ($)</th></tr>'
    for model, d in sorted(by_model.items(), key=lambda x: -x[1]["total"]):
        rel = (d["ok"] / d["total"] * 100) if d["total"] > 0 else 0
        lat_avg = (sum(d["latencies"]) / len(d["latencies"])) if d["latencies"] else 0
        tok_avg = (sum(d["tokens"]) / len(d["tokens"])) if d["tokens"] else 0
        cost_sum = sum(d["costs"])
        html += f"""<tr><td>{model}</td><td>{d['source']}</td><td>{d['total']}</td><td>{d['ok']}</td>
<td>{d['fail']}</td><td>{rel:.0f}%</td><td>{lat_avg:.0f}</td><td>{tok_avg:.0f}</td><td>${cost_sum:.4f}</td></tr>
"""
    html += "</table></body></html>"

    Path(output_path).write_text(html, encoding="utf-8")
    print(f"Dashboard gerado: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Dashboard de observabilidade")
    parser.add_argument("--results", default="results_v2", help="diretorio com results_v2/*.json")
    parser.add_argument("--output", default="dashboard.html", help="arquivo HTML de saida")
    args = parser.parse_args()
    results = load_results(args.results)
    if not results:
        print(f"Nenhum result encontrado em {args.results}/")
        return
    metrics = aggregate_metrics(results)
    generate_html(results, metrics, args.output)


if __name__ == "__main__":
    main()
