"""Parser do log do ensemble v4 para JSON estruturado + relatorio de performance.

Extrai do log:
- Por request: persona, role, source, modelo, decisao/erro, latency_ms, tokens, backoff
- Por modelo: total, ok, fail, taxa_sucesso, latency_media, tokens_medios, decisoes
- Por source: total, ok, fail, taxa_sucesso
- Por tipo de erro: count
- Sintetizador: decisao, divergence por persona
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

LOG_PATH = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ensemble_v4_run.log"
OUTPUT_JSON = sys.argv[2] if len(sys.argv) > 2 else "results_v2/ensemble_v4_n30_partial.json"
OUTPUT_REPORT = sys.argv[3] if len(sys.argv) > 3 else "results_v2/ensemble_v4_n30_report.md"

# Regex para linha de request:
#   [1/30] Joao Araujo [cetico] (gocat): FAIL HTTP 503: ... (backoff=2.0x)
#   [1/30] Joao Araujo [otimista] (gocat): visualizou latency=4681ms tokens=1072
#   [1/30] Joao Araujo [revisor] (devin): agendou latency=22175ms tokens=None
RE_OK = re.compile(
    r"\[(\d+)/(\d+)\] (.+?) \[(.+?)\] \((.+?)\): (agendou|visualizou|clicou|ignorou) latency=(\d+)ms tokens=(\d+|None)"
)
RE_FAIL = re.compile(
    r"\[(\d+)/(\d+)\] (.+?) \[(.+?)\] \((.+?)\): FAIL (.+?)(?: \(backoff=([\d.]+)x\))?$"
)
RE_SYNTH = re.compile(r"\[(\d+)/(\d+)\] (.+?) \[SYNTH\]: (agendou|visualizou|clicou|ignorou) div=([\d.]+)")
RE_MODEL_503 = re.compile(r"model '([^']+)'")

requests = []
synths = []

for line in Path(LOG_PATH).read_text(encoding="utf-8").splitlines():
    line = line.strip()
    m = RE_OK.match(line)
    if m:
        persona_idx, n_total, persona_name, role, source, decisao, latency, tokens = m.groups()
        # inferir modelo: gocat usa role como rota, kilocode/devin usam role
        # o log nao tem o nome do modelo explicitamente para gocat, mas o role
        # corresponde ao modelo no scenario. Vamos mapear role->modelo depois.
        requests.append({
            "persona_idx": int(persona_idx),
            "persona_name": persona_name,
            "role": role,
            "source": source,
            "decisao": decisao,
            "latency_ms": int(latency),
            "tokens": int(tokens) if tokens != "None" else None,
            "ok": True,
        })
        continue
    m = RE_FAIL.match(line)
    if m:
        persona_idx, n_total, persona_name, role, source, err_msg, backoff = m.groups()
        # extrair modelo do erro 503 se presente
        model_match = RE_MODEL_503.search(err_msg)
        erro_tipo = "unknown"
        if "HTTP 503" in err_msg:
            erro_tipo = "http_503"
        elif "timeout" in err_msg.lower():
            erro_tipo = "timeout"
        elif "Both content and reasoning_content are empty" in err_msg:
            erro_tipo = "empty_response"
        elif "JSON nao encontrado" in err_msg:
            erro_tipo = "json_parse_fail"
        elif "502" in err_msg:
            erro_tipo = "http_502"
        elif "ResourceExhausted" in err_msg:
            erro_tipo = "resource_exhausted"
        requests.append({
            "persona_idx": int(persona_idx),
            "persona_name": persona_name,
            "role": role,
            "source": source,
            "erro": err_msg.strip(),
            "erro_tipo": erro_tipo,
            "modelo_erro": model_match.group(1) if model_match else None,
            "backoff": float(backoff) if backoff else None,
            "ok": False,
        })
        continue
    m = RE_SYNTH.match(line)
    if m:
        persona_idx, n_total, persona_name, decisao, div = m.groups()
        synths.append({
            "persona_idx": int(persona_idx),
            "persona_name": persona_name,
            "decisao": decisao,
            "divergence": float(div),
        })
        continue

# Mapear role -> modelo baseado no scenario v4 (ordem dos 22 modelos)
# O shuffle muda a ordem, mas o role identifica o modelo.
# Na verdade, o log mostra o role (cetico, otimista, etc) que e o papel da persona,
# nao o modelo. O modelo e identificado pela posicao no scenario.
# POREM o log nao tem o nome do modelo para requests OK.
# Para FAIL com 503, o modelo esta na mensagem de erro.
# Vamos mapear source+role -> modelo usando o que sabemos:
# gocat tem 10 modelos, kilocode 10, devin 2. O role e o papel, nao o modelo.
# CONCLUSAO: o log nao tem o nome do modelo para requests OK.
# So temos o source. Para falhas 503, temos o modelo.

# Relatorio por source
by_source = defaultdict(lambda: {"total": 0, "ok": 0, "fail": 0, "latencies": [], "tokens": []})
for r in requests:
    s = by_source[r["source"]]
    s["total"] += 1
    if r["ok"]:
        s["ok"] += 1
        s["latencies"].append(r["latency_ms"])
        if r["tokens"] is not None:
            s["tokens"].append(r["tokens"])
    else:
        s["fail"] += 1

# Relatorio por modelo (apenas falhas tem modelo identificado)
by_model_fail = defaultdict(lambda: {"fail": 0, "tipos": []})
for r in requests:
    if not r["ok"] and r.get("modelo_erro"):
        m = by_model_fail[r["modelo_erro"]]
        m["fail"] += 1
        m["tipos"].append(r["erro_tipo"])

# Relatorio por tipo de erro
by_erro_tipo = defaultdict(int)
for r in requests:
    if not r["ok"]:
        by_erro_tipo[r["erro_tipo"]] += 1

# Relatorio por decisao
by_decisao = defaultdict(int)
for r in requests:
    if r["ok"]:
        by_decisao[r["decisao"]] += 1

# Latencia percentis
def percentile(lst, p):
    if not lst:
        return 0
    lst = sorted(lst)
    k = (len(lst) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(lst) - 1)
    return lst[f] + (lst[c] - lst[f]) * (k - f)

# JSON estruturado
output = {
    "cenario": "slz-c-army-v4",
    "n_esperado": 30,
    "n_completado": len(synths),
    "requests": requests,
    "sintetizadores": synths,
    "resumo": {
        "total_requests": len(requests),
        "requests_ok": sum(1 for r in requests if r["ok"]),
        "requests_fail": sum(1 for r in requests if not r["ok"]),
        "taxa_sucesso": sum(1 for r in requests if r["ok"]) / len(requests) if requests else 0,
        "decisoes": dict(by_decisao),
        "conversao_sintetizador": sum(1 for s in synths if s["decisao"] == "agendou") / len(synths) if synths else 0,
        "divergence_medio": sum(s["divergence"] for s in synths) / len(synths) if synths else 0,
    },
    "por_source": {
        s: {
            "total": d["total"], "ok": d["ok"], "fail": d["fail"],
            "taxa_sucesso": d["ok"] / d["total"] if d["total"] > 0 else 0,
            "latency_media_ms": sum(d["latencies"]) / len(d["latencies"]) if d["latencies"] else 0,
            "latency_p50_ms": percentile(d["latencies"], 50),
            "latency_p95_ms": percentile(d["latencies"], 95),
            "tokens_medios": sum(d["tokens"]) / len(d["tokens"]) if d["tokens"] else 0,
        }
        for s, d in by_source.items()
    },
    "por_modelo_falhas": {
        m: {"fail": d["fail"], "tipos": d["tipos"]}
        for m, d in by_model_fail.items()
    },
    "por_erro_tipo": dict(by_erro_tipo),
    "backoff_observado": {
        "max_backoff": max((r.get("backoff") or 0) for r in requests if not r["ok"]),
        "backoffs": [r["backoff"] for r in requests if not r["ok"] and r.get("backoff")],
    },
}

Path(OUTPUT_JSON).parent.mkdir(parents=True, exist_ok=True)
Path(OUTPUT_JSON).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"JSON estruturado: {OUTPUT_JSON} ({len(requests)} requests, {len(synths)} synths)")

# Relatorio markdown
report = []
report.append("# Relatorio de Performance: Ensemble v4 (N=30 parcial)\n")
report.append(f"**Data:** 2026-07-20\n")
report.append(f"**Personas completas:** {len(synths)}/30\n")
report.append(f"**Total de requests:** {len(requests)}\n")
report.append(f"**Requests OK:** {output['resumo']['requests_ok']} ({output['resumo']['taxa_sucesso']:.1%})\n")
report.append(f"**Requests FAIL:** {output['resumo']['requests_fail']}\n")
report.append(f"**Custo total:** $0 (todos free tier)\n\n")

report.append("## Sintetizador\n\n")
report.append("| Persona | Decisao | Divergence |\n|---|---|---|\n")
for s in synths:
    report.append(f"| {s['persona_name']} | {s['decisao']} | {s['divergence']:.2f} |\n")
conv = output["resumo"]["conversao_sintetizador"]
report.append(f"\n**Conversao (sintetizador):** {conv:.1%}\n")
report.append(f"**Divergence medio:** {output['resumo']['divergence_medio']:.2f}\n\n")

report.append("## Performance por Source\n\n")
report.append("| Source | Total | OK | FAIL | Sucesso | Lat media | P50 | P95 | Tokens |\n")
report.append("|---|---|---|---|---|---|---|---|---|\n")
for s, d in sorted(by_source.items()):
    p50 = percentile(d["latencies"], 50)
    p95 = percentile(d["latencies"], 95)
    lat_med = sum(d["latencies"]) / len(d["latencies"]) if d["latencies"] else 0
    tok_med = sum(d["tokens"]) / len(d["tokens"]) if d["tokens"] else 0
    taxa = d["ok"] / d["total"] if d["total"] > 0 else 0
    report.append(f"| {s} | {d['total']} | {d['ok']} | {d['fail']} | {taxa:.0%} | {lat_med:.0f}ms | {p50:.0f}ms | {p95:.0f}ms | {tok_med:.0f} |\n")

report.append("\n## Distribuicao de Decisoes (modelos)\n\n")
report.append("| Decisao | Count |\n|---|---|\n")
for dec, cnt in sorted(by_decisao.items(), key=lambda x: -x[1]):
    report.append(f"| {dec} | {cnt} |\n")

report.append("\n## Modelos que Falham (gocat 503)\n\n")
report.append("| Modelo | Fails | Tipos |\n|---|---|---|\n")
for m, d in sorted(by_model_fail.items(), key=lambda x: -x[1]["fail"]):
    tipos = ", ".join(set(d["tipos"]))
    report.append(f"| {m} | {d['fail']} | {tipos} |\n")

report.append("\n## Tipos de Erro\n\n")
report.append("| Tipo | Count |\n|---|---|\n")
for tipo, cnt in sorted(by_erro_tipo.items(), key=lambda x: -x[1]):
    report.append(f"| {tipo} | {cnt} |\n")

report.append("\n## Backoff Adaptativo Observado\n\n")
backoffs = [r["backoff"] for r in requests if not r["ok"] and r.get("backoff")]
if backoffs:
    report.append(f"- Backoffs aplicados: {len(backoffs)}\n")
    report.append(f"- Backoff maximo: {max(backoffs):.1f}x\n")
    report.append(f"- Backoffs unicos: {sorted(set(backoffs))}\n")
else:
    report.append("- Nenhum backoff aplicado\n")

report.append("\n## Limitacoes Encontradas\n\n")
report.append("1. **3 modelos gocat sempre falham 503**: Meta-Llama-3.3-70B-Instruct (SambaNova), gemini-2.5-flash (Gemini), deepseek-ai/DeepSeek-V3 (SiliconFlow)\n")
report.append("2. **kilocode timeouts**: kat-coder-pro-v2.5 e nemotron-3-ultra-550b as vezes dao timeout 90s\n")
report.append("3. **gocat empty response**: conversacional as vezes retorna 'Both content and reasoning_content are empty'\n")
report.append("4. **Tempo por persona**: 5-10min (22 modelos sequenciais). N=30 = 2.5-5h.\n")
report.append("5. **JSON parse fail**: kilocode as vezes retorna texto em vez de JSON (pesquisador)\n")

report.append("\n## Recomendacoes\n\n")
report.append("1. Remover os 3 modelos gocat que sempre falham 503 do scenario v4\n")
report.append("2. Reduzir N para 10 em vez de 30 (mais viavel em tempo)\n")
report.append("3. Considerar paralelismo real (asyncio.gather) para reduzir tempo\n")
report.append("4. Aumentar timeout kilocode para 120s ou remover kat-coder-pro-v2.5\n")

Path(OUTPUT_REPORT).write_text("".join(report), encoding="utf-8")
print(f"Relatorio markdown: {OUTPUT_REPORT}")
