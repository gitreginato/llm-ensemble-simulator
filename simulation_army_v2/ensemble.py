"""Pipeline do Simulation Army v2: ensemble heterogeneo com sintetizador de consenso.

Para cada persona:
1. Fan-out: 3 modelos processam a persona (sequencial para evitar rate limit do gocat)
2. Sintetizador: 1 modelo agrega as 3 respostas em DecisaoAggregada
3. Metricas: divergence_score, pairwise disagreement, IC95%

Output: 1 JSON por run com N personas x (3 decisoes + 1 agregada).
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
from scipy.stats import beta

# Reusa gerador de personas e helpers do baseline.
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.advanced_simulation import BusinessProfile, generate_personas  # noqa: E402
from simulation_army_v2.personas_v5 import generate_personas_v5  # noqa: E402

from simulation_army_v2.baseline import (  # noqa: E402
    GOCAT_KEY,
    GOCAT_URL,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    USER_PROMPT_TEMPLATE_V5,
    _call_model,
    _parse_json_response,
    _profile_to_prompt_kwargs,
    _profile_v5_to_prompt_kwargs,
)
from simulation_army_v2.kilocode_adapter import call_kilocode  # noqa: E402
from simulation_army_v2.devin_adapter import call_devin  # noqa: E402
from simulation_army_v2.cline_adapter import call_cline  # noqa: E402
from simulation_army_v2.ollama_adapter import call_ollama  # noqa: E402
from simulation_army_v2.costs import calculate_run_cost  # noqa: E402
from simulation_army_v2.config import load_config  # noqa: E402
from simulation_army_v2.schema import (  # noqa: E402
    ConcordanciaPar,
    DecisaoAggregada,
    DecisaoPersona,
    divergence_score_from_decisoes,
)

# Circuit breaker e backoff constants.
CIRCUIT_THRESHOLD = 5  # 5 falhas consecutivas = abre circuito
CIRCUIT_COOLDOWN = 300  # 5 minutos cooldown em segundos
SOURCE_BACKOFF_DECAY_SECONDS = 300  # 5 minutos para resetar backoff

SYNTH_PROMPT_TEMPLATE = """## Contexto
Voce e um sintetizador de consenso. {n_modelos} modelos de IA diferentes simularam a decisao
de um dono de loja face a uma oferta de seguranca. Sua tarefa e agregar as {n_modelos} respostas
em uma decisao unica e coerente.

## Perfil do dono
- Nome: {owner_name}
- Negocio: {business_name} ({segment})

## Respostas dos {n_modelos} modelos
{respostas_formatadas}

## Tarefa
Retorne APENAS um JSON com exatamente estes campos:
{{
  "decisao_final": "visualizou" | "clicou" | "agendou" | "ignorou",
  "wtp_medio": float,
  "sentimento_medio": float,
  "objecoes_consolidadas": ["budget" | "timing" | "existing_solution" | "skepticism" | "complexity" | "need_lack" | "area_externa" | "concorrencia_local" | "contract_fear" | "ticket_alto"],
  "divergence_score": float,
  "concordancia": [{{"modelo_a": "x", "modelo_b": "y", "concordam": true}}],
  "confianca_agregada": float,
  "raciocinio_sintese": "2-4 frases em portugues explicando o consenso"
}}

Regras:
- decisao_final: escolha a decisao que melhor representa o consenso. Se 2+ modelos
  concordam, use essa. Se todos discordam, use a mais conservadora (menor no funil).
