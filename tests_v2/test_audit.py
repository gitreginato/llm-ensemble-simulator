"""Testes do audit.py (helpers de auditoria)."""
import pytest

from simulation_army_v2.audit import run_audit, auditar_decisao
from unittest.mock import AsyncMock, patch, MagicMock


def test_audit_prompt_tem_campos_obrigatorios():
    """Verifica que o prompt template tem todos os campos necessarios."""
    from simulation_army_v2.audit import AUDIT_PROMPT
    campos = ["owner_name", "business_name", "segment", "wtp_brl",
              "risk_profile", "recent_event", "has_existing_security",
              "decisao_final", "wtp_medio", "sentimento_medio",
              "objecoes", "confianca_agregada", "raciocinio_sintese"]
    for c in campos:
        assert "{" + c + "}" in AUDIT_PROMPT, f"Campo {c} ausente no prompt"


@pytest.mark.asyncio
async def test_auditar_decisao_resposta_valida():
    """Mock da API retornando JSON valido com coerencia 0.8."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"coerencia": 0.8, "justificativa": "ok", "problemas": []}'}}]
    }
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    persona = {"owner_name": "Joao", "business_name": "Loja A", "segment": "varejo",
               "wtp_brl": 500, "risk_profile": "medio", "recent_event": "roubo",
               "has_existing_security": False}
    decisao = {"decisao_final": "agendou", "wtp_medio": 500, "sentimento_medio": 0.5,
               "objecoes_consolidadas": [], "confianca_agregada": 0.8,
               "raciocinio_sintese": "cliente decidiu agendar"}

    result = await auditar_decisao(mock_client, "command-r-plus", persona, decisao)
    assert result["coerencia"] == 0.8
    assert result["rejeitada"] is False
    assert result["justificativa"] == "ok"


@pytest.mark.asyncio
async def test_auditar_decisao_coerencia_baixa_rejeitada():
    """Coerencia < 0.5 deve ser rejeitada."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"coerencia": 0.3, "justificativa": "incoerente", "problemas": ["wtp errado"]}'}}]
    }
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    persona = {"owner_name": "Maria", "business_name": "Loja B", "segment": "varejo",
               "wtp_brl": 100, "risk_profile": "baixo", "recent_event": "none",
               "has_existing_security": True}
    decisao = {"decisao_final": "agendou", "wtp_medio": 1000, "sentimento_medio": -0.5,
               "objecoes_consolidadas": ["budget"], "confianca_agregada": 0.2,
               "raciocinio_sintese": "vai agendar"}

    result = await auditar_decisao(mock_client, "command-r-plus", persona, decisao)
    assert result["coerencia"] == 0.3
    assert result["rejeitada"] is True


@pytest.mark.asyncio
async def test_auditar_decisao_erro_api():
    """Erro de API deve retornar rejeitada=True."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "server error"
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    persona = {"owner_name": "Test", "business_name": "Test", "segment": "test",
               "wtp_brl": 0, "risk_profile": "test", "recent_event": "test",
               "has_existing_security": False}
    decisao = {"decisao_final": "visualizou", "wtp_medio": 0, "sentimento_medio": 0,
               "objecoes_consolidadas": [], "confianca_agregada": 0,
               "raciocinio_sintese": "test"}

    result = await auditar_decisao(mock_client, "command-r-plus", persona, decisao)
    assert result["rejeitada"] is True
    assert result["coerencia"] == 0.0
