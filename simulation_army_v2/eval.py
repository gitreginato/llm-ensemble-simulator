"""Eval do Simulation Army v2: 3 checks com score 0..1.

1. CALIBRACAO: mediana da taxa de conversao em [2%, 8%]
2. DIVERSIDADE: pairwise_disagreement_rate > 0.3 E p < 0.05
3. COERENCIA: >= 90% com confianca_agregada >= 0.6 E raciocinio nao-vazio

Score = media dos 3 checks. Aceitar >= 0.8.
"""
import json
import os
from pathlib import Path

RESULTS_DIR = Path(__file__).parent.parent / "results_v2"


def _load_json(path):
    if not Path(path).exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_calibracao(ensemble_data, benchmark_lo=0.02, benchmark_hi=0.08):
    """Check 1: mediana da taxa de conversao em [2%, 8%]."""
    if not ensemble_data:
        return {"pass": False, "score": 0.0, "detail": "ensemble data missing"}
    conv = ensemble_data.get("taxa_conversao", 0)
    # Para N=30, mediana ~= taxa. Usar a taxa diretamente.
    in_range = benchmark_lo <= conv <= benchmark_hi
    # Score parcial: quao proximo do range.
    if in_range:
        score = 1.0
    elif conv < benchmark_lo:
        score = max(0.0, conv / benchmark_lo)
    else:
        score = max(0.0, benchmark_hi / conv)
    return {
        "pass": in_range,
        "score": round(score, 3),
        "detail": f"conversao={conv:.1%} benchmark=[{benchmark_lo:.0%}, {benchmark_hi:.0%}]",
    }


def check_diversidade(metricas_data, pdr_threshold=0.3, p_threshold=0.05):
    """Check 2: pairwise_disagreement_rate > 0.3 E p < 0.05."""
    if not metricas_data:
        return {"pass": False, "score": 0.0, "detail": "metricas data missing"}
    pdr = metricas_data.get("pairwise_disagreement_rate", 0)
    p = metricas_data.get("teste_permutacao_p_valor", 1.0)
    pdr_ok = pdr > pdr_threshold
    p_ok = p < p_threshold
    passed = pdr_ok and p_ok
    score = (0.5 if pdr_ok else 0.0) + (0.5 if p_ok else 0.0)
    return {
        "pass": passed,
        "score": round(score, 3),
        "detail": f"pairwise={pdr:.2f} (>{pdr_threshold}) p={p:.3f} (<{p_threshold})",
    }


def check_coerencia(ensemble_data, min_confianca=0.6, min_pct=0.9):
    """Check 3: >= 90% com confianca >= 0.6 E raciocinio nao-vazio."""
    if not ensemble_data:
        return {"pass": False, "score": 0.0, "detail": "ensemble data missing"}
    agregadas = [
        p["decisao_agregada"]
        for p in ensemble_data.get("personas", [])
        if p.get("decisao_agregada")
    ]
    if not agregadas:
        return {"pass": False, "score": 0.0, "detail": "nenhuma decisao agregada"}
    coerentes = sum(
        1
        for a in agregadas
        if a.get("confianca_agregada", 0) >= min_confianca
        and a.get("raciocinio_sintese", "").strip()
    )
    pct = coerentes / len(agregadas)
    passed = pct >= min_pct
    return {
        "pass": passed,
        "score": round(min(1.0, pct / min_pct), 3) if not passed else 1.0,
        "detail": f"coerentes={coerentes}/{len(agregadas)} ({pct:.1%}) min={min_pct:.0%}",
    }


def run_eval(ensemble_path=None, metricas_path=None):
    """Roda os 3 checks e retorna score 0..1."""
    if ensemble_path is None:
        ensemble_path = RESULTS_DIR / "ensemble_n30_s42.json"
    if metricas_path is None:
        metricas_path = RESULTS_DIR / "metricas_diversidade.json"

    ens = _load_json(ensemble_path)
    met = _load_json(metricas_path)

    c1 = check_calibracao(ens)
    c2 = check_diversidade(met)
    c3 = check_coerencia(ens)

    score = (c1["score"] + c2["score"] + c3["score"]) / 3
    passed = score >= 0.8

    return {
        "score": round(score, 3),
        "passed": passed,
        "threshold": 0.8,
        "checks": {
            "calibracao": c1,
            "diversidade": c2,
            "coerencia": c3,
        },
    }


if __name__ == "__main__":
    result = run_eval()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    exit(0 if result["passed"] else 1)
