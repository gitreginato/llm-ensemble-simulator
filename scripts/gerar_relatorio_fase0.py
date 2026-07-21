"""Gera relatorio final da FASE 0 + mapa de prospeccao por bairro/nicho.

Le os resultados da simulacao v0 e gera:
- results_v2/fase0_relatorio.md: relatorio completo em markdown
- results_v2/mapa_prospeccao.json: mapa bairro x nicho x P(agendou) x WTP
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from simulation_army_v2.bairros_slz import BAIRROS_SLZ
from simulation_army_v2.informacao import analise_completa
from simulation_army_v2.modelo_probabilistico import ic_bayesiano
from simulation_army_v2.personas_v5 import MENSALIDADE_MIN

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results_v2"


def gerar_mapa_prospeccao(resultado_sim: dict) -> dict:
    """Gera mapa de prospeccao: bairro x nicho x conversao x WTP.

    Args:
        resultado_sim: resultado da simulacao v0

    Returns:
        Dict estruturado para JSON.
    """
    resultados = resultado_sim["resultados"]

    # Agrupa por (bairro, nicho)
    matriz = defaultdict(lambda: {"n": 0, "agendou": 0, "wtp_mediana": [], "revenue_mediana": []})
    for r in resultados:
        p = r["persona"]
        s = r["simulacao"]
        key = (p["bairro"], p["segment"])
        matriz[key]["n"] += 1
        if s["decisao"] == "agendou":
            matriz[key]["agendou"] += 1
        matriz[key]["wtp_mediana"].append(p["wtp_brl"])
        matriz[key]["revenue_mediana"].append(p["revenue_mensal"])

    # Calcula metricas
    mapa = []
    for (bairro, nicho), dados in matriz.items():
        if dados["n"] == 0:
            continue
        conv = dados["agendou"] / dados["n"]
        lo, hi = ic_bayesiano(dados["agendou"], dados["n"])
        wtp_sorted = sorted(dados["wtp_mediana"])
        wtp_med = wtp_sorted[len(wtp_sorted) // 2] if wtp_sorted else 0
        rev_sorted = sorted(dados["revenue_mediana"])
        rev_med = rev_sorted[len(rev_sorted) // 2] if rev_sorted else 0

        # Potencial = conversao * numero de empresas do nicho no bairro
        n_empresas = BAIRROS_SLZ.get(bairro, {}).get("empresas", 1000)
        # ponytail: heuristica simples. 26 nichos distribuidos ~ uniformemente
        # => cada nicho e ~3.8% das empresas. Arredondamos para 5% (margem de seguranca).
        # Upgrade path: usar distribuicao real por nicho se disponivel (LeadJet tem).
        est_empresas_nicho = max(1, int(n_empresas * 0.05))
        potencial_agendamentos = int(conv * est_empresas_nicho)

        mapa.append({
            "bairro": bairro,
            "nicho": nicho,
            "risco_bairro": BAIRROS_SLZ.get(bairro, {}).get("risco", "medio"),
            "n_simulado": dados["n"],
            "conversao": round(conv, 4),
            "ic_95": [round(lo, 4), round(hi, 4)],
            "wtp_mediana": round(wtp_med, 2),
            "revenue_mediana": round(rev_med, 2),
            "pode_pagar_mensalidade": wtp_med >= MENSALIDADE_MIN,
            "est_empresas_nicho": est_empresas_nicho,
            "potencial_agendamentos": potencial_agendamentos,
        })

    # Ordena por potencial
    mapa.sort(key=lambda x: -x["potencial_agendamentos"])
    return mapa


def gerar_relatorio_md(resultado_sim: dict, mapa: dict, analise_real: dict) -> str:
    """Gera relatorio em markdown.

    Args:
        resultado_sim: resultado da simulacao v0
        mapa: mapa de prospeccao
        analise_real: analise de informacao do dataset real (142 personas)

    Returns:
        String com relatorio em markdown.
    """
    meta = resultado_sim["meta"]
    stats = resultado_sim["estatisticas"]
    mc = stats["monte_carlo"]

    linhas = []
    linhas.append("# Relatorio FASE 0: Simulacao Programatica EMIVE Sao Luis-MA")
    linhas.append("")
    linhas.append(f"**Data:** {date.today().isoformat()}")
    linhas.append(f"**N personas:** {meta['n_personas']}")
    linhas.append(f"**Segmento:** {meta['segment']}")
    linhas.append(f"**Mes:** {meta['mes']} (sazonalidade)")
    linhas.append(f"**Canal:** {meta['canal']}")
    linhas.append(f"**Mercado:** {meta['mercado']}")
    linhas.append(f"**Tempo de execucao:** {meta['tempo_segundos']}s")
    linhas.append(f"**Mensalidade base:** R$ {MENSALIDADE_MIN:.0f}")
    linhas.append("")
    linhas.append("---")
    linhas.append("")

    # 1. Estatisticas globais
    linhas.append("## 1. Estatisticas Globais")
    linhas.append("")
    linhas.append(f"| Metrica | Valor |")
    linhas.append(f"|---|---|")
    linhas.append(f"| Taxa de conversao | {stats['taxa_conversao']:.1%} |")
    linhas.append(f"| IC 95% bayesiano | [{stats['ic_95_bayesiano'][0]:.1%}, {stats['ic_95_bayesiano'][1]:.1%}] |")
    linhas.append(f"| MC mediana | {mc['conversao_mediana']:.1%} |")
    linhas.append(f"| MC P5 | {mc['conversao_p5']:.1%} |")
    linhas.append(f"| MC P95 | {mc['conversao_p95']:.1%} |")
    linhas.append(f"| MC desvio | {mc['conversao_std']:.1%} |")
    linhas.append("")
    linhas.append(f"**Decisoes:** {stats['decisoes']}")
    linhas.append("")

    # 2. Objeções
    linhas.append("## 2. Objecoes")
    linhas.append("")
    linhas.append("| Objecao | Contagem | % |")
    linhas.append("|---|---|---|")
    total_obj = sum(stats["objecoes"].values())
    for obj, count in sorted(stats["objecoes"].items(), key=lambda x: -x[1]):
        pct = count / total_obj if total_obj > 0 else 0
        linhas.append(f"| {obj} | {count} | {pct:.1%} |")
    linhas.append("")

    # 3. Competencias medias
    linhas.append("## 3. Competencias Medias (avaliacao do pitch)")
    linhas.append("")
    linhas.append("| Competencia | Score (0-10) |")
    linhas.append("|---|---|")
    for comp, score in stats["competencias_medias"].items():
        linhas.append(f"| {comp.replace('_', ' ').title()} | {score} |")
    linhas.append("")

    # 4. Por nicho
    if resultado_sim["por_nicho"]:
        linhas.append("## 4. Conversao por Nicho")
        linhas.append("")
        linhas.append("| Nicho | N | Agendou | Conversao | IC 95% |")
        linhas.append("|---|---|---|---|---|")
        for nicho, dados in sorted(resultado_sim["por_nicho"].items(), key=lambda x: -x[1]["conversao"]):
            linhas.append(f"| {nicho} | {dados['n']} | {dados['agendou']} | {dados['conversao']:.1%} | [{dados['ic_95'][0]:.1%}, {dados['ic_95'][1]:.1%}] |")
        linhas.append("")

    # 5. Por bairro
    if resultado_sim["por_bairro"]:
        linhas.append("## 5. Conversao por Bairro")
        linhas.append("")
        linhas.append("| Bairro | Risco | N | Agendou | Conversao | IC 95% |")
        linhas.append("|---|---|---|---|---|---|")
        for bairro, dados in sorted(resultado_sim["por_bairro"].items(), key=lambda x: -x[1]["conversao"]):
            risco = BAIRROS_SLZ.get(bairro, {}).get("risco", "?")
            linhas.append(f"| {bairro} | {risco} | {dados['n']} | {dados['agendou']} | {dados['conversao']:.1%} | [{dados['ic_95'][0]:.1%}, {dados['ic_95'][1]:.1%}] |")
        linhas.append("")

    # 6. Analise de informacao
    linhas.append("## 6. Analise de Informacao")
    linhas.append("")
    linhas.append("### 6.1 Informacao Mutua (feature ; decisao)")
    linhas.append("")
    linhas.append("| Feature | MI (bits) | Interpretacao |")
    linhas.append("|---|---|---|")
    for feat, mi in resultado_sim["informacao"]["mi_features"]:
        if mi > 0.1:
            interp = "driver forte"
        elif mi > 0.05:
            interp = "driver moderado"
        else:
            interp = "driver fraco"
        linhas.append(f"| {feat} | {mi} | {interp} |")
    linhas.append("")

    # 6.2 Entropia por nicho
    linhas.append("### 6.2 Entropia por Nicho")
    linhas.append("")
    linhas.append("| Nicho | H (bits) | H norm | Distribuicao |")
    linhas.append("|---|---|---|---|")
    for nicho, dados in sorted(resultado_sim["informacao"]["entropia_por_nicho"].items(),
                                key=lambda x: -x[1]["h_bits"]):
        linhas.append(f"| {nicho} | {dados['h_bits']} | {dados['h_norm']} | {dados['distribuicao']} |")
    linhas.append("")
    linhas.append("> H alta = imprevisivel (pitch importa). H baixa = deterministico (pouco o que fazer).")
    linhas.append("")

    # 7. Comparacao com dataset real
    n_real = analise_real.get("n_personas", 0)
    dist_real = analise_real.get("entropia_global", {}).get("distribuicao", {})
    n_agendou_real = dist_real.get("agendou", 0)
    conv_real = n_agendou_real / n_real if n_real > 0 else 0
    linhas.append(f"## 7. Comparacao com Dataset Real ({n_real} personas)")
    linhas.append("")
    linhas.append("| Metrica | Real ({}) | Simulado (N={}) |".format(n_real, meta["n_personas"]))
    linhas.append("|---|---|---|")
    linhas.append(f"| Conversao | {conv_real:.1%} | {stats['taxa_conversao']:.1%} |")
    mi_real = analise_real.get("informacao_mutua_features", [])
    mi_sim = resultado_sim["informacao"]["mi_features"]
    mi_re_0 = mi_real[0][1] if len(mi_real) > 0 else 0
    mi_re_1 = mi_real[1][1] if len(mi_real) > 1 else 0
    mi_si_0 = mi_sim[0][1] if len(mi_sim) > 0 else 0
    mi_si_1 = mi_sim[1][1] if len(mi_sim) > 1 else 0
    linhas.append(f"| MI recent_event | {mi_re_0} | {mi_si_0} |")
    linhas.append(f"| MI segment | {mi_re_1} | {mi_si_1} |")
    linhas.append(f"| H global | {analise_real.get('entropia_global', {}).get('h_bits', 0)} | (ver entropia por nicho acima) |")
    linhas.append("")

    # 8. Mapa de prospeccao
    linhas.append("## 8. Mapa de Prospeccao (top 20 bairro x nicho)")
    linhas.append("")
    linhas.append("| Bairro | Nicho | Risco | Conv | IC 95% | WTP med | Empresas est. | Potencial |")
    linhas.append("|---|---|---|---|---|---|---|---|")
    for item in mapa[:20]:
        linhas.append(
            f"| {item['bairro']} | {item['nicho']} | {item['risco_bairro']} | "
            f"{item['conversao']:.1%} | [{item['ic_95'][0]:.1%}, {item['ic_95'][1]:.1%}] | "
            f"R$ {item['wtp_mediana']:.0f} | {item['est_empresas_nicho']} | "
            f"{item['potencial_agendamentos']} |"
        )
    linhas.append("")

    # 9. Recomendacoes
    linhas.append("## 9. Recomendacoes de Prospeccao")
    linhas.append("")
    # Top 3 bairros por potencial
    bairros_pot = defaultdict(int)
    for item in mapa:
        bairros_pot[item["bairro"]] += item["potencial_agendamentos"]
    top_bairros = sorted(bairros_pot.items(), key=lambda x: -x[1])[:5]
    linhas.append("### 9.1 Bairros prioritarios para scrap no Maps")
    linhas.append("")
    for bairro, pot in top_bairros:
        risco = BAIRROS_SLZ.get(bairro, {}).get("risco", "?")
        n_emp = BAIRROS_SLZ.get(bairro, {}).get("empresas", 0)
        linhas.append(f"- **{bairro}** (risco {risco}, {n_emp} empresas): potencial ~{pot} agendamentos")
    linhas.append("")

    # Top 3 nichos por conversao
    if resultado_sim["por_nicho"]:
        top_nichos = sorted(resultado_sim["por_nicho"].items(), key=lambda x: -x[1]["conversao"])[:3]
        linhas.append("### 9.2 Nichos prioritarios")
        linhas.append("")
        for nicho, dados in top_nichos:
            linhas.append(f"- **{nicho}**: conversao {dados['conversao']:.1%} (IC {dados['ic_95'][0]:.1%}-{dados['ic_95'][1]:.1%})")
    linhas.append("")

    # Drivers de decisao
    linhas.append("### 9.3 Drivers de decisao (por informacao mutua)")
    linhas.append("")
    for feat, mi in resultado_sim["informacao"]["mi_features"]:
        if mi > 0.05:
            linhas.append(f"- **{feat}**: MI={mi} bits (driver significativo)")
    linhas.append("")
    linhas.append("> Foco em personas com `recent_event=theft` e `has_existing_security=none` para maximizar conversao.")
    linhas.append("")

    linhas.append("---")
    linhas.append("")
    linhas.append("*Relatorio gerado por scripts/gerar_relatorio_fase0.py*")

    return "\n".join(linhas)


def main():
    """Gera relatorio e mapa de prospeccao."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Gera relatorio FASE 0")
    parser.add_argument("--sim", type=str, default="sim_v0_n1000_segdistribuido_mes7.json",
                        help="Nome do arquivo de simulacao em results_v2/")
    args = parser.parse_args()

    # Carrega resultado da simulacao
    sim_path = RESULTS_DIR / args.sim
    if not sim_path.exists():
        print(f"Erro: {sim_path} nao encontrado. Rode scripts/run_sim_v0.py primeiro.")
        sys.exit(1)

    resultado_sim = json.loads(sim_path.read_text(encoding="utf-8"))

    # Analise do dataset real
    analise_real = analise_completa(str(RESULTS_DIR / "dataset_real.json"))

    # Gera mapa de prospeccao
    mapa = gerar_mapa_prospeccao(resultado_sim)

    # Salva mapa JSON
    mapa_path = RESULTS_DIR / "mapa_prospeccao.json"
    mapa_path.write_text(json.dumps(mapa, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Mapa: {mapa_path}")

    # Gera relatorio markdown
    relatorio = gerar_relatorio_md(resultado_sim, mapa, analise_real)
    rel_path = RESULTS_DIR / "fase0_relatorio.md"
    rel_path.write_text(relatorio, encoding="utf-8")
    print(f"Relatorio: {rel_path}")

    # Resumo
    print(f"\n=== RESUMO ===")
    print(f"Mapa: {len(mapa)} combinacoes bairro x nicho")
    print(f"Top 3 potencial:")
    for item in mapa[:3]:
        print(f"  {item['bairro']} / {item['nicho']}: conv={item['conversao']:.1%} potencial={item['potencial_agendamentos']}")


if __name__ == "__main__":
    main()
