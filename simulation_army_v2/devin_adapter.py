"""Adapter devin CLI: chama `devin --print --model <model> -- <prompt>` via subprocess.

O devin retorna o output direto no stdout (sem eventos JSON como o kilocode).
Modelos free: glm-5-2, swe-1-7, swe-1-6.

Reusa _parse_json_response e DecisaoPersona do baseline para validar a resposta.
"""
import asyncio
import os
import time
from typing import Any

from simulation_army_v2.baseline import _parse_json_response
from simulation_army_v2.schema import DecisaoPersona

_SYSTEM = "You are a store owner evaluating a security offer. Return ONLY valid JSON."


async def call_devin(
    model: str,
    user_prompt: str,
    timeout: int = 90,
) -> tuple[DecisaoPersona, dict[str, Any]]:
    """Chama devin --print --model <model> -- <prompt> e retorna (DecisaoPersona, metadados).

    metadados: latency_ms, http_status (200 se OK), provider_used (devin).
    Tokens nao estao disponiveis no output do devin CLI (None).
    """
    t0 = time.monotonic()
    full_prompt = f"{_SYSTEM}\n\n{user_prompt}"
    env = os.environ.copy()
    cmd = ["devin", "--print", "--model", model, "--", full_prompt]
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
        raise RuntimeError(f"devin timeout {timeout}s para {model}")
    latency_ms = int((time.monotonic() - t0) * 1000)
    content = stdout_b.decode("utf-8", errors="replace").strip()
    if not content:
        raise RuntimeError(f"devin {model}: content vazio. stderr={stderr_b.decode('utf-8', errors='replace')[:200]}")
    data = _parse_json_response(content)
    data["modelo"] = model
    decisao = DecisaoPersona(**data)
    meta = {
        "latency_ms": latency_ms,
        "http_status": 200,
        "prompt_tokens": None,  # devin CLI nao expoe tokens
        "completion_tokens": None,
        "total_tokens": None,
        "provider_used": "devin",
    }
    return decisao, meta
