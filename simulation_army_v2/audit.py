"""Auditoria de coerencia: 10% das decisoes auditadas por modelo de vendor diferente.

O auditor nao ve qual modelo gerou a decisao (blind audit).
Pontua coerencia 0..1. Rejeitar se score < 0.5. Criterio: % rejeitadas < 10%.
"""
import argparse
import asyncio
import json
import random
from pathlib import Path

import httpx

from simulation_army_v2.baseline import GOCAT_KEY, GOCAT_URL, _parse_json_response

RESULTS_DIR = Path(__file__).parent.parent / "results_v2"

AUDIT_PROMPT = """## Contexto
Voce e um auditor de qualidade. Uma IA tomou uma decisao de venda face a um dono de loja.
Sua tarefa e avaliar a COERENCIA da decisao, sem saber qual modelo a tomou.

## Perfil do dono
- Nome: {owner_name}
- Negocio: {business_name} ({segment})
- WTP estimado: R$ {wtp_brl}
- Risco: {risk_profile}
- Evento recente: {recent_event}
- Tem seguranca: {has_existing_security}

## Decisao auditada
- Decisao: {decisao_final}
- WTP medio: R$ {wtp_medio}
- Sentimento medio: {sentimento_medio}
- Objecoes: {objecoes}
- Confianca agregada: {confianca_agregada}
- Raciocinio: {raciocinio_sintese}

## Tarefa
Retorne APENAS um JSON:
{{
  "coerencia": float (0.0 a 1.0),
  "justificativa": "1-2 frases em portugues",
  "problemas": ["lista de problemas encontrados, se houver"]
}}

Criterios de coerencia:
- 1.0: decisao perfeitamente alinhada com perfil, WTP e objecoes
- 0.5: decisao plausivel mas com inconsistencias menores
- 0.0: decisao claramente errada (ex: agendou apesar de objecoes graves e WTP baixo)

Preste atencao a:
- WTP medio coerente com WTP estimado do perfil?
- Decisao coerente com sentimento e objecoes?
- Raciocinio justifica a decisao?
"""


