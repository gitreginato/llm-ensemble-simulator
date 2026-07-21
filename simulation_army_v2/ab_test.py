"""A/B test: pitch tecnico (A) vs pitch financeiro (B).

Roda o ensemble em 2 variantes de scenario e compara conversao com bootstrap IC95%.
Diferenca significativa (IC95% nao sobrepoe) = recomendar vencedor.
"""
import argparse
import asyncio
import json
from pathlib import Path

from simulation_army_v2.ensemble import run_ensemble
from simulation_army_v2.scale import bootstrap_ic95, power_analysis

RESULTS_DIR = Path(__file__).parent.parent / "results_v2"


async def run_ab_test(
    scenario_a: str,
    scenario_b: str,
    n: int = 30,
    seed: int = 42,
) -> dict:
    """Roda ensemble em 2 variantes e compara."""
    out_a = str(RESULTS_DIR / f"ab_test_A_n{n}_s{seed}.json")
    out_b = str(RESULTS_DIR / f"ab_test_B_n{n}_s{seed}.json")

    # Variante A
    if not Path(out_a).exists():
        print(f"[A/B] Rodando variante A (tecnico)...")
        res_a = await run_ensemble(scenario_a, n, seed, out_a)
    else:
        print(f"[A/B] Variante A ja existe: {out_a}")
        with open(out_a, encoding="utf-8") as f:
            res_a = json.load(f)

    # Variante B
    if not Path(out_b).exists():
        print(f"[A/B] Rodando variante B (financeiro)...")
        res_b = await run_ensemble(scenario_b, n, seed, out_b)
    else:
        print(f"[A/B] Variante B ja existe: {out_b}")
        with open(out_b, encoding="utf-8") as f:
            res_b = json.load(f)

    # Comparar com bootstrap
    bernoulli_a = [
        1 if p["decisao_agregada"]["decisao_final"] == "agendou" else 0
        for p in res_a["personas"]
        if p.get("decisao_agregada")
    ]
    bernoulli_b = [
        1 if p["decisao_agregada"]["decisao_final"] == "agendou" else 0
        for p in res_b["personas"]
        if p.get("decisao_agregada")
    ]

    boot_a = bootstrap_ic95(bernoulli_a, n_resamples=10000)
    boot_b = bootstrap_ic95(bernoulli_b, n_resamples=10000)

    # Diferenca
    diff = boot_b["media"] - boot_a["media"]
    # IC95% da diferenca via bootstrap
    import numpy as np
    rng = np.random.default_rng(42)
    diffs = []
    for _ in range(10000):
        sa = rng.choice(bernoulli_a, size=len(bernoulli_a), replace=True)
        sb = rng.choice(bernoulli_b, size=len(bernoulli_b), replace=True)
        diffs.append(np.mean(sb) - np.mean(sa))
    diff_lo = float(np.percentile(diffs, 2.5))
    diff_hi = float(np.percentile(diffs, 97.5))

    # Significancia: IC95% da diferenca nao inclui 0
    significativo = not (diff_lo <= 0 <= diff_hi)

    # Power analysis
    power = power_analysis(boot_b["media"], boot_a["media"], n)

    # Vencedor
    if significativo:
        vencedor = "B (financeiro)" if diff > 0 else "A (tecnico)"
    else:
        vencedor = "empate (sem diferenca significativa)"

    result = {
        "variante_A": {
            "scenario": scenario_a,
            "taxa_conversao": boot_a["media"],
            "bootstrap_ic95": boot_a,
        },
        "variante_B": {
            "scenario": scenario_b,
            "taxa_conversao": boot_b["media"],
            "bootstrap_ic95": boot_b,
        },
        "diferenca": {
            "B_minus_A": round(diff, 4),
            "ic95": [round(diff_lo, 4), round(diff_hi, 4)],
            "significativo": significativo,
        },
        "power_analysis": power,
        "vencedor": vencedor,
        "recomendacao": (
            f"Recomendar {vencedor}" if significativo
            else "Sem diferenca significativa. Aumentar N para confirmar."
        ),
    }
    return result


def main():
    parser = argparse.ArgumentParser(description="A/B test: pitch tecnico vs financeiro")
    parser.add_argument("--scenario-a", default="scenarios_v2/slz-c-army-A-tecnico.yaml")
    parser.add_argument("--scenario-b", default="scenarios_v2/slz-c-army-B-financeiro.yaml")
    parser.add_argument("--n", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="results_v2/ab_test_result.json")
    args = parser.parse_args()

    result = asyncio.run(run_ab_test(args.scenario_a, args.scenario_b, args.n, args.seed))
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
