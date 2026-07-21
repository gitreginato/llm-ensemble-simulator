"""CLI unificado do Simulation Army v2.

Uso:
    python -m simulation_army_v2 run --scenario scenarios_v2/slz-c-army.yaml --n 30 --seed 42
    python -m simulation_army_v2 baseline --model gpt-4o-mini --n 30 --seed 42
    python -m simulation_army_v2 ab-test --n 30 --seed 42
    python -m simulation_army_v2 metrics
    python -m simulation_army_v2 audit
    python -m simulation_army_v2 objections
    python -m simulation_army_v2 scale --seeds 42 123 456 --n 30
    python -m simulation_army_v2 eval
"""
import argparse
import asyncio
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="simulation_army_v2",
        description="Simulation Army v2: ensemble de IAs para reduzir vies cognitivo",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # run (ensemble)
    p_run = sub.add_parser("run", help="Roda ensemble completo (3 modelos + sintetizador)")
    p_run.add_argument("--scenario", default="scenarios_v2/slz-c-army.yaml")
    p_run.add_argument("--n", type=int, default=30)
    p_run.add_argument("--seed", type=int, default=42)
    p_run.add_argument("--output", default=None)

    # baseline
    p_base = sub.add_parser("baseline", help="Roda baseline com 1 modelo")
    p_base.add_argument("--model", required=True)
    p_base.add_argument("--scenario", default="scenarios_v2/slz-c-army.yaml")
    p_base.add_argument("--n", type=int, default=30)
    p_base.add_argument("--seed", type=int, default=42)
    p_base.add_argument("--output", default=None)

    # ab-test
    p_ab = sub.add_parser("ab-test", help="A/B test: 2 variantes de pitch")
    p_ab.add_argument("--scenario-a", default="scenarios_v2/slz-c-army-A-tecnico.yaml")
    p_ab.add_argument("--scenario-b", default="scenarios_v2/slz-c-army-B-financeiro.yaml")
    p_ab.add_argument("--n", type=int, default=30)
    p_ab.add_argument("--seed", type=int, default=42)
    p_ab.add_argument("--output", default="results_v2/ab_test_result.json")

    # metrics
    p_met = sub.add_parser("metrics", help="Metricas de diversidade (entropia, KL, pairwise)")
    p_met.add_argument("--ensemble", default="results_v2/ensemble_n30_s42.json")
    p_met.add_argument("--output", default="results_v2/metricas_diversidade.json")

    # audit
    p_aud = sub.add_parser("audit", help="Auditoria de coerencia (10pct por frontier)")
    p_aud.add_argument("--ensemble", default="results_v2/ensemble_n30_s42.json")
    p_aud.add_argument("--auditor", default="command-r-plus-08-2024")
    p_aud.add_argument("--output", default="results_v2/auditoria_coerencia.json")

    # objections
    p_obj = sub.add_parser("objections", help="Mapa de objecoes ponderado")
    p_obj.add_argument("--ensemble", default="results_v2/ensemble_n30_s42.json")
    p_obj.add_argument("--output", default="results_v2/mapa_objecoes.json")

    # scale
    p_scl = sub.add_parser("scale", help="Escala multi-seed + bootstrap + power analysis")
    p_scl.add_argument("--seeds", nargs="+", type=int, default=[42, 123, 456])
    p_scl.add_argument("--n", type=int, default=30)
    p_scl.add_argument("--bootstrap-only", action="store_true")
    p_scl.add_argument("--output", default="results_v2/escala_analise.json")

    # eval
    p_eval = sub.add_parser("eval", help="Eval: 3 checks (calibracao, diversidade, coerencia)")

    args = parser.parse_args()

    if args.command == "run":
        from simulation_army_v2.ensemble import run_ensemble
        output = args.output or f"results_v2/ensemble_n{args.n}_s{args.seed}.json"
        asyncio.run(run_ensemble(args.scenario, args.n, args.seed, output))

    elif args.command == "baseline":
        from simulation_army_v2.baseline import run_baseline
        model_slug = args.model.replace("/", "_").replace(".", "_")
        output = args.output or f"results_v2/baseline_{model_slug}_n{args.n}_s{args.seed}.json"
        asyncio.run(run_baseline(args.scenario, args.model, args.n, args.seed, output))

    elif args.command == "ab-test":
        from simulation_army_v2.ab_test import run_ab_test
        result = asyncio.run(run_ab_test(args.scenario_a, args.scenario_b, args.n, args.seed))
        import json
        from pathlib import Path
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "metrics":
        from simulation_army_v2.metrics import analisar_resultados
        import json
        from pathlib import Path
        baselines = [
            "results_v2/baseline_gpt-4o-mini_n30_s42.json",
            "results_v2/baseline_command-r-plus_n30_s42.json",
            "results_v2/baseline_llama-3_3-70b-versatile_n30_s42.json",
        ]
        result = analisar_resultados(args.ensemble, baselines, args.output)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "audit":
        from simulation_army_v2.audit import run_audit
        asyncio.run(run_audit(args.ensemble, args.auditor, 0.1, 42, args.output))

    elif args.command == "objections":
        from simulation_army_v2.objections import analisar_objecoes
        import json
        from pathlib import Path
        result = analisar_objecoes(args.ensemble)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "scale":
        from simulation_army_v2.scale import main as scale_main
        sys.argv = ["scale"] + (["--bootstrap-only"] if args.bootstrap_only else []) + \
                   ["--seeds"] + [str(s) for s in args.seeds] + \
                   ["--n", str(args.n)] + ["--output", args.output]
        scale_main()

    elif args.command == "eval":
        from simulation_army_v2.eval import run_eval
        import json
        result = run_eval()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
