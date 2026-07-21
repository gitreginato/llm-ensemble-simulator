"""Baseline de modelo unico para o Simulation Army v2.

Roda o cenario SLZ-C com 1 modelo so (sem ensemble) para servir de baseline
de comparacao. 3 baselines: gpt-4o, DeepSeek-V3.1, llama-3.3-70b-versatile.

Reusa generate_personas do advanced_simulation para gerar as mesmas personas
(mesma seed) em todos os baselines, garantindo comparacao justa.
"""
import argparse
import asyncio
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Any

import httpx

# Reusa gerador de personas do motor existente.
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.advanced_simulation import BusinessProfile, generate_personas  # noqa: E402

from simulation_army_v2.config import load_config  # noqa: E402
from simulation_army_v2.schema import DecisaoPersona  # noqa: E402

GOCAT_URL = os.getenv("GOCAT_BASE_URL", "http://127.0.0.1:8080")
GOCAT_KEY = os.getenv("GOCAT_API_KEY", "local-dev-key-change-me")

SYSTEM_PROMPT = (
    "You are a realistic Brazilian small-business decision simulator for Sao Luis, MA. "
    "Simulate how each owner would ACTUALLY react to a security offer via WhatsApp referral. "
    "Be realistic: some will schedule (especially if recent theft, valuable stock, or weak existing security), "
    "most will not. Aim for 5-10% scheduling rate overall. "
    "Return ONLY valid JSON. No markdown, no preamble."
)

USER_PROMPT_TEMPLATE = """## Business Owner Profile
- Name: {owner_name}
- Age: {age}
- Business: {business_name} ({segment})
- Monthly revenue: R$ {revenue:,.2f}
- Profit margin: {margin:.0%}
- Security budget: R$ {sec_budget:,.2f}
- Existing security: {existing_security} (satisfaction {satisfaction}/10)
- Risk profile: {risk_profile}
- Decision maker: {decision_maker}
- Day of month: {day_of_month}
- Season: {season}
- Bairro: {bairro}
- Recent event: {recent_event}
- Tech savviness: {tech_savviness}/10
- Trust in local providers: {trust_local}/10
- WTP for security: R$ {wtp:,.2f}

## Offer
- Product: {product_name}
- Description: {description}
- Price: R$ {price_brl:,.2f} (visit)
- Channel: {channel}
- Value proposition: {value_proposition}
- Pain focus: {pain_focus}

## Task
Return ONLY a JSON object with exactly these fields:
{{
  "decisao": "visualizou" | "clicou" | "agendou" | "ignorou",
  "wtp": float,
  "sentimento": float,
  "objecoes": ["budget" | "timing" | "existing_solution" | "skepticism" | "complexity" | "need_lack"],
  "confianca": float,
  "raciocinio": "1-3 frases em portugues"
}}

IMPORTANT: sentimento and confianca MUST be in range -1.0 to 1.0 (not 0-10).

Rules:
- "ignorou" = nem visualizou a mensagem. Expect 15-35% to ignore.
- "visualizou" = viu mas nao clicou.
- "clicou" = clicou mas nao agendou.
- "agendou" = scheduled the visit (conversao final). Expect 5-10% to schedule.
- Owners with recent_event "theft" AND weak existing security (none/diy_cameras) are MORE likely to schedule.
- Owners with existing security satisfaction >= 7 usually do NOT schedule (existing_solution objection).
- If price > WTP, objecoes must include "budget".
- If day_of_month > 25 AND season != high, "timing" is a common objection.
- crisis_driven risk profile with recent theft: high chance to schedule.
- conservative risk profile: needs trust, often schedules only if trust_local >= 7.
- raciocinio in Portuguese, 1-3 sentences.
"""


