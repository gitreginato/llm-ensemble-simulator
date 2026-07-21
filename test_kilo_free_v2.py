"""Teste real: modelos free do gateway kilo via kilocode CLI.

Salva content completo e usa o parser _parse_json_response do baseline
para validar se cada modelo retorna uma DecisaoPersona valida.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, ".")
from simulation_army_v2.baseline import _parse_json_response
from simulation_army_v2.schema import DecisaoPersona

PROMPT_SIMULACAO = """Voce e um dono de loja de roupas em Sao Luis, MA.
Recebeu uma oferta de sistema de seguranca inteligente para lojas.
Faturamento mensal: R$ 80.000. Estoque valioso, vitrine exposta.

Responda APENAS com JSON valido:
{"decisao": "agendou" | "visualizou" | "clicou" | "ignorou", "wtp": 500.0, "sentimento": 0.5, "objecoes": ["budget"], "confianca": 0.7, "raciocinio": "explicacao curta"}"""

SYSTEM_PROMPT = "You are a store owner. Return ONLY valid JSON."

MODELOS_FREE_KILO = [
    "kilo/cohere/north-mini-code:free",
    "kilo/kilo-auto/free",
    "kilo/kilo-auto/small",
    "kilo/kwaipilot/kat-coder-pro-v2.5:free",
    "kilo/nvidia/nemotron-3-super-120b-a12b:free",
    "kilo/nvidia/nemotron-3-ultra-550b-a55b:free",
    "kilo/openrouter/free",
    "kilo/poolside/laguna-m.1:free",
    "kilo/poolside/laguna-xs-2.1:free",
    "kilo/stepfun/step-3.7-flash:free",
    "kilo/tencent/hy3:free",
]


def testar(modelo: str) -> dict:
    t0 = time.monotonic()
    env = os.environ.copy()
    # kilocode precisa de system + user. O CLI aceita so a mensagem.
    # Vamos incluir o system no prompt para garantir.
    prompt_full = f"{SYSTEM_PROMPT}\n\n{PROMPT_SIMULACAO}"
    try:
        result = subprocess.run(
            ["kilocode", "run", "-m", modelo, "--format", "json", prompt_full],
            capture_output=True,
            text=True,
            timeout=90,
            env=env,
        )
        latency_ms = int((time.monotonic() - t0) * 1000)
        content_parts = []
        tokens_total = None
        cost = None
        error_msg = None
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                evt = json.loads(line)
                t = evt.get("type")
                part = evt.get("part", {})
                if t == "text":
                    text = part.get("text", "")
                    if text:
                        content_parts.append(text)
                elif t == "step_finish":
                    toks = part.get("tokens", {})
                    tokens_total = toks.get("total")
                    cost = part.get("cost")
                elif t == "error":
                    err = part.get("error", evt.get("error", {}))
                    error_msg = err.get("data", {}).get("message", str(err))
            except json.JSONDecodeError:
                pass
        content = "".join(content_parts)
        if error_msg and not content:
            return {"modelo": modelo, "status": "FAIL", "latency_ms": latency_ms, "erro": error_msg[:200]}
        if not content:
            return {"modelo": modelo, "status": "FAIL", "latency_ms": latency_ms, "erro": "content vazio"}

        # Tentar parser do baseline
        parse_ok = False
        decisao = None
        parse_erro = None
        try:
            data = _parse_json_response(content)
            decisao = DecisaoPersona(modelo=modelo, **data)
            parse_ok = True
        except Exception as e:
            parse_erro = str(e)[:150]

        return {
            "modelo": modelo,
            "status": "OK",
            "latency_ms": latency_ms,
            "total_tokens": tokens_total,
            "cost_usd": cost,
            "content_len": len(content),
            "content_full": content[:500],
            "parse_ok": parse_ok,
            "decisao": decisao.decisao if parse_ok else None,
            "parse_erro": parse_erro,
        }
    except subprocess.TimeoutExpired:
        return {"modelo": modelo, "status": "FAIL", "latency_ms": int((time.monotonic() - t0) * 1000), "erro": "timeout 90s"}
    except Exception as e:
        return {"modelo": modelo, "status": "FAIL", "latency_ms": int((time.monotonic() - t0) * 1000), "erro": str(e)[:150]}


def main():
    print("=" * 95)
    print("TESTE REAL: 11 modelos free do gateway kilo via kilocode CLI + parser do baseline")
    print("=" * 95)
    print()
    resultados = []
    for i, modelo in enumerate(MODELOS_FREE_KILO, 1):
        print(f"  [{i:2d}/{len(MODELOS_FREE_KILO)}] {modelo:55s} ...", end=" ", flush=True)
        r = testar(modelo)
        resultados.append(r)
        if r["status"] == "OK":
            parse = "PARSE_OK" if r.get("parse_ok") else "PARSE_FAIL"
            dec = r.get("decisao", "-")
            print(f"OK  {r['latency_ms']:5d}ms {parse:10s} decisao={dec}")
        else:
            print(f"FAIL {r['latency_ms']:5d}ms {r.get('erro', '')[:50]}")
        time.sleep(0.5)

    print()
    print("=" * 95)
    print("RESUMO")
    print("=" * 95)
    ok = [r for r in resultados if r["status"] == "OK"]
    fail = [r for r in resultados if r["status"] == "FAIL"]
    parse_ok = [r for r in ok if r.get("parse_ok")]
    print(f"\nRespondeu: {len(ok)}/{len(resultados)}")
    print(f"Parse OK (DecisaoPersona valida): {len(parse_ok)}/{len(ok)}")
    print(f"FAIL: {len(fail)}/{len(resultados)}")

    if ok:
        lats = [r["latency_ms"] for r in ok]
        print(f"Latencia: min={min(lats)}ms media={sum(lats)//len(lats)}ms max={max(lats)}ms")

    print("\n>>> Modelos que retornaram DecisaoPersona valida:")
    for r in parse_ok:
        print(f"  {r['modelo']:55s} {r['latency_ms']:5d}ms decisao={r['decisao']} tokens={r.get('total_tokens')} cost=${r.get('cost_usd')}")

    print("\n>>> Modelos que responderam mas falharam no parse:")
    for r in ok:
        if not r.get("parse_ok"):
            print(f"  {r['modelo']:55s} erro: {r.get('parse_erro', '')[:80]}")
            print(f"    content: {r.get('content_full', '')[:150]}")

    print("\n>>> Modelos que falharam:")
    for r in fail:
        print(f"  {r['modelo']:55s} {r.get('erro', '')[:80]}")

    out = Path("/tmp/test_kilo_free_v2.json")
    out.write_text(json.dumps(resultados, ensure_ascii=False, indent=2))
    print(f"\nSalvo em: {out}")


if __name__ == "__main__":
    main()
