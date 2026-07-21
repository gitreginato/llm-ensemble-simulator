"""Adapter kilocode CLI: chama `kilocode run -m <model> --format json` via subprocess.

Eventos JSON (newline-delimited) no stdout:
  type=text        -> part.text = conteudo da resposta
  type=step_finish -> part.tokens = {input, output, total, reasoning}, part.cost
  type=error       -> part.error.data.message

Reusa _parse_json_response e DecisaoPersona do baseline para validar a resposta.
"""
import asyncio
import json
import os
import time
from typing import Any

from simulation_army_v2.baseline import _parse_json_response
from simulation_army_v2.schema import DecisaoPersona

# System prompt alinhado com o do baseline.py (SYSTEM_PROMPT).
_SYSTEM = "You are a store owner evaluating a security offer. Return ONLY valid JSON."


def _parse_kilocode_events(stdout: str) -> tuple[str, dict[str, Any]]:
    """Extrai (content, metadados) dos eventos JSON newline-delimited do kilocode.

    Retorna (content, {"prompt_tokens": int|None, "completion_tokens": int|None,
    "total_tokens": int|None, "cost_usd": float|None, "error": str|None}).
    """
    content_parts: list[str] = []
    meta: dict[str, Any] = {
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
        "cost_usd": None,
        "error": None,
    }
    for line in stdout.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = evt.get("type")
        part = evt.get("part", {})
        if t == "text":
            text = part.get("text", "")
            if text:
                content_parts.append(text)
        elif t == "step_finish":
            toks = part.get("tokens", {}) or {}
            meta["prompt_tokens"] = toks.get("input")
            meta["completion_tokens"] = toks.get("output")
            meta["total_tokens"] = toks.get("total")
            meta["cost_usd"] = part.get("cost")
        elif t == "error":
            err = part.get("error", evt.get("error", {}))
            meta["error"] = err.get("data", {}).get("message", str(err))
    return "".join(content_parts), meta


async def call_kilocode(
    model: str,
    user_prompt: str,
    timeout: int = 90,
) -> tuple[DecisaoPersona, dict[str, Any]]:
    """Chama kilocode run -m <model> --format json e retorna (DecisaoPersona, metadados).

    metadados contem: latency_ms, prompt_tokens, completion_tokens, total_tokens,
    cost_usd, http_status (sempre 200 se OK), provider_used (kilocode).
    """
    t0 = time.monotonic()
    # System + user em 1 prompt (kilocode CLI aceita so a mensagem posicional).
    full_prompt = f"{_SYSTEM}\n\n{user_prompt}"
    env = os.environ.copy()
    cmd = ["kilocode", "run", "-m", model, "--format", "json", full_prompt]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise RuntimeError(f"kilocode timeout {timeout}s para {model}")
    latency_ms = int((time.monotonic() - t0) * 1000)
    stdout = stdout_b.decode("utf-8", errors="replace")
    content, meta = _parse_kilocode_events(stdout)
    if meta.get("error") and not content:
        raise RuntimeError(f"kilocode {model}: {meta['error'][:200]}")
    if not content:
        # Fallback: stderr pode ter log util, mas content e o que importa.
        raise RuntimeError(f"kilocode {model}: content vazio. stderr={stderr_b.decode('utf-8', errors='replace')[:200]}")
    data = _parse_json_response(content)
    data["modelo"] = model
    decisao = DecisaoPersona(**data)
    meta["latency_ms"] = latency_ms
    meta["http_status"] = 200
    meta["provider_used"] = "kilocode"
    return decisao, meta