USER_PROMPT_TEMPLATE_V5 = """## Business Owner Profile
- Name: {owner_name}
- Gender: {gender}
- Business: {segment} ({segment_porte}, {segment_perene})
- Bairro: {bairro} (risco: {bairro_risco}, perfil: {bairro_perfil})
- Monthly revenue: R$ {revenue_mensal:,.2f} (season: {season}, multiplier: {season_revenue_multiplier})
- Profit margin: {margin:.0%}
- Security budget: R$ {budget_mensal_seguranca:,.2f}
- Existing security: {has_existing_security} (satisfaction {existing_security_satisfaction}/10)
- Risk profile: {risk_profile}
- Recent event: {recent_event}
- Decision maker: {decision_maker}
- Tech savviness: {tech_savviness}/10
- Trust in local providers: {trust_local_providers}/10
- WTP for security: R$ {wtp_brl:,.2f}

## EMIVE Offer (franquia em Sao Luis-MA)
- Product: {product_name}
- Description: {description}
- Mensalidade: R$ {mensalidade_emive:,.2f}/mes (contrato {contrato_meses} meses, multa proporcional)
- Ticket medio 36 meses: R$ {ticket_medio_36m:,.2f}
- Visita tecnica gratuita: R$ {price_brl:,.2f}
- Channel: {channel}
- Value proposition: {value_proposition}
- Pain focus: {pain_focus}

## Limitacoes EMIVE
- Cobertura: apenas area interna (cameras e sensores dentro do estabelecimento)
- {area_externa_nota}
- {concorrencia_nota}

## Task
Return ONLY a JSON object with exactly these fields:
{{
  "decisao": "visualizou" | "clicou" | "agendou" | "ignorou",
  "wtp": float,
  "sentimento": float,
  "objecoes": ["budget" | "timing" | "existing_solution" | "skepticism" | "complexity" | "need_lack" | "area_externa" | "concorrencia_local" | "contract_fear" | "ticket_alto"],
  "confianca": float,
  "raciocinio": "1-3 frases em portugues"
}}

IMPORTANT: sentimento and confianca MUST be in range -1.0 to 1.0 (not 0-10).

Rules:
- "ignorou" = nem visualizou a mensagem. Expect 15-35% to ignore.
- "visualizou" = viu mas nao clicou.
- "clicou" = clicou mas nao agendou.
- "agendou" = scheduled the visit (conversao final). Expect 5-15% to schedule.
- Owners with recent_event "theft" AND weak existing security are MORE likely to schedule.
- Owners with existing security satisfaction >= 7 usually do NOT schedule (existing_solution objection).
- If mensalidade > WTP, objecoes must include "budget".
- If precisa_area_externa=True, objecoes must include "area_externa" (EMIVE so cobre area interna).
- If concorrencia_local_instalada=True, objecoes must include "concorrencia_local".
- If segment_perene=False (volatil), "contract_fear" e comum (contrato 36 meses assusta).
- If ticket_medio_36m > wtp_brl * 12, "ticket_alto" e comum.
- raciocinio in Portuguese, 1-3 sentences.
"""


def _profile_v5_to_prompt_kwargs(p, cfg: Any) -> dict:
    """Mapeia PersonaV5 para os placeholders do USER_PROMPT_TEMPLATE_V5."""
    area_nota = (
        "ATENCAO: este negocio PRECISA de cobertura externa (vitrine, patio, estacionamento)."
        if p.precisa_area_externa
        else "Este negocio nao precisa de cobertura externa."
    )
    conc_nota = (
        "ATENCAO: ja existem 20-30 instaladores de seguranca atuando neste bairro."
        if p.concorrencia_local_instalada
        else "Concorrencia local baixa neste bairro."
    )
    return {
        "owner_name": p.owner_name,
        "gender": p.gender,
        "segment": p.segment,
        "segment_porte": p.segment_porte,
        "segment_perene": "perene" if p.segment_perene else "volatil",
        "bairro": p.bairro,
        "bairro_risco": p.bairro_risco,
        "bairro_perfil": p.bairro_perfil,
        "revenue_mensal": p.revenue_mensal,
        "season": p.season,
        "season_revenue_multiplier": p.season_revenue_multiplier,
        "margin": p.margin,
        "budget_mensal_seguranca": p.budget_mensal_seguranca,
        "has_existing_security": p.has_existing_security,
        "existing_security_satisfaction": p.existing_security_satisfaction,
        "risk_profile": p.risk_profile,
        "recent_event": p.recent_event,
        "decision_maker": p.decision_maker,
        "tech_savviness": p.tech_savviness,
        "trust_local_providers": p.trust_local_providers,
        "wtp_brl": p.wtp_brl,
        "product_name": cfg.scenario.product_name,
        "description": cfg.scenario.description,
        "mensalidade_emive": p.mensalidade_emive,
        "contrato_meses": 36,
        "ticket_medio_36m": p.ticket_medio_36m,
        "price_brl": cfg.scenario.price_brl,
        "channel": cfg.scenario.channel,
        "value_proposition": cfg.scenario.value_proposition,
        "pain_focus": cfg.scenario.pain_focus,
        "area_externa_nota": area_nota,
        "concorrencia_nota": conc_nota,
    }


