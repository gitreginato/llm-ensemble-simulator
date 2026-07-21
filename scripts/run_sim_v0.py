"""Simulador programatico completo (FASE 0).

Integra:
- personas_v5: gerador de personas com bairros reais e budget mensal
- modelo_probabilistico: sigmoid + Bayes + Monte Carlo
- informacao: entropia, MI, JSD, chi-quadrado
- pitch_templates: narrativa por nicho + avaliacao de competencias

Roda N=1000 personas em < 1s, sem custo, sem rede, sem LLM.
Output: JSON + relatorio markdown + dashboard HTML.
"""
from __future__ import annotations

import json
import random
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from simulation_army_v2.informacao import (
    analise_completa,
    entropia_por_grupo,
    entropia_shannon,
    informacao_mutua,
    ranquear_features_por_mi,
)
from simulation_army_v2.modelo_probabilistico import (
    PersonaInput,
    amostrar_decisao,
    calcular_prob_agendou,
    gerar_objecoes,
    ic_bayesiano,
    monte_carlo,
)
from simulation_army_v2.personas_v5 import generate_personas_v5, persona_to_dict
from simulation_army_v2.pitch_templates import avaliar_competencias, gerar_pitch


def persona_v5_to_input(p) -> PersonaInput:
    """Converte PersonaV5 para PersonaInput do modelo probabilistico."""
    return PersonaInput(
        segment=p.segment,
        risk_profile=p.risk_profile,
        recent_event=p.recent_event,
        has_existing_security=p.has_existing_security,
        wtp_brl=p.wtp_brl,
        bairro=p.bairro,
        bairro_p_theft=p.bairro_p_theft,
        budget_mensal=p.budget_mensal_seguranca,
        mensalidade=p.mensalidade_emive,
        ticket_medio_36m=p.ticket_medio_36m,
        precisa_area_externa=p.precisa_area_externa,
        concorrencia_local_instalada=p.concorrencia_local_instalada,
    )


def simular_persona(p, rng: random.Random, canal: str = "phone_call",
                    mercado: str = "mercado_c_nao_avisado") -> dict[str, Any]:
    """Simula uma persona: gera pitch, calcula prob, amostra decisao, gera objecoes.

    Args:
        p: PersonaV5
        rng: random.Random
        canal: phone_call ou whatsapp
        mercado: mercado_a, mercado_c_avisado, mercado_c_nao_avisado

    Returns:
        Dict com resultado da simulacao.
    """
    # Converte para input do modelo
    p_input = persona_v5_to_input(p)

    # Calcula probabilidade
    prob_agendou = calcular_prob_agendou(p_input)

    # Amostra decisao
    decisao = amostrar_decisao(p_input, rng)

    # Gera objecoes
    objecoes = gerar_objecoes(p_input, decisao, rng)

    # Gera pitch
    pitch = gerar_pitch(p, canal=canal, mercado=mercado)

    # Avalia competencias
    scores = avaliar_competencias(pitch, decisao, objecoes)

    # Persona dict
    p_dict = persona_to_dict(p)

    return {
        "persona": p_dict,
        "simulacao": {
            "prob_agendou": round(prob_agendou, 4),
            "decisao": decisao,
            "objecoes": objecoes,
            "pitch": pitch,
            "competencias": scores,
            "canal": canal,
            "mercado": mercado,
        },
    }


