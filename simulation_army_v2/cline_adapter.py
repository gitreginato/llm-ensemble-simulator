"""Adapter cline CLI: chama `cline -y --json -P openai -m <model> "prompt"` via subprocess.

Cline CLI (v3.0.46+) suporta headless mode com --json (newline-delimited JSON events).
Configurado para usar gocat como backend OpenAI-compatible (http://127.0.0.1:8080/v1).
Assim as API keys ficam no gocat, nao expostas no ambiente.

Reusa _parse_json_response e DecisaoPersona do baseline para validar a resposta.
"""
import asyncio
import json
import os
import time
from typing import Any

from simulation_army_v2.baseline import _parse_json_response
from simulation_army_v2.schema import DecisaoPersona

_SYSTEM = "You are a store owner evaluating a security offer. Return ONLY valid JSON."


def _parse_cline_json_events(stdout: str) -> tuple[str, dict[str, Any]]:
    """Extrai (content, metadados) dos eventos JSON newline-delimited do cline --json.

    Cline --json emite um JSON object por linha. Campos relevantes:
      type=agent_event, event.type=content_end, event.text -> texto completo da resposta
      type=agent_event, event.type=content_start, event.accumulated -> texto parcial acumulado
      type=run_result, usage -> {inputTokens, outputTokens, totalCost}
      type=error, message -> mensagem de erro

    Retorna (content, {"prompt_tokens": int|None, "completion_tokens": int|None,
    "total_tokens": int|None, "error": str|None}).
    """
    content_parts: list[str] = []
    last_accumulated: str = ""
    meta: dict[str, Any] = {
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
        "error": None,
    }
    for line in stdout.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        etype = event.get("type", "")
        if etype == "agent_event":
            ev = event.get("event", {})
            ev_type = ev.get("type", "")
            if ev_type == "content_end" and ev.get("contentType") == "text":
                # content_end tem o texto completo do chunk.
                content_parts.append(ev.get("text", ""))
            elif ev_type == "content_start" and ev.get("contentType") == "text":
                # Fallback: accumulated tem o texto parcial acumulado.
                last_accumulated = ev.get("accumulated", "")
        elif etype == "run_result":
            usage = event.get("usage", {})
            if isinstance(usage, dict):
                meta["prompt_tokens"] = usage.get("inputTokens")
                meta["completion_tokens"] = usage.get("outputTokens")
        elif etype == "error":
            msg = event.get("message", "")
            if msg:
                meta["error"] = msg
    content = "".join(content_parts) or last_accumulated
    if meta["prompt_tokens"] and meta["completion_tokens"]:
        meta["total_tokens"] = (meta["prompt_tokens"] or 0) + (meta["completion_tokens"] or 0)
    return content, meta


async def call_cline(
    model: str,
    user_prompt: str,
    provider: str = "openai",
    api_key: str | None = None,
    base_url: str | None = None,
    timeout: int = 120,
) -> tuple[DecisaoPersona, dict[str, Any]]:
    """Chama cline -y --json -P openai -m <model> "prompt" via gocat e retorna (DecisaoPersona, metadados).

    Por padrao usa gocat como backend (http://127.0.0.1:8080/v1) com a local dev key.
    As API keys reais ficam no gocat, nao expostas no ambiente.

    Args:
        model: modelo no gocat (ex: gpt-oss:120b, Meta-Llama-3.3-70B-Instruct, gpt-4o-mini)
        user_prompt: prompt do usuario (sem system prompt, adicionado internamente)
        provider: provider id do cline (default: openai = OpenAI-compatible = gocat)
        api_key: override de API key (default: GOCAT_KEY do baseline)
        base_url: override de base URL (default: GOCAT_URL do baseline)
        timeout: timeout em segundos

    Returns:
        (DecisaoPersona, metadados) onde metadados tem latency_ms, http_status, tokens, provider_used.
    """
    t0 = time.monotonic()
    full_prompt = f"{_SYSTEM}\n\n{user_prompt}"
    env = os.environ.copy()
    # Cline usa auth configurada (cline auth --provider openai --baseurl <gocat>).
    # --baseurl nao e opcao do comando cline, apenas do auth.
    # Keys ficam no gocat, nao expostas no ambiente.
    cmd = [
        "cline", "-y", "--json",
        "-P", provider,
        "-m", model,
        "--auto-approve", "true",
        full_prompt,
    ]
    if api_key:
        cmd.extend(["-k", api_key])
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
        raise RuntimeError(f"cline timeout {timeout}s para {model} (provider={provider})")
    latency_ms = int((time.monotonic() - t0) * 1000)
    stdout_str = stdout_b.decode("utf-8", errors="replace")
    content, token_meta = _parse_cline_json_events(stdout_str)
    if not content:
        stderr_str = stderr_b.decode("utf-8", errors="replace")[:300]
        raise RuntimeError(
            f"cline {model} (provider={provider}): content vazio. "
            f"error={token_meta.get('error')} stderr={stderr_str}"
        )
    data = _parse_json_response(content)
    data["modelo"] = model
    decisao = DecisaoPersona(**data)
    meta = {
        "latency_ms": latency_ms,
        "http_status": 200,
        "prompt_tokens": token_meta["prompt_tokens"],
        "completion_tokens": token_meta["completion_tokens"],
        "total_tokens": token_meta["total_tokens"],
        "provider_used": "cline",
    }
    return decisao, meta