def _profile_to_prompt_kwargs(p: BusinessProfile, cfg: Any) -> dict:
    return {
        "owner_name": p.owner_name,
        "age": p.age,
        "business_name": p.business_name,
        "segment": p.segment,
        "revenue": p.monthly_revenue_brl,
        "margin": p.profit_margin_pct,
        "sec_budget": p.security_budget_brl,
        "existing_security": p.has_existing_security,
        "satisfaction": p.existing_security_satisfaction,
        "risk_profile": p.risk_profile,
        "decision_maker": p.decision_maker,
        "day_of_month": p.day_of_month,
        "season": p.season,
        "bairro": p.location_bairro,
        "recent_event": p.recent_event,
        "tech_savviness": p.tech_savviness,
        "trust_local": p.trust_local_providers,
        "wtp": p.wtp_brl,
        "product_name": cfg.scenario.product_name,
        "description": cfg.scenario.description,
        "price_brl": cfg.scenario.price_brl,
        "channel": cfg.scenario.channel,
        "value_proposition": cfg.scenario.value_proposition,
        "pain_focus": cfg.scenario.pain_focus,
    }


def _parse_json_response(content: str) -> dict:
    """Extrai JSON da resposta do LLM (pode ter code fences, texto extra, ou thinking)."""
    text = content.strip()
    # Remover code fences se presentes.
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
    text = text.strip()
    # Tenta regex para JSON completo (suporta JSON aninhado).
    import re
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if json_match:
        json_str = json_match.group(0)
    else:
        # Fallback original: primeiro { e ultimo }.
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError(f"JSON nao encontrado em: {content[:200]}")
        json_str = text[start : end + 1]
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        # JSON truncado: tentar reparar fechando chaves/colchetes abertos.
        try:
            data = json.loads(json_str + "}")
        except json.JSONDecodeError:
            try:
                # Contar chaves/colchetes abertos e fechar.
                opens = json_str.count("{") - json_str.count("}")
                brackets = json_str.count("[") - json_str.count("]")
                repaired = json_str + ("]" * max(0, brackets)) + ("}" * max(0, opens))
                data = json.loads(repaired)
            except json.JSONDecodeError:
                # Ultima tentativa: extrair campos com regex.
                import re
                fields = {}
                for field in ["decisao", "wtp", "sentimento", "confianca", "raciocinio"]:
                    m = re.search(rf'"{field}"\s*:\s*["\[]?([^",\]}}]+)', json_str)
                    if m:
                        val = m.group(1).strip().strip('"')
                        try:
                            fields[field] = float(val) if field in ("wtp", "sentimento", "confianca") else val
                        except ValueError:
                            fields[field] = val
                if "decisao" not in fields:
                    raise ValueError(f"JSON nao parseado em: {content[:200]}")
                data = fields
    # LLMs frequentemente retornam sentimento/confianca em escala 0-10 em vez de 0-1.
    # Clampar para o range valido do schema (dividir por 10 sempre, nao por -10).
    for field in ("sentimento", "confianca"):
        if field in data and isinstance(data[field], (int, float)):
            v = float(data[field])
            if abs(v) > 1.0:
                data[field] = v / 10.0
            data[field] = max(-1.0, min(1.0, data[field])) if field == "sentimento" else max(0.0, min(1.0, data[field]))
    # Mapear variantes comuns de decisao para o enum valido.
    DECISAO_MAP = {
        "scheduled": "agendou", "yes": "agendou", "comprou": "agendou", "agendamento": "agendou",
        "clicked": "clicou", "click": "clicou", "visit": "visualizou",
        "viewed": "visualizou", "view": "visualizou", "saw": "visualizou",
        "ignored": "ignorou", "ignore": "ignorou", "no": "ignorou", "skip": "ignorou",
    }
    if "decisao" in data and isinstance(data["decisao"], str):
        d = data["decisao"].strip().lower()
        if d not in ("visualizou", "clicou", "agendou", "ignorou"):
            data["decisao"] = DECISAO_MAP.get(d, data["decisao"])
    # Mapear variantes comuns de objecoes.
    OBJECAO_MAP = {
        "price": "budget", "cost": "budget", "expensive": "budget", "orcamento": "budget",
        "time": "timing", "schedule": "timing", "momento": "timing",
        "existing": "existing_solution", "current": "existing_solution", "atual": "existing_solution",
        "trust": "skepticism", "duvida": "skepticism", "desconfianca": "skepticism",
        "hard": "complexity", "difficult": "complexity", "complexo": "complexity",
        "no_need": "need_lack", "unnecessary": "need_lack", "desnecessario": "need_lack",
    }
    if "objecoes" in data and isinstance(data["objecoes"], list):
        data["objecoes"] = [
            OBJECAO_MAP.get(o.strip().lower(), o) if isinstance(o, str) else o
            for o in data["objecoes"]
        ]
    return data


