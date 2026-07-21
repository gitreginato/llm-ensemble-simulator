"""Adapter Ollama via gocat (HTTP, rate limits do gocat).

Ollama cloud esta configurado no gocat (8 modelos free):
  gpt-oss:120b, gpt-oss:20b, nemotron-3-ultra, nemotron-3-nano:30b,
  nemotron-3-super, minimax-m2.5, minimax-m3, gemma4:31b

Este adapter chama o gocat (nao ollama.com direto) para manter as API keys
no gocat. O gocat roteia para o provider ollama internamente.

Reusa _parse_json_response e DecisaoPersona do baseline para validar a resposta.
"""
import asyncio
import json
import os
import time
from typing import Any

import httpx

from simulation_army_v2.baseline import GOCAT_KEY, GOCAT_URL, SYSTEM_PROMPT, _parse_json_response
from simulation_army_v2.schema import DecisaoPersona


async def call_ollama(
    model: str,
    user_prompt: str,
    client: httpx.AsyncClient | None = None,
    timeout: int = 90,
) -> tuple[DecisaoPersona, dict[str, Any]]:
    """Chama modelo Ollama via gocat e retorna (DecisaoPersona, metadados).

    Usa o endpoint do gocat (http://127.0.0.1:8080/v1/chat/completions).
    O gocat roteia para o provider ollama internamente, mantendo as API keys seguras.

    Args:
        model: modelo Ollama no gocat (ex: gpt-oss:120b, gemma4:31b)
        user_prompt: prompt do usuario
        client: httpx.AsyncClient opcional (reuso de conexao)
        timeout: timeout em segundos

    Returns:
        (DecisaoPersona, metadados) com latency_ms, http_status, tokens, provider_used.
    """
    t0 = time.monotonic()
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 2000,
        "temperature": 0.7,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GOCAT_KEY}",
    }
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient()
    try:
        last_status = None
        for attempt in range(3):
            try:
                r = await client.post(
                    f"{GOCAT_URL}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=timeout,
                )
                last_status = r.status_code
                latency_ms = int((time.monotonic() - t0) * 1000)
                if r.status_code == 200:
                    data = r.json()
                    if "choices" not in data or not data["choices"]:
                        raise ValueError(f"Ollama response missing choices: {str(data)[:200]}")
                    msg = data["choices"][0].get("message", {})
                    content = msg.get("content") or ""
                    if not content and msg.get("reasoning_content"):
                        content = msg["reasoning_content"]
                    if not content:
                        raise ValueError("Ollama: content e reasoning_content vazios")
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
                        "provider_used": "ollama",
                    }
                    return decisao, meta
                if r.status_code >= 500 and attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                if r.status_code == 429 and attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f"Ollama HTTP {r.status_code}: {r.text[:200]}")
            except (httpx.HTTPError, json.JSONDecodeError, ValueError) as e:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
        raise RuntimeError(f"Ollama {model}: 3 tentativas falharam (last_status={last_status})")
    finally:
        if own_client:
            await client.aclose()
