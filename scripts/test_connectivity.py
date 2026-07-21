"""Valida conectividade de cada source (1 chamada por source).

Testa: gocat, kilocode, devin, cline, ollama.
Cada source deve retornar DecisaoPersona valida (JSON parseado).
Salva resultado em results_v2/connectivity_test.json.
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

from simulation_army_v2.baseline import GOCAT_KEY, GOCAT_URL, SYSTEM_PROMPT, _call_model
from simulation_army_v2.cline_adapter import call_cline
from simulation_army_v2.devin_adapter import call_devin
from simulation_army_v2.kilocode_adapter import call_kilocode
from simulation_army_v2.ollama_adapter import call_ollama

TEST_PROMPT = """## Business Owner Profile
- Name: Joao Silva
- Business: clinica (perene, medio)
- Bairro: Centro (risco: alto, perfil: comercial)
- Monthly revenue: R$ 25,000.00
- WTP for security: R$ 400.00

## EMIVE Offer
- Mensalidade: R$ 350.00/mes (contrato 36 meses)
- Visita tecnica gratuita

## Task
Return ONLY a JSON object with exactly these fields:
{
  "decisao": "visualizou" | "clicou" | "agendou" | "ignorou",
  "wtp": float,
  "sentimento": float,
  "objecoes": ["budget" | "timing" | "existing_solution" | "skepticism" | "complexity" | "need_lack"],
  "confianca": float,
  "raciocinio": "1-3 frases em portugues"
}

IMPORTANT: sentimento and confianca MUST be in range -1.0 to 1.0.
"""

SOURCES = [
    ("gocat", "gpt-oss:120b", "gocat"),
    ("kilocode", "kilo/cohere/north-mini-code:free", "kilocode"),
    ("devin", "glm-5-2", "devin"),
    ("cline", "gpt-oss:20b", "cline"),
    ("ollama", "nemotron-3-nano:30b", "ollama"),
]


async def test_source(source_name: str, model: str, source_type: str):
    """Testa 1 source e retorna (success, decisao, meta, error)."""
    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient() as client:
            if source_type == "gocat":
                d, meta = await _call_model(client, model, TEST_PROMPT)
            elif source_type == "kilocode":
                d, meta = await call_kilocode(model, TEST_PROMPT)
            elif source_type == "devin":
                d, meta = await call_devin(model, TEST_PROMPT)
            elif source_type == "cline":
                d, meta = await call_cline(model, TEST_PROMPT)
            elif source_type == "ollama":
                d, meta = await call_ollama(model, TEST_PROMPT, client=client)
            else:
                return False, None, None, f"unknown source: {source_type}"
        latency = time.monotonic() - t0
        return True, d, meta, None
    except Exception as e:
        latency = time.monotonic() - t0
        return False, None, {"latency_ms": int(latency * 1000)}, str(e)[:300]


async def main():
    print("=== Connectivity Test: 5 sources ===\n")
    results = {}
    for source_name, model, source_type in SOURCES:
        print(f"[{source_name}] Testing {model}...", end=" ", flush=True)
        success, decisao, meta, error = await test_source(source_name, model, source_type)
        if success:
            print(f"OK decisao={decisao.decisao} latency={meta.get('latency_ms')}ms")
            results[source_name] = {
                "model": model,
                "success": True,
                "decisao": decisao.decisao,
                "wtp": decisao.wtp,
                "latency_ms": meta.get("latency_ms"),
                "tokens": meta.get("total_tokens"),
                "provider_used": meta.get("provider_used"),
            }
        else:
            print(f"FAIL: {error}")
            results[source_name] = {
                "model": model,
                "success": False,
                "error": error,
                "latency_ms": meta.get("latency_ms") if meta else None,
            }
        await asyncio.sleep(1)

    # Salvar resultado.
    out_path = Path(__file__).parent.parent / "results_v2" / "connectivity_test.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nResultado salvo em {out_path}")

    ok = sum(1 for r in results.values() if r["success"])
    print(f"\n{ok}/{len(SOURCES)} sources OK")
    return ok


if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok >= 3 else 1)
