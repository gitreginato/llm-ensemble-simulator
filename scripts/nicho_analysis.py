#!/usr/bin/env python3
"""Analise multi-nicho: roda baseline (1 modelo) para 8 nichos relevantes para EMIVE.

Usa command-a-03-2025 (sintetizador, funciona bem) via gocat.
N=10 por nicho = 80 requests total. ~7min.

Nichos selecionados (alto valor de estoque + vitrine exposta + dor noturna):
- loja_roupas (baseline, ja temos dados)
- loja_calcados (similar, vitrine exposta)
- farmacia (estoque valioso, alto fluxo, drogaria)
- autopecas (estoque valioso, ferramentas)
- mercearia (estoque valioso, movimento)
- bar (movimento noturno, alcool, caixa)
- hamburgueria (movimento noturno, caixa)
- oficina (ferramentas valiosas, veiculos)
"""
import argparse
import asyncio
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from simulation_army_v2.baseline import _call_model, _profile_to_prompt_kwargs
from simulation_army_v2.config import load_config
from simulation_army_v2.ensemble import USER_PROMPT_TEMPLATE
from src.advanced_simulation import generate_personas

import httpx

NICHOS = [
    "loja_roupas",
    "loja_calcados",
    "farmacia",
    "autopecas",
    "mercearia",
    "bar",
    "hamburgueria",
    "oficina",
]

MODEL = "command-a-03-2025"  # sintetizador, funciona bem via gocat
N = 10


async def run_nicho(nicho: str, n: int, seed: int) -> list[dict]:
    """Roda baseline para 1 nicho. Retorna lista de decisoes."""
    cfg = load_config("scenarios_v2/slz-c-army-v4.yaml")
    cfg.scenario.target_segment = nicho
    cfg.scenario.num_agents = n

    personas = generate_personas(nicho, n)
    results = []

    async with httpx.AsyncClient(timeout=120) as client:
        for i, p in enumerate(personas, 1):
            user_prompt = USER_PROMPT_TEMPLATE.format(**_profile_to_prompt_kwargs(p, cfg))
            try:
                d, meta = await _call_model(client, MODEL, user_prompt)
                results.append({
                    "nome": p.owner_name,
                    "segment": p.segment,
                    "risk_profile": p.risk_profile,
                    "recent_event": p.recent_event,
                    "has_existing_security": p.has_existing_security,
                    "wtp_brl": p.wtp_brl,
                    "decisao": d.decisao,
                    "wtp": d.wtp,
                    "sentimento": d.sentimento,
                    "confianca": d.confianca,
                    "objecoes": d.objecoes,
                    "raciocinio": d.raciocinio,
                    "latency_ms": meta.get("latency_ms"),
                })
                print(f"  [{i}/{n}] {nicho} {p.owner_name}: {d.decisao} wtp=R${d.wtp:.0f} lat={meta.get('latency_ms')}ms")
            except Exception as e:
                results.append({
                    "nome": p.owner_name,
                    "segment": p.segment,
                    "risk_profile": p.risk_profile,
                    "recent_event": p.recent_event,
                    "has_existing_security": p.has_existing_security,
                    "wtp_brl": p.wtp_brl,
                    "decisao": "erro",
                    "erro": str(e)[:200],
                })
                print(f"  [{i}/{n}] {nicho} {p.owner_name}: FAIL {e}")
            await asyncio.sleep(1)
    return results


async def main():
    parser = argparse.ArgumentParser(description="Analise multi-nicho EMIVE")
    parser.add_argument("--n", type=int, default=N)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="results_v2/nicho_analysis.json")
    args = parser.parse_args()

    all_results = {}
    for nicho in NICHOS:
        print(f"\n=== {nicho} ===")
        results = await run_nicho(nicho, args.n, args.seed)
        all_results[nicho] = results

    # Analise por nicho
    print("\n\n=== ANALISE POR NICHO ===")
    by_nicho = {}
    for nicho, results in all_results.items():
        total = len(results)
        agendou = sum(1 for r in results if r["decisao"] == "agendou")
        clicou = sum(1 for r in results if r["decisao"] == "clicou")
        visualizou = sum(1 for r in results if r["decisao"] == "visualizou")
        ignorou = sum(1 for r in results if r["decisao"] == "ignorou")
        erros = sum(1 for r in results if r["decisao"] == "erro")
        wtps = [r.get("wtp", 0) for r in results if r["decisao"] != "erro"]
        wtp_med = sum(wtps) / len(wtps) if wtps else 0
        conv = agendou / total if total > 0 else 0
        by_nicho[nicho] = {
            "total": total, "agendou": agendou, "clicou": clicou,
            "visualizou": visualizou, "ignorou": ignorou, "erros": erros,
            "conversao": conv, "wtp_medio": wtp_med,
        }
        print(f"{nicho}: conv={conv:.0%} ({agendou}/{total}) wtp_med=R${wtp_med:.0f} "
              f"agendou={agendou} clicou={clicou} visualizou={visualizou} ignorou={ignorou} erro={erros}")

    # Ranking
    print("\n=== RANKING DE CONVERSAO ===")
    for nicho, d in sorted(by_nicho.items(), key=lambda x: -x[1]["conversao"]):
        print(f"  {nicho}: {d['conversao']:.0%} (WTP R${d['wtp_medio']:.0f})")

    # Salvar
    output = {
        "model": MODEL,
        "n": args.n,
        "seed": args.seed,
        "por_nicho": by_nicho,
        "detalhes": all_results,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
