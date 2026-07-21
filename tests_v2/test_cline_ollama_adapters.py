"""Testes para cline_adapter e ollama_adapter.

Mocka subprocess (cline) e HTTP (ollama) para testar parsing e error handling
sem chamar LLMs reais.
"""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from simulation_army_v2.cline_adapter import _parse_cline_json_events, call_cline
from simulation_army_v2.ollama_adapter import call_ollama
from simulation_army_v2.schema import DecisaoPersona


# === cline_adapter: _parse_cline_json_events ===

def test_parse_cline_events_content_end():
    """Extrai content de agent_event com type=content_end e contentType=text."""
    stdout = json.dumps({
        "type": "agent_event",
        "event": {"type": "content_end", "contentType": "text", "text": "hello world"},
    }) + "\n"
    content, meta = _parse_cline_json_events(stdout)
    assert content == "hello world"
    assert meta["error"] is None


def test_parse_cline_events_multiple_content_end_concatenated():
    """Multiplos content_end sao concatenados."""
    stdout = (
        json.dumps({"type": "agent_event", "event": {"type": "content_end", "contentType": "text", "text": "part1 "}}) + "\n" +
        json.dumps({"type": "agent_event", "event": {"type": "content_end", "contentType": "text", "text": "part2"}}) + "\n"
    )
    content, _ = _parse_cline_json_events(stdout)
    assert content == "part1 part2"


def test_parse_cline_events_content_start_accumulated_fallback():
    """Se nao ha content_end, usa accumulated do ultimo content_start."""
    stdout = json.dumps({
        "type": "agent_event",
        "event": {"type": "content_start", "contentType": "text", "accumulated": "fallback text"},
    }) + "\n"
    content, _ = _parse_cline_json_events(stdout)
    assert content == "fallback text"


def test_parse_cline_events_run_result_tokens():
    """Extrai tokens de run_result.usage."""
    stdout = json.dumps({
        "type": "run_result",
        "usage": {"inputTokens": 100, "outputTokens": 50, "totalCost": 0},
    }) + "\n"
    _, meta = _parse_cline_json_events(stdout)
    assert meta["prompt_tokens"] == 100
    assert meta["completion_tokens"] == 50
    assert meta["total_tokens"] == 150


def test_parse_cline_events_error():
    """Extrai error de evento error."""
    stdout = json.dumps({
        "type": "error",
        "message": "rate limit exceeded",
    }) + "\n"
    _, meta = _parse_cline_json_events(stdout)
    assert meta["error"] == "rate limit exceeded"


def test_parse_cline_events_empty_stdout():
    """Stdout vazio retorna content vazio e meta com None."""
    content, meta = _parse_cline_json_events("")
    assert content == ""
    assert meta["prompt_tokens"] is None
    assert meta["error"] is None


def test_parse_cline_events_invalid_json_skipped():
    """Linhas com JSON invalido sao puladas silenciosamente."""
    stdout = "not json\n" + json.dumps({
        "type": "agent_event",
        "event": {"type": "content_end", "contentType": "text", "text": "ok"},
    }) + "\n"
    content, _ = _parse_cline_json_events(stdout)
    assert content == "ok"


def test_parse_cline_events_json_response_extracted():
    """Extrai JSON da resposta do LLM embutido em content_end."""
    json_resp = '{"decisao": "agendou", "wtp": 500.0, "sentimento": 0.5, "objecoes": [], "confianca": 0.8, "raciocinio": "teste"}'
    stdout = json.dumps({
        "type": "agent_event",
        "event": {"type": "content_end", "contentType": "text", "text": json_resp},
    }) + "\n"
    content, _ = _parse_cline_json_events(stdout)
    assert "decisao" in content
    assert "agendou" in content


# === cline_adapter: call_cline (mocked subprocess) ===

