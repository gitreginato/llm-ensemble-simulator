"""Escala modular: multi-seed + bootstrap 10000 + power analysis.

Modular: cada seed roda independentemente e acumula em results_v2/.
Bootstrap nao precisa de API calls, apenas resampling dos dados existentes.
Power analysis: calcular poder estatistico para detectar diferenca observada.

Uso:
    python -m simulation_army_v2.scale --seeds 42 123 456 --n 30
    python -m simulation_army_v2.scale --bootstrap-only  # usa dados existentes
"""
import argparse
import asyncio
import json
import os
from pathlib import Path

import numpy as np

RESULTS_DIR = Path(__file__).parent.parent / "results_v2"


def bootstrap_ic95(data: list, n_resamples: int = 10000, confidence: float = 0.95, seed: int = 42) -> dict:
    """Bootstrap IC95% para a media. Mais robusto que beta para N pequeno.

    Retorna: media, ic_lo, ic_hi, n_resamples.
    """
    if not data:
        return {"media": 0.0, "ic_lo": 0.0, "ic_hi": 0.0, "n": 0}
    arr = np.array(data, dtype=float)
    n = len(arr)
    rng = np.random.default_rng(seed)
    means = np.array([
        np.mean(rng.choice(arr, size=n, replace=True))
        for _ in range(n_resamples)
    ])
    alpha = (1 - confidence) / 2
    lo = float(np.percentile(means, alpha * 100))
    hi = float(np.percentile(means, (1 - alpha) * 100))
    return {
        "media": float(np.mean(arr)),
        "ic_lo": lo,
        "ic_hi": hi,
        "n": n,
        "n_resamples": n_resamples,
    }


def power_analysis(
    taxa_ensemble: float,
    taxa_baseline: float,
    n: int,
    alpha: float = 0.05,
) -> dict:
    """Power analysis: dado N e diferenca observada, qual o poder estatistico?

    Usa normal approximation para proporcoes.
    H0: p_ensemble = p_baseline (nao ha diferenca)
    H1: p_ensemble != p_baseline

    Poder = P(rejeitar H0 | H1 verdadeira)
    """
    from scipy.stats import norm

    p1, p2 = taxa_ensemble, taxa_baseline
    diff = abs(p1 - p2)
    if diff == 0:
        return {"poder": 0.0, "diff": 0.0, "n": n, "nota": "sem diferenca para detectar"}

    # Pooled SE sob H0
    p_pool = (p1 + p2) / 2
    se_h0 = np.sqrt(p_pool * (1 - p_pool) * 2 / n)

    # SE sob H1
    se_h1 = np.sqrt(p1 * (1 - p1) / n + p2 * (1 - p2) / n)

    # Z critico (two-sided)
    z_crit = norm.ppf(1 - alpha / 2)

    # Poder: P(|Z| > z_crit | H1)
    z_effect = diff / se_h1
    poder = float(norm.cdf(-z_crit - z_effect) + (1 - norm.cdf(z_crit - z_effect)))

    # N necessario para 80% power
    z_beta = norm.ppf(0.8)
    n_needed = int(np.ceil(((z_crit + z_beta) * se_h0 / diff) ** 2 * 2))

    return {
        "poder": round(poder, 4),
        "diff_observada": round(diff, 4),
        "n_atual": n,
        "n_necessario_80pct": n_needed,
        "se_h0": round(float(se_h0), 4),
        "se_h1": round(float(se_h1), 4),
    }


def agregar_seeds(seed_paths: list[str]) -> dict:
    """Agrega resultados de multiplas seeds em um dataset unico."""
    all_personas = []
    all_div_scores = []
    all_conversoes = []
    seeds_usadas = []

    for sp in seed_paths:
        if not Path(sp).exists():
            continue
        with open(sp, encoding="utf-8") as f:
            data = json.load(f)
        seeds_usadas.append(data.get("seed", "?"))
        all_personas.extend(data.get("personas", []))
        all_div_scores.extend([
            p["decisao_agregada"]["divergence_score"]
            for p in data.get("personas", [])
            if p.get("decisao_agregada")
        ])
        all_conversoes.append(data.get("taxa_conversao", 0))

    return {
        "seeds": seeds_usadas,
        "n_total": len(all_personas),
        "personas": all_personas,
        "divergence_scores": all_div_scores,
        "conversoes_por_seed": all_conversoes,
    }