- wtp_medio: media dos WTPs de todos os modelos.
- sentimento_medio: media dos sentimentos de todos os modelos.
- objecoes_consolidadas: uniao das objecoes de todos os modelos (sem duplicatas).
- divergence_score: 0 se todos concordam, 1 se todos discordam.
- concordancia: liste todos os pares com concordam=true/false.
- confianca_agregada: media das confiancas de todos os modelos.
- sentimento e confianca em escala -1 a 1 (NAO 0-10).
"""


def _format_respostas(decisoes: list[DecisaoPersona]) -> str:
    """Formata as 3 decisoes para o prompt do sintetizador."""
    lines = []
    for d in decisoes:
        lines.append(
            f"### {d.modelo}\n"
            f"- decisao: {d.decisao}\n"
            f"- wtp: R$ {d.wtp:.2f}\n"
            f"- sentimento: {d.sentimento:.2f}\n"
            f"- objecoes: {d.objecoes}\n"
            f"- confianca: {d.confianca:.2f}\n"
            f"- raciocinio: {d.raciocinio}\n"
        )
    return "\n".join(lines)


def _compute_concordancia(decisoes: list[DecisaoPersona]) -> list[ConcordanciaPar]:
    """Computa concordancia pairwise entre os 3 modelos."""
    pairs = []
    for i in range(len(decisoes)):
        for j in range(i + 1, len(decisoes)):
            pairs.append(
                ConcordanciaPar(
                    modelo_a=decisoes[i].modelo,
                    modelo_b=decisoes[j].modelo,
                    concordam=decisoes[i].decisao == decisoes[j].decisao,
                )
            )
    return pairs


def _ic95(conversao: float, n: int) -> tuple[float, float]:
    """IC95% via distribuicao Beta (metodo exato, melhor que normal approx para n pequeno)."""
    if n == 0:
        return 0.0, 1.0
    import math
    try:
        lo = beta.ppf(0.025, conversao * n + 0.5, (1 - conversao) * n + 0.5)
        hi = beta.ppf(0.975, conversao * n + 0.5, (1 - conversao) * n + 0.5)
        if math.isnan(lo) or math.isnan(hi):
            raise ValueError("NaN from beta.ppf")
        return float(lo), float(hi)
    except Exception:
        # Fallback: normal approximation.
        import statistics
        sd = statistics.stdev([1] * int(conversao * n) + [0] * (n - int(conversao * n))) if n > 1 else 0.5
        se = sd / math.sqrt(n)
        return max(0.0, conversao - 1.96 * se), min(1.0, conversao + 1.96 * se)


async def _call_synthesizer(
    client: httpx.AsyncClient,
    model: str,
    owner_name: str,
    business_name: str,
    segment: str,
    decisoes: list[DecisaoPersona],
) -> DecisaoAggregada:
    """Chama o sintetizador para agregar as 3 decisoes."""
    respostas = _format_respostas(decisoes)
    prompt = SYNTH_PROMPT_TEMPLATE.format(
        n_modelos=len(decisoes),
        owner_name=owner_name,
        business_name=business_name,
        segment=segment,
        respostas_formatadas=respostas,
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a consensus synthesizer. Return ONLY valid JSON."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 2000,
        "temperature": 0.3,
    }
    headers = {"Authorization": f"Bearer {GOCAT_KEY}", "Content-Type": "application/json"}
    for attempt in range(3):
        try:
            r = await client.post(
                f"{GOCAT_URL}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=90,
            )
            if r.status_code == 200:
                data = r.json()
                if "choices" not in data or not data["choices"]:
                    raise ValueError(f"synthesizer missing choices: {str(data)[:200]}")
                msg = data["choices"][0].get("message", {})
                content = msg.get("content") or ""
                if not content and msg.get("reasoning_content"):
                    content = msg["reasoning_content"]
                if not content:
                    # Tenta campos alternativos antes de falhar.
                    content = msg.get("text") or ""
                if not content:
                    content = msg.get("output") or ""
                if not content:
                    raise ValueError("synthesizer: content, reasoning_content, text and output empty")
                parsed = _parse_json_response(content)
                # Normaliza campos medio/agregado que o LLM pode retornar em escala 0-10.
                for field in ("sentimento_medio", "confianca_agregada"):
                    if field in parsed and isinstance(parsed[field], (int, float)):
                        v = float(parsed[field])
                        if abs(v) > 1.0:
                            parsed[field] = v / 10.0
                        if field == "sentimento_medio":
                            parsed[field] = max(-1.0, min(1.0, parsed[field]))
                        else:
                            parsed[field] = max(0.0, min(1.0, parsed[field]))
                # Mapear decisao_final e objecoes_consolidadas (variantes comuns).
                DECISAO_MAP = {
                    "scheduled": "agendou", "yes": "agendou", "comprou": "agendou",
                    "clicked": "clicou", "click": "clicou", "viewed": "visualizou",
                    "view": "visualizou", "saw": "visualizou", "ignored": "ignorou",
                    "ignore": "ignorou", "no": "ignorou", "skip": "ignorou",
                }
                if "decisao_final" in parsed and isinstance(parsed["decisao_final"], str):
                    d = parsed["decisao_final"].strip().lower()
                    if d not in ("visualizou", "clicou", "agendou", "ignorou"):
                        parsed["decisao_final"] = DECISAO_MAP.get(d, parsed["decisao_final"])
                OBJECAO_MAP = {
                    "price": "budget", "cost": "budget", "expensive": "budget", "orcamento": "budget",
                    "time": "timing", "schedule": "timing", "momento": "timing",
                    "existing": "existing_solution", "current": "existing_solution", "atual": "existing_solution",
                    "trust": "skepticism", "duvida": "skepticism", "desconfianca": "skepticism",
                    "hard": "complexity", "difficult": "complexity", "complexo": "complexity",
                    "no_need": "need_lack", "unnecessary": "need_lack", "desnecessario": "need_lack",
                }
                if "objecoes_consolidadas" in parsed and isinstance(parsed["objecoes_consolidadas"], list):
                    parsed["objecoes_consolidadas"] = [
                        OBJECAO_MAP.get(o.strip().lower(), o) if isinstance(o, str) else o
                        for o in parsed["objecoes_consolidadas"]
                    ]
                # Concordancia: sempre computar localmente (LLM pode errar nomes).
                parsed["concordancia"] = [
                    {"modelo_a": p.modelo_a, "modelo_b": p.modelo_b, "concordam": p.concordam}
                    for p in _compute_concordancia(decisoes)
                ]
                if "divergence_score" not in parsed:
                    parsed["divergence_score"] = divergence_score_from_decisoes(decisoes)
                if "decisao_final" not in parsed:
                    # Mais conservadora (menor no funil) entre as 3.
                    rank = {"ignorou": 0, "visualizou": 1, "clicou": 2, "agendou": 3}
                    parsed["decisao_final"] = min((d.decisao for d in decisoes), key=lambda x: rank.get(x, 0))
                if "wtp_medio" not in parsed:
                    parsed["wtp_medio"] = sum(d.wtp for d in decisoes) / len(decisoes)
                if "sentimento_medio" not in parsed:
                    parsed["sentimento_medio"] = sum(d.sentimento for d in decisoes) / len(decisoes)
                if "confianca_agregada" not in parsed:
                    parsed["confianca_agregada"] = sum(d.confianca for d in decisoes) / len(decisoes)
                if "objecoes_consolidadas" not in parsed:
                    seen = set()
                    parsed["objecoes_consolidadas"] = [
                        o for d in decisoes for o in d.objecoes
                        if not (o in seen or seen.add(o))
                    ]
                if "raciocinio_sintese" not in parsed:
                    parsed["raciocinio_sintese"] = "Sintese automatica: " + ", ".join(d.decisao for d in decisoes)
                return DecisaoAggregada(**parsed)
            if r.status_code >= 500 and attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            if r.status_code == 429 and attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"synthesizer HTTP {r.status_code}: {r.text[:200]}")
        except (httpx.HTTPError, json.JSONDecodeError, ValueError) as e:
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError(f"synthesizer: 3 tentativas falharam")


def _save_checkpoint(output_path, cfg, n, seed, ensemble_models, synth_model,
                     results, falhas):
    """Salva JSON parcial a cada persona. Permite retomar apos interrupcao."""
    decisoes_finais = [
        r["decisao_agregada"]["decisao_final"]
        for r in results
        if r.get("decisao_agregada")
    ]
    agendaram = sum(1 for d in decisoes_finais if d == "agendou")
    sucessos = len(decisoes_finais)
    conversao = agendaram / sucessos if sucessos > 0 else 0
    ic_lo, ic_hi = _ic95(conversao, sucessos)
    divergence_scores = [
        r["decisao_agregada"]["divergence_score"]
        for r in results
        if r.get("decisao_agregada")
    ]
    div_media = sum(divergence_scores) / len(divergence_scores) if divergence_scores else 0
    todos_metadados = []
    for r in results:
        todos_metadados.extend(r.get("metadados_modelos", []))
    custos = calculate_run_cost(todos_metadados)
    partial = {
        "cenario": cfg.scenario.code,
        "n": n,
        "seed": seed,
        "personas_completas": len(results),
        "modelos": [m[0] for m in ensemble_models],
        "sintetizador": synth_model,
        "taxa_conversao": conversao,
        "agendaram": agendaram,
        "sucessos": sucessos,
        "falhas": falhas,
        "ic95": [ic_lo, ic_hi],
        "divergence_score_medio": div_media,
        "custo_total_usd": custos["custo_total_usd"],
        "custo_por_modelo": custos["custo_por_modelo"],
        "personas": results,
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(partial, f, ensure_ascii=False, indent=2)
    os.replace(tmp, output_path)


async def run_ensemble(
    config_path: str, n: int, seed: int, output_path: str
) -> dict:
    """Roda o ensemble completo: N modelos + sintetizador para N personas.

    Suporta persona_version v4 (default, generate_personas) e v5 (generate_personas_v5
    com bairros reais, mensalidade, limitacoes EMIVE).
    """
    cfg = load_config(config_path)
    random.seed(seed)
    # Detectar versao de personas do cenario (default: v4).
    persona_version = getattr(cfg.scenario, "persona_version", "v4")
    mes = getattr(cfg.execution, "mes", 7)

    if persona_version == "v5":
        personas = generate_personas_v5(
            n=n,
            segment=cfg.scenario.target_segment if cfg.scenario.target_segment != "all" else None,
            mes=mes,
            seed=seed,
        )
        prompt_template = USER_PROMPT_TEMPLATE_V5
        prompt_fn = _profile_v5_to_prompt_kwargs
        print(f"[ENSEMBLE] personas V5: {len(personas)} personas, bairros reais, mensalidade EMIVE")
    else:
        personas = generate_personas(cfg.scenario.target_segment, n)
        prompt_template = USER_PROMPT_TEMPLATE
        prompt_fn = _profile_to_prompt_kwargs

    if not personas:
        raise ValueError(f"generate_personas retornou lista vazia para segmento {cfg.scenario.target_segment}")

    ensemble_models = [(m.model, m.role, m.source) for m in cfg.ensemble.models]
    synth_model = cfg.synthesizer.model

    print(f"[ENSEMBLE] n={n} seed={seed} persona={persona_version} modelos={[m[0] for m in ensemble_models]} synth={synth_model}")
    results = []
    falhas = 0
    # Backoff por source: 1.0 = normal, 2.0/4.0/8.0 = backoff apos falhas.
    source_backoff: dict[str, float] = {}
    # Circuit breaker por source: contador de falhas consecutivas e timestamp de reabertura.
    source_fail_count: dict[str, int] = {}
    source_circuit_open_until: dict[str, float] = {}
    # Timestamp da ultima falha por source (para decay do backoff).
    source_last_fail: dict[str, float] = {}

    async with httpx.AsyncClient() as client:
        for i, p in enumerate(personas, 1):
            user_prompt = prompt_template.format(**prompt_fn(p, cfg))

            # Shuffle dos modelos a cada persona para distribuir carga entre providers.
            # Evita que o mesmo provider receba N requests seguidos (rate limit 503).
            # Ponytail: shuffle simples em vez de round-robin complexo.
            models_this_persona = ensemble_models[:]
            random.shuffle(models_this_persona)

            # Fan-out: N modelos processam a persona (sequencial para evitar rate limit).
            # source=gocat -> HTTP via gocat; source=kilocode -> subprocess CLI.
            # Delay adaptativo: se source retornou 503/429 na ultima persona,
            # dobra o delay para essa source na proxima (backoff simples).
            decisoes_persona = []
            metadados_modelos = []
            for model_name, role, source in models_this_persona:
                now = time.monotonic()

                # Circuit breaker: se circuito estiver aberto, skip essa source.
                if source in source_circuit_open_until and now < source_circuit_open_until[source]:
                    print(f"  [{i}/{n}] {p.owner_name} [{role}] ({source}): SKIP (circuit open until {source_circuit_open_until[source]:.0f})")
                    metadados_modelos.append({
                        "modelo": model_name,
                        "role": role,
                        "source": source,
                        "erro": "circuit breaker open",
                    })
                    continue

                # Backoff decay: se passou 300s desde a ultima falha, reseta backoff.
                if source in source_last_fail and (now - source_last_fail[source]) > SOURCE_BACKOFF_DECAY_SECONDS:
                    source_backoff[source] = 1.0

                # Delay adaptativo: se essa source falhou na persona anterior,
                # aplica backoff (2x o delay base) antes de chamar.
                base_delay = cfg.execution.delay_between_models_seconds
                adaptive_delay = base_delay * source_backoff.get(source, 1.0)
                if adaptive_delay > base_delay:
                    await asyncio.sleep(adaptive_delay - base_delay)
                try:
                    if source == "kilocode":
                        d, meta = await call_kilocode(
                            model_name, user_prompt,
                            timeout=cfg.execution.kilocode_timeout_seconds
                        )
                    elif source == "devin":
                        d, meta = await call_devin(
                            model_name, user_prompt,
                            timeout=cfg.execution.devin_timeout_seconds
                        )
                    elif source == "cline":
                        d, meta = await call_cline(
                            model_name, user_prompt,
                            timeout=cfg.execution.cline_timeout_seconds
                        )
                    elif source == "ollama":
                        d, meta = await call_ollama(model_name, user_prompt, client=client)
                    else:
                        d, meta = await _call_model(client, model_name, user_prompt)
                    decisoes_persona.append(d)
                    metadados_modelos.append({
                        "modelo": model_name,
                        "role": role,
                        "source": source,
                        **meta,
                    })
                    # Sucesso: reseta backoff e contador de falhas dessa source.
                    source_backoff[source] = 1.0
                    source_fail_count[source] = 0
                    print(f"  [{i}/{n}] {p.owner_name} [{role}] ({source}): {d.decisao} latency={meta.get('latency_ms')}ms tokens={meta.get('total_tokens')}")
                except Exception as e:
                    err_str = str(e)[:200]
                    metadados_modelos.append({
                        "modelo": model_name,
                        "role": role,
                        "source": source,
                        "erro": err_str,
                    })
                    # Falha: aumenta backoff dessa source (max 8x).
                    source_backoff[source] = min(source_backoff.get(source, 1.0) * 2.0, 8.0)
                    # Circuit breaker: incrementa contador e abre se >= threshold.
                    source_fail_count[source] = source_fail_count.get(source, 0) + 1
                    if source_fail_count[source] >= CIRCUIT_THRESHOLD:
                        source_circuit_open_until[source] = now + CIRCUIT_COOLDOWN
                        print(f"  [{i}/{n}] {p.owner_name} [{role}] ({source}): CIRCUIT OPEN ({source_fail_count[source]} falhas)")
                    # Timestamp da ultima falha (para decay).
                    source_last_fail[source] = now
                    print(f"  [{i}/{n}] {p.owner_name} [{role}] ({source}): FAIL {e} (backoff={source_backoff[source]:.1f}x)")
                    falhas += 1
                await asyncio.sleep(base_delay)

            # Sintetizador: agrega as N decisoes (requer pelo menos 1 decisao).
            # PersonaV5 nao tem business_name; usar segment como fallback.
            _business_name = getattr(p, "business_name", p.segment)
            agregada = None
            if len(decisoes_persona) >= 1:
                try:
                    agregada = await _call_synthesizer(
                        client, synth_model, p.owner_name, _business_name, p.segment, decisoes_persona
                    )
                    print(f"  [{i}/{n}] {p.owner_name} [SYNTH]: {agregada.decisao_final} div={agregada.divergence_score:.2f}")
                except Exception as e:
                    # Fallback: agregacao simples das decisoes (sintetizador falhou).
                    print(f"  [{i}/{n}] {p.owner_name} [SYNTH]: FAIL {e} -> usando fallback")
                    rank = {"ignorou": 0, "visualizou": 1, "clicou": 2, "agendou": 3}
                    decisao_final = min((d.decisao for d in decisoes_persona), key=lambda x: rank.get(x, 0))
                    wtp_medio = sum(d.wtp for d in decisoes_persona) / len(decisoes_persona)
                    sentimento_medio = sum(d.sentimento for d in decisoes_persona) / len(decisoes_persona)
                    confianca_agregada = sum(d.confianca for d in decisoes_persona) / len(decisoes_persona)
                    seen = set()
                    objecoes_consolidadas = [
                        o for d in decisoes_persona for o in d.objecoes
                        if not (o in seen or seen.add(o))
                    ]
                    divergence_score = divergence_score_from_decisoes(decisoes_persona)
                    concordancia = [
                        {"modelo_a": p.modelo_a, "modelo_b": p.modelo_b, "concordam": p.concordam}
                        for p in _compute_concordancia(decisoes_persona)
                    ]
                    agregada = DecisaoAggregada(
                        decisao_final=decisao_final,
                        wtp_medio=wtp_medio,
                        sentimento_medio=sentimento_medio,
                        objecoes_consolidadas=objecoes_consolidadas,
                        divergence_score=divergence_score,
                        concordancia=concordancia,
                        confianca_agregada=confianca_agregada,
                        raciocinio_sintese="Sintese automatica (sintetizador falhou)",
                    )
                    # NAO incrementar falhas neste caso (persona foi processada com sucesso via fallback)
            else:
                print(f"  [{i}/{n}] {p.owner_name} [SYNTH]: SKIP (apenas {len(decisoes_persona)} decisoes)")

            # Serializar persona: V5 usa persona_to_dict, V4 usa atributos diretos.
            if persona_version == "v5":
                from simulation_army_v2.personas_v5 import persona_to_dict
                persona_dict = persona_to_dict(p)
            else:
                persona_dict = {
                    "owner_name": p.owner_name,
                    "business_name": p.business_name,
                    "segment": p.segment,
                    "wtp_brl": p.wtp_brl,
                    "risk_profile": p.risk_profile,
                    "recent_event": p.recent_event,
                    "has_existing_security": p.has_existing_security,
                }
            results.append({
                "persona": persona_dict,
                "decisoes_modelos": [d.model_dump() for d in decisoes_persona],
                "metadados_modelos": metadados_modelos,
                "decisao_agregada": agregada.model_dump() if agregada else None,
            })

            # Checkpoint incremental: salva JSON parcial a cada persona.
            # Se o run for interrompido, nao perdemos horas de trabalho.
            _save_checkpoint(output_path, cfg, n, seed, ensemble_models,
                             synth_model, results, falhas)

            await asyncio.sleep(cfg.execution.delay_between_personas_seconds)

    # Metricas globais.
    decisoes_finais = [
        r["decisao_agregada"]["decisao_final"]
        for r in results
        if r.get("decisao_agregada")
    ]
    agendaram = sum(1 for d in decisoes_finais if d == "agendou")
    sucessos = len(decisoes_finais)
    conversao = agendaram / sucessos if sucessos > 0 else 0
    ic_lo, ic_hi = _ic95(conversao, sucessos)

    # Divergence score medio.
    divergence_scores = [
        r["decisao_agregada"]["divergence_score"]
        for r in results
        if r.get("decisao_agregada")
    ]
    div_media = sum(divergence_scores) / len(divergence_scores) if divergence_scores else 0

    # Custo total e por modelo (USD).
    todos_metadados = []
    for r in results:
        todos_metadados.extend(r.get("metadados_modelos", []))
    custos = calculate_run_cost(todos_metadados)

    output = {
        "cenario": cfg.scenario.code,
        "n": n,
        "seed": seed,
        "modelos": [m[0] for m in ensemble_models],
        "sintetizador": synth_model,
        "taxa_conversao": conversao,
        "agendaram": agendaram,
        "sucessos": sucessos,
        "falhas": falhas,
        "ic95": [ic_lo, ic_hi],
        "divergence_score_medio": div_media,
        "custo_total_usd": custos["custo_total_usd"],
        "custo_por_modelo": custos["custo_por_modelo"],
        "personas": results,
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[ENSEMBLE] conversao={conversao:.1%} ({agendaram}/{sucessos}) IC95=[{ic_lo:.1%}, {ic_hi:.1%}] div={div_media:.2f} custo=${custos['custo_total_usd']:.4f} -> {output_path}")
    return output


def main():
    parser = argparse.ArgumentParser(description="Simulation Army v2 - Ensemble")
    parser.add_argument("--scenario", default="scenarios_v2/slz-c-army.yaml")
    parser.add_argument("--n", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    if args.output is None:
        args.output = f"results_v2/ensemble_n{args.n}_s{args.seed}.json"

    out = asyncio.run(run_ensemble(args.scenario, args.n, args.seed, args.output))
    print(json.dumps({
        "taxa_conversao": out["taxa_conversao"],
        "agendaram": out["agendaram"],
        "sucessos": out["sucessos"],
        "falhas": out["falhas"],
        "ic95": out["ic95"],
        "divergence_score_medio": out["divergence_score_medio"],
    }, indent=2))


if __name__ == "__main__":
    main()