def rodar_simulacao(
    n: int = 1000,
    segment: str | None = None,
    mes: int = 7,
    seed: int = 42,
    canal: str = "phone_call",
    mercado: str = "mercado_c_nao_avisado",
    n_seeds_monte_carlo: int = 100,
) -> dict[str, Any]:
    """Roda simulacao completa.

    Args:
        n: numero de personas
        segment: nicho especifico ou None para distribuir
        mes: mes (1-12) para sazonalidade
        seed: seed aleatoria
        canal: phone_call ou whatsapp
        mercado: mercado_a, mercado_c_avisado, mercado_c_nao_avisado
        n_seeds_monte_carlo: numero de seeds para Monte Carlo

    Returns:
        Dict completo com personas, estatisticas, informacao.
    """
    t0 = time.time()

    # 1. Gera personas
    personas = generate_personas_v5(n=n, segment=segment, mes=mes, seed=seed)

    # 2. Simula cada persona
    rng = random.Random(seed + 1)
    resultados = []
    for p in personas:
        resultado = simular_persona(p, rng, canal=canal, mercado=mercado)
        resultados.append(resultado)

    # 3. Estatisticas aggregate
    decisoes = defaultdict(int)
    for r in resultados:
        decisoes[r["simulacao"]["decisao"]] += 1

    total = len(resultados)
    n_agendou = decisoes.get("agendou", 0)
    taxa_conv = n_agendou / total if total > 0 else 0

    # IC bayesiano
    ic_lo, ic_hi = ic_bayesiano(n_agendou, total)

    # 4. Monte Carlo
    personas_input = [persona_v5_to_input(p) for p in personas]
    mc = monte_carlo(personas_input, n_seeds=n_seeds_monte_carlo, base_seed=seed)

    # 5. Analise de informacao
    # Prepara personas para analise (formato compativel)
    personas_analise = []
    for r in resultados:
        p = r["persona"]
        s = r["simulacao"]
        personas_analise.append({
            "segment": p["segment"],
            "bairro": p["bairro"],
            "risk_profile": p["risk_profile"],
            "recent_event": p["recent_event"],
            "has_existing_security": p["has_existing_security"],
            "decisao": s["decisao"],
        })

    # Entropia por nicho
    ent_nichos = entropia_por_grupo(personas_analise, "segment")
    # Entropia por bairro
    ent_bairros = entropia_por_grupo(personas_analise, "bairro")
    # MI features
    mi_features = ranquear_features_por_mi(personas_analise)

    # 6. Por nicho (se distribuido)
    por_nicho = {}
    if segment is None:
        for seg in set(p["segment"] for p in personas_analise):
            seg_results = [r for r in resultados if r["persona"]["segment"] == seg]
            seg_decisoes = defaultdict(int)
            for r in seg_results:
                seg_decisoes[r["simulacao"]["decisao"]] += 1
            seg_total = len(seg_results)
            seg_agendou = seg_decisoes.get("agendou", 0)
            seg_conv = seg_agendou / seg_total if seg_total > 0 else 0
            seg_lo, seg_hi = ic_bayesiano(seg_agendou, seg_total)
            por_nicho[seg] = {
                "n": seg_total,
                "agendou": seg_agendou,
                "conversao": round(seg_conv, 4),
                "ic_95": [round(seg_lo, 4), round(seg_hi, 4)],
                "decisoes": dict(seg_decisoes),
            }

    # 7. Por bairro
    por_bairro = {}
    for bairro in set(p["bairro"] for p in personas_analise):
        b_results = [r for r in resultados if r["persona"]["bairro"] == bairro]
        b_decisoes = defaultdict(int)
        for r in b_results:
            b_decisoes[r["simulacao"]["decisao"]] += 1
        b_total = len(b_results)
        b_agendou = b_decisoes.get("agendou", 0)
        b_conv = b_agendou / b_total if b_total > 0 else 0
        b_lo, b_hi = ic_bayesiano(b_agendou, b_total)
        por_bairro[bairro] = {
            "n": b_total,
            "agendou": b_agendou,
            "conversao": round(b_conv, 4),
            "ic_95": [round(b_lo, 4), round(b_hi, 4)],
            "decisoes": dict(b_decisoes),
        }

    # 8. Objeções aggregate
    objecoes_agg = defaultdict(int)
    for r in resultados:
        for o in r["simulacao"]["objecoes"]:
            objecoes_agg[o] += 1

    # 9. Competencias medias
    comp_medias = defaultdict(list)
    for r in resultados:
        for k, v in r["simulacao"]["competencias"].items():
            comp_medias[k].append(v)
    comp_medias = {k: round(sum(v) / len(v), 2) for k, v in comp_medias.items()}

    t1 = time.time()

    return {
        "meta": {
            "n_personas": n,
            "segment": segment or "distribuido",
            "mes": mes,
            "seed": seed,
            "canal": canal,
            "mercado": mercado,
            "tempo_segundos": round(t1 - t0, 3),
        },
        "estatisticas": {
            "taxa_conversao": round(taxa_conv, 4),
            "ic_95_bayesiano": [round(ic_lo, 4), round(ic_hi, 4)],
            "decisoes": dict(decisoes),
            "monte_carlo": {
                "conversao_mediana": mc["conversao_mediana"],
                "conversao_p5": mc["conversao_p5"],
                "conversao_p95": mc["conversao_p95"],
                "conversao_std": mc["conversao_std"],
            },
            "objecoes": dict(objecoes_agg),
            "competencias_medias": comp_medias,
        },
        "por_nicho": por_nicho,
        "por_bairro": por_bairro,
        "informacao": {
            "entropia_por_nicho": ent_nichos,
            "entropia_por_bairro": ent_bairros,
            "mi_features": [(f, round(mi, 4)) for f, mi in mi_features],
        },
        "resultados": resultados,
    }