def analisar_escala(ensemble_paths: list[str], baseline_paths: list[str]) -> dict:
    """Analisa multi-seed com bootstrap e power analysis."""
    # Agregar ensemble
    ens_agg = agregar_seeds(ensemble_paths)

    # Decisoes finais do ensemble (todas seeds)
    decisoes_finais = [
        p["decisao_agregada"]["decisao_final"]
        for p in ens_agg["personas"]
        if p.get("decisao_agregada")
    ]
    agendaram = sum(1 for d in decisoes_finais if d == "agendou")
    n_total = len(decisoes_finais)
    taxa_ensemble = agendaram / n_total if n_total > 0 else 0

    # Bootstrap IC95% para conversao
    # Cada persona e um Bernoulli (agendou=1, nao=0)
    bernoulli = [1 if d == "agendou" else 0 for d in decisoes_finais]
    boot_conv = bootstrap_ic95(bernoulli, n_resamples=10000)

    # Bootstrap IC95% para divergence_score
    boot_div = bootstrap_ic95(ens_agg["divergence_scores"], n_resamples=10000)

    # Baselines
    baselines = {}
    for bp in baseline_paths:
        if not Path(bp).exists():
            continue
        with open(bp, encoding="utf-8") as f:
            b = json.load(f)
        b_bernoulli = [1 if d["decisao"] == "agendou" else 0 for d in b.get("decisoes", []) if not d.get("_falha")]
        boot_b = bootstrap_ic95(b_bernoulli, n_resamples=10000)
        baselines[b["modelo"]] = {
            "taxa_conversao": b.get("taxa_conversao", 0),
            "bootstrap_ic95": boot_b,
        }

    # Power analysis: ensemble vs cada baseline
    power = {}
    for modelo, b in baselines.items():
        power[modelo] = power_analysis(taxa_ensemble, b["taxa_conversao"], n_total)

    return {
        "n_total": n_total,
        "seeds": ens_agg["seeds"],
        "conversoes_por_seed": ens_agg["conversoes_por_seed"],
        "taxa_conversao_ensemble": taxa_ensemble,
        "bootstrap_conversao": boot_conv,
        "bootstrap_divergence": boot_div,
        "baselines": baselines,
        "power_analysis": power,
        "divergence_score_medio": boot_div["media"],
    }


async def rodar_seed(seed: int, n: int, config_path: str) -> str:
    """Roda uma seed do ensemble e salva resultado."""
    from simulation_army_v2.ensemble import run_ensemble
    output_path = str(RESULTS_DIR / f"ensemble_n{n}_s{seed}.json")
    if Path(output_path).exists():
        print(f"[SCALE] Seed {seed} ja existe, pulando: {output_path}")
        return output_path
    print(f"[SCALE] Rodando seed {seed} com N={n}...")
    await run_ensemble(config_path, n, seed, output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Escala modular: multi-seed + bootstrap + power analysis")
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 123, 456])
    parser.add_argument("--n", type=int, default=30)
    parser.add_argument("--scenario", default="scenarios_v2/slz-c-army.yaml")
    parser.add_argument("--bootstrap-only", action="store_true", help="Apenas bootstrap nos dados existentes")
    parser.add_argument("--output", default="results_v2/escala_analise.json")
    args = parser.parse_args()

    ensemble_paths = [str(RESULTS_DIR / f"ensemble_n{args.n}_s{s}") + ".json" for s in args.seeds]
    baseline_paths = [
        str(RESULTS_DIR / "baseline_gpt-4o-mini_n30_s42.json"),
        str(RESULTS_DIR / "baseline_command-r-plus_n30_s42.json"),
        str(RESULTS_DIR / "baseline_llama-3_3-70b-versatile_n30_s42.json"),
    ]

    if not args.bootstrap_only:
        for s in args.seeds:
            asyncio.run(rodar_seed(s, args.n, args.scenario))

    result = analisar_escala(ensemble_paths, baseline_paths)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