async def auditar_decisao(
    client: httpx.AsyncClient,
    auditor_model: str,
    persona: dict,
    decisao: dict,
) -> dict:
    """Audita uma decisao agregada com modelo de vendor diferente."""
    prompt = AUDIT_PROMPT.format(
        owner_name=persona.get("owner_name", "?"),
        business_name=persona.get("business_name", "?"),
        segment=persona.get("segment", "?"),
        wtp_brl=persona.get("wtp_brl", 0),
        risk_profile=persona.get("risk_profile", "?"),
        recent_event=persona.get("recent_event", "?"),
        has_existing_security=persona.get("has_existing_security", False),
        decisao_final=decisao.get("decisao_final", "?"),
        wtp_medio=decisao.get("wtp_medio", 0),
        sentimento_medio=decisao.get("sentimento_medio", 0),
        objecoes=decisao.get("objecoes_consolidadas", []),
        confianca_agregada=decisao.get("confianca_agregada", 0),
        raciocinio_sintese=decisao.get("raciocinio_sintese", ""),
    )
    payload = {
        "model": auditor_model,
        "messages": [
            {"role": "system", "content": "You are a blind quality auditor. Return ONLY valid JSON."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 500,
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {GOCAT_KEY}", "Content-Type": "application/json"}
    for attempt in range(3):
        try:
            r = await client.post(
                f"{GOCAT_URL}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=60,
            )
            if r.status_code == 200:
                data = r.json()
                msg = data["choices"][0].get("message", {})
                content = msg.get("content") or ""
                if not content and msg.get("reasoning_content"):
                    content = msg["reasoning_content"]
                if not content:
                    raise ValueError("auditor: content empty")
                parsed = _parse_json_response(content)
                return {
                    "coerencia": float(parsed.get("coerencia", 0)),
                    "justificativa": parsed.get("justificativa", ""),
                    "problemas": parsed.get("problemas", []),
                    "rejeitada": float(parsed.get("coerencia", 0)) < 0.5,
                }
            if r.status_code >= 500 and attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            if r.status_code == 429 and attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"auditor HTTP {r.status_code}: {r.text[:200]}")
        except (httpx.HTTPError, json.JSONDecodeError, ValueError, KeyError, RuntimeError) as e:
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            return {"coerencia": 0.0, "justificativa": f"erro: {e}", "problemas": [str(e)], "rejeitada": True}
    return {"coerencia": 0.0, "justificativa": "3 tentativas falharam", "problemas": ["timeout"], "rejeitada": True}


async def run_audit(
    ensemble_path: str = None,
    auditor_model: str = "command-r-plus-08-2024",
    sample_pct: float = 0.1,
    seed: int = 42,
    output_path: str = None,
) -> dict:
    """Roda auditoria em amostra das decisoes agregadas."""
    if ensemble_path is None:
        ensemble_path = str(RESULTS_DIR / "ensemble_n30_s42.json")
    if output_path is None:
        output_path = str(RESULTS_DIR / "auditoria_coerencia.json")

    with open(ensemble_path, encoding="utf-8") as f:
        ens = json.load(f)

    # Filtra personas com decisao agregada.
    personas_com_agregada = [
        (p.get("persona", p), p["decisao_agregada"])
        for p in ens["personas"]
        if p.get("decisao_agregada")
    ]

    # Amostra 10% (minimo 3).
    n_sample = max(3, int(len(personas_com_agregada) * sample_pct))
    rng = random.Random(seed)
    amostra = rng.sample(personas_com_agregada, min(n_sample, len(personas_com_agregada)))

    print(f"[AUDIT] modelo={auditor_model} amostra={len(amostra)}/{len(personas_com_agregada)} ({sample_pct:.0%})")

    auditorias = []
    async with httpx.AsyncClient() as client:
        for i, (persona, decisao) in enumerate(amostra, 1):
            result = await auditar_decisao(client, auditor_model, persona, decisao)
            auditorias.append({
                "owner_name": persona.get("owner_name", "?"),
                "decisao_final": decisao.get("decisao_final", "?"),
                "coerencia": result["coerencia"],
                "rejeitada": result["rejeitada"],
                "justificativa": result["justificativa"],
                "problemas": result["problemas"],
            })
            status = "REJEITADA" if result["rejeitada"] else "OK"
            print(f"  [{i}/{len(amostra)}] {persona.get('owner_name', '?')}: {decisao.get('decisao_final', '?')} coerencia={result['coerencia']:.2f} {status}")
            await asyncio.sleep(2)

    # Metricas.
    n_auditado = len(auditorias)
    n_rejeitadas = sum(1 for a in auditorias if a["rejeitada"])
    pct_rejeitadas = n_rejeitadas / n_auditado if n_auditado > 0 else 0
    coerencia_media = sum(a["coerencia"] for a in auditorias) / n_auditado if n_auditado > 0 else 0
    passed = pct_rejeitadas < 0.10

    output = {
        "auditor_model": auditor_model,
        "n_auditado": n_auditado,
        "n_rejeitadas": n_rejeitadas,
        "pct_rejeitadas": round(pct_rejeitadas, 4),
        "coerencia_media": round(coerencia_media, 4),
        "criterio": "pct_rejeitadas < 10%",
        "passed": passed,
        "auditorias": auditorias,
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[AUDIT] coerencia_media={coerencia_media:.2f} rejeitadas={n_rejeitadas}/{n_auditado} ({pct_rejeitadas:.1%}) -> {output_path}")
    return output


def main():
    parser = argparse.ArgumentParser(description="Auditoria de coerencia do Simulation Army v2")
    parser.add_argument("--ensemble", default="results_v2/ensemble_n30_s42.json")
    parser.add_argument("--auditor", default="command-r-plus-08-2024")
    parser.add_argument("--sample-pct", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="results_v2/auditoria_coerencia.json")
    args = parser.parse_args()
    result = asyncio.run(run_audit(args.ensemble, args.auditor, args.sample_pct, args.seed, args.output))
    print(json.dumps({
        "coerencia_media": result["coerencia_media"],
        "pct_rejeitadas": result["pct_rejeitadas"],
        "passed": result["passed"],
    }, indent=2))


if __name__ == "__main__":
    main()