async def _call_model(
    client: httpx.AsyncClient, model: str, user_prompt: str
) -> tuple[DecisaoPersona, dict]:
    """Chama 1 modelo via gocat e retorna (DecisaoPersona, metadados).

    metadados: latency_ms, http_status, prompt_tokens, completion_tokens,
    total_tokens, provider_used (gocat).
    """
    import time as _t
    t0 = _t.monotonic()
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 2000,
        "temperature": 0.7,
    }
    headers = {"Authorization": f"Bearer {GOCAT_KEY}", "Content-Type": "application/json"}
    last_status = None
    for attempt in range(3):
        try:
            r = await client.post(
                f"{GOCAT_URL}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=60,
            )
            last_status = r.status_code
            latency_ms = int((_t.monotonic() - t0) * 1000)
            if r.status_code == 200:
                data = r.json()
                if "choices" not in data or not data["choices"]:
                    raise ValueError(f"API response missing choices: {str(data)[:200]}")
                msg = data["choices"][0].get("message", {})
                content = msg.get("content") or ""
                # Modelos de raciocinio (GLM, Qwen) podem colocar output em reasoning_content.
                if not content and msg.get("reasoning_content"):
                    content = msg["reasoning_content"]
                if not content:
                    raise ValueError("Both content and reasoning_content are empty")
                parsed = _parse_json_response(content)
                parsed["modelo"] = model
                decisao = DecisaoPersona(**parsed)
                usage = data.get("usage", {}) or {}
                meta = {
                    "latency_ms": latency_ms,
                    "http_status": 200,
                    "prompt_tokens": usage.get("prompt_tokens"),
                    "completion_tokens": usage.get("completion_tokens"),
                    "total_tokens": usage.get("total_tokens"),
                    "provider_used": "gocat",
                }
                return decisao, meta
            if r.status_code >= 500 and attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            if r.status_code == 429 and attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
        except (httpx.HTTPError, json.JSONDecodeError, ValueError) as e:
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError(f"modelo {model}: 3 tentativas falharam (last_status={last_status})")


async def run_baseline(
    config_path: str, model: str, n: int, seed: int, output_path: str
) -> dict:
    """Roda baseline com 1 modelo para N personas."""
    cfg = load_config(config_path)
    random.seed(seed)
    personas = generate_personas(cfg.scenario.target_segment, n)
    if not personas:
        raise ValueError(f"generate_personas retornou lista vazia para segmento {cfg.scenario.target_segment}")

    print(f"[BASELINE] modelo={model} n={n} seed={seed}")
    results = []
    falhas = 0
    async with httpx.AsyncClient() as client:
        for i, p in enumerate(personas, 1):
            user_prompt = USER_PROMPT_TEMPLATE.format(**_profile_to_prompt_kwargs(p, cfg))
            try:
                decisao, meta = await _call_model(client, model, user_prompt)
                row = decisao.model_dump()
                row["meta"] = meta
                results.append(row)
                print(f"  [{i}/{n}] {p.owner_name}: {decisao.decisao} (wtp={decisao.wtp}) latency={meta['latency_ms']}ms tokens={meta.get('total_tokens')}")
            except Exception as e:
                print(f"  [{i}/{n}] {p.owner_name}: FAIL {e}")
                results.append({"modelo": model, "erro": str(e), "decisao": "ignorou", "_falha": True})
                falhas += 1
            await asyncio.sleep(cfg.execution.delay_between_personas_seconds)

    # Calcula taxa de conversao: exclui falhas do denominador.
    sucessos = len(results) - falhas
    agendaram = sum(1 for r in results if r.get("decisao") == "agendou" and not r.get("_falha"))
    conversao = agendaram / sucessos if sucessos > 0 else 0

    output = {
        "modelo": model,
        "n": n,
        "seed": seed,
        "cenario": cfg.scenario.code,
        "taxa_conversao": conversao,
        "agendaram": agendaram,
        "falhas": falhas,
        "sucessos": sucessos,
        "decisoes": results,
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[BASELINE] conversao={conversao:.1%} ({agendaram}/{n}) -> {output_path}")
    return output


def main():
    parser = argparse.ArgumentParser(description="Baseline modelo unico")
    parser.add_argument("--scenario", default="scenarios_v2/slz-c-army.yaml")
    parser.add_argument("--model", required=True, help="gpt-4o | DeepSeek-V3.1 | llama-3.3-70b-versatile")
    parser.add_argument("--n", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    if args.output is None:
        safe = args.model.replace("/", "_").replace(".", "_")
        args.output = f"results_v2/baseline_{safe}_n{args.n}_s{args.seed}.json"

    out = asyncio.run(run_baseline(args.scenario, args.model, args.n, args.seed, args.output))
    print(json.dumps({"taxa_conversao": out["taxa_conversao"], "agendaram": out["agendaram"], "n": out["n"]}, indent=2))


if __name__ == "__main__":
    main()