@pytest.mark.asyncio
async def test_call_cline_success():
    """call_cline com subprocess mockado retorna DecisaoPersona valida."""
    json_resp = '{"decisao": "agendou", "wtp": 500.0, "sentimento": 0.5, "objecoes": [], "confianca": 0.8, "raciocinio": "bom"}'
    event_line = json.dumps({
        "type": "agent_event",
        "event": {"type": "content_end", "contentType": "text", "text": json_resp},
    }) + "\n"
    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(return_value=(
        event_line.encode(),
        b"",
    ))
    mock_proc.kill = MagicMock()
    mock_proc.wait = AsyncMock()
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        decisao, meta = await call_cline("test-model", "prompt")
    assert isinstance(decisao, DecisaoPersona)
    assert decisao.decisao == "agendou"
    assert decisao.wtp == 500.0
    assert meta["provider_used"] == "cline"
    assert meta["http_status"] == 200
    assert meta["latency_ms"] >= 0


@pytest.mark.asyncio
async def test_call_cline_timeout():
    """call_cline com timeout levanta RuntimeError."""
    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
    mock_proc.kill = MagicMock()
    mock_proc.wait = AsyncMock()
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        with pytest.raises(RuntimeError, match="timeout"):
            await call_cline("test-model", "prompt", timeout=1)


@pytest.mark.asyncio
async def test_call_cline_empty_content():
    """call_cline com content vazio levanta RuntimeError."""
    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(return_value=(b"", b"some error"))
    mock_proc.kill = MagicMock()
    mock_proc.wait = AsyncMock()
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        with pytest.raises(RuntimeError, match="content vazio"):
            await call_cline("test-model", "prompt")


# === ollama_adapter: call_ollama (mocked HTTP) ===

@pytest.mark.asyncio
async def test_call_ollama_success():
    """call_ollama com HTTP mockado retorna DecisaoPersona valida."""
    json_resp = {
        "choices": [{
            "message": {
                "content": '{"decisao": "visualizou", "wtp": 200.0, "sentimento": -0.2, "objecoes": ["budget"], "confianca": 0.5, "raciocinio": "caro"}'
            }
        }],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    }
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = json_resp
    mock_resp.text = json.dumps(json_resp)
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.aclose = AsyncMock()
    with patch("simulation_army_v2.ollama_adapter.GOCAT_KEY", "test-key"):
        decisao, meta = await call_ollama("gpt-oss:120b", "prompt", client=mock_client)
    assert isinstance(decisao, DecisaoPersona)
    assert decisao.decisao == "visualizou"
    assert meta["provider_used"] == "ollama"
    assert meta["total_tokens"] == 150


@pytest.mark.asyncio
async def test_call_ollama_500_retries():
    """call_ollama com HTTP 500 retrata 3 vezes antes de falhar com HTTP error."""
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "internal error"
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.aclose = AsyncMock()
    with patch("asyncio.sleep", new=AsyncMock()):
        with pytest.raises(RuntimeError, match="Ollama HTTP 500"):
            await call_ollama("gpt-oss:120b", "prompt", client=mock_client, timeout=5)


@pytest.mark.asyncio
async def test_call_ollama_429_retries():
    """call_ollama com HTTP 429 retrata antes de falhar com HTTP error."""
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.text = "rate limit"
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.aclose = AsyncMock()
    with patch("asyncio.sleep", new=AsyncMock()):
        with pytest.raises(RuntimeError, match="Ollama HTTP 429"):
            await call_ollama("gpt-oss:120b", "prompt", client=mock_client, timeout=5)


@pytest.mark.asyncio
async def test_call_ollama_empty_choices():
    """call_ollama com choices vazio levanta ValueError."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"choices": []}
    mock_resp.text = '{"choices": []}'
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.aclose = AsyncMock()
    with patch("asyncio.sleep", new=AsyncMock()):
        with pytest.raises((ValueError, RuntimeError)):
            await call_ollama("gpt-oss:120b", "prompt", client=mock_client, timeout=5)


# === ensemble.py: source dispatch (import check) ===

def test_ensemble_imports_cline_and_ollama():
    """ensemble.py deve importar call_cline e call_ollama sem erro."""
    from simulation_army_v2.ensemble import call_cline, call_ollama
    assert callable(call_cline)
    assert callable(call_ollama)


def test_ensemble_source_dispatch_has_cline_and_ollama():
    """ensemble.py deve ter source == 'cline' e source == 'ollama' no dispatch."""
    import simulation_army_v2.ensemble as ens
    source = open(ens.__file__).read()
    assert 'source == "cline"' in source
    assert 'source == "ollama"' in source
    assert "call_cline" in source
    assert "call_ollama" in source