def salvar_resultados(resultado: dict, output_dir: str = "results_v2") -> dict[str, str]:
    """Salva resultados em JSON.

    Returns:
        Dict com caminhos dos arquivos salvos.
    """
    out = Path(output_dir)
    try:
        out.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise PermissionError(f"output_dir sem permissao de escrita: {output_dir}") from e

    meta = resultado["meta"]
    nome = f"sim_v0_n{meta['n_personas']}_seg{meta['segment']}_mes{meta['mes']}"

    # JSON completo
    json_path = out / f"{nome}.json"
    try:
        json_path.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    except PermissionError as e:
        raise PermissionError(f"output_dir sem permissao de escrita: {output_dir}") from e

    # JSON so estatisticas (mais leve)
    stats_path = out / f"{nome}_stats.json"
    stats = {k: v for k, v in resultado.items() if k != "resultados"}
    try:
        stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    except PermissionError as e:
        raise PermissionError(f"output_dir sem permissao de escrita: {output_dir}") from e

    return {"json_completo": str(json_path), "json_stats": str(stats_path)}


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Simulador programatico FASE 0")
    parser.add_argument("-n", "--n-personas", type=int, default=1000, help="Numero de personas")
    parser.add_argument("-s", "--segment", type=str, default=None, help="Nicho especifico")
    parser.add_argument("-m", "--mes", type=int, default=7, help="Mes (1-12)")
    parser.add_argument("--seed", type=int, default=42, help="Seed aleatoria")
    parser.add_argument("--canal", type=str, default="phone_call", choices=["phone_call", "whatsapp"])
    parser.add_argument("--mercado", type=str, default="mercado_c_nao_avisado",
                        choices=["mercado_a", "mercado_c_avisado", "mercado_c_nao_avisado"])
    parser.add_argument("--mc-seeds", type=int, default=100, help="Seeds para Monte Carlo")
    parser.add_argument("-o", "--output-dir", type=str, default="results_v2")
    args = parser.parse_args()

    if not 1 <= args.mes <= 12:
        parser.error(f"mes invalido: {args.mes}. Deve estar entre 1 e 12.")

    print(f"Rodando simulacao FASE 0: N={args.n_personas}, segment={args.segment or 'distribuido'}, mes={args.mes}")
    resultado = rodar_simulacao(
        n=args.n_personas,
        segment=args.segment,
        mes=args.mes,
        seed=args.seed,
        canal=args.canal,
        mercado=args.mercado,
        n_seeds_monte_carlo=args.mc_seeds,
    )

    paths = salvar_resultados(resultado, args.output_dir)

    print(f"\n=== RESULTADOS ===")
    print(f"Tempo: {resultado['meta']['tempo_segundos']}s")
    print(f"Taxa conversao: {resultado['estatisticas']['taxa_conversao']:.1%}")
    print(f"IC 95%: [{resultado['estatisticas']['ic_95_bayesiano'][0]:.1%}, {resultado['estatisticas']['ic_95_bayesiano'][1]:.1%}]")
    print(f"Monte Carlo: mediana={resultado['estatisticas']['monte_carlo']['conversao_mediana']:.1%} "
          f"P5={resultado['estatisticas']['monte_carlo']['conversao_p5']:.1%} "
          f"P95={resultado['estatisticas']['monte_carlo']['conversao_p95']:.1%}")
    print(f"\nDecisoes: {resultado['estatisticas']['decisoes']}")
    print(f"\nObjecoes: {resultado['estatisticas']['objecoes']}")
    print(f"\nMI features:")
    for feat, mi in resultado['informacao']['mi_features']:
        print(f"  {feat}: {mi} bits")

    if resultado['por_nicho']:
        print(f"\n=== POR NICHO ===")
        for nicho, dados in sorted(resultado['por_nicho'].items(), key=lambda x: -x[1]['conversao']):
            print(f"  {nicho}: conv={dados['conversao']:.1%} (IC {dados['ic_95'][0]:.1%}-{dados['ic_95'][1]:.1%}) n={dados['n']}")

    if resultado['por_bairro']:
        print(f"\n=== POR BAIRRO (top 5) ===")
        for bairro, dados in sorted(resultado['por_bairro'].items(), key=lambda x: -x[1]['conversao'])[:5]:
            print(f"  {bairro}: conv={dados['conversao']:.1%} (IC {dados['ic_95'][0]:.1%}-{dados['ic_95'][1]:.1%}) n={dados['n']}")

    print(f"\nArquivos: {paths}")


if __name__ == "__main__":
    main()
