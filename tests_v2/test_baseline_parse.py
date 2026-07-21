"""Testes do baseline.py (parse e clamp)."""
import pytest

from simulation_army_v2.baseline import _parse_json_response


def test_parse_json_simple():
    data = _parse_json_response('{"decisao": "agendou", "wtp": 500, "sentimento": 0.5, "objecoes": [], "confianca": 0.8, "raciocinio": "ok"}')
    assert data["decisao"] == "agendou"
    assert data["wtp"] == 500


def test_parse_json_code_fences():
    data = _parse_json_response('```json\n{"decisao": "agendou", "wtp": 500, "sentimento": 0.5, "objecoes": [], "confianca": 0.8, "raciocinio": "ok"}\n```')
    assert data["decisao"] == "agendou"


def test_parse_json_with_preamble():
    data = _parse_json_response('Here is the response:\n{"decisao": "ignorou", "wtp": 0, "sentimento": -0.3, "objecoes": ["need_lack"], "confianca": 0.9, "raciocinio": "nao precisa"}')
    assert data["decisao"] == "ignorou"


def test_clamp_sentimento_0_10_to_0_1():
    data = _parse_json_response('{"decisao": "agendou", "wtp": 500, "sentimento": 6.5, "objecoes": [], "confianca": 0.8, "raciocinio": "ok"}')
    assert data["sentimento"] == 0.65


def test_clamp_confianca_0_10_to_0_1():
    data = _parse_json_response('{"decisao": "agendou", "wtp": 500, "sentimento": 0.5, "objecoes": [], "confianca": 5.5, "raciocinio": "ok"}')
    assert data["confianca"] == 0.55


def test_clamp_sentimento_negative_0_10_to_0_1():
    """Bug fix: -5 / -10 = 0.5 (wrong sign). Should be -5 / 10 = -0.5."""
    data = _parse_json_response('{"decisao": "ignorou", "wtp": 0, "sentimento": -5.0, "objecoes": [], "confianca": 0.8, "raciocinio": "ok"}')
    assert data["sentimento"] == -0.5, f"Expected -0.5, got {data['sentimento']}"


def test_clamp_sentimento_already_in_range():
    data = _parse_json_response('{"decisao": "agendou", "wtp": 500, "sentimento": 0.7, "objecoes": [], "confianca": 0.8, "raciocinio": "ok"}')
    assert data["sentimento"] == 0.7


def test_decisao_map_scheduled_to_agendou():
    data = _parse_json_response('{"decisao": "scheduled", "wtp": 500, "sentimento": 0.5, "objecoes": [], "confianca": 0.8, "raciocinio": "ok"}')
    assert data["decisao"] == "agendou"


def test_decisao_map_ignored_to_ignorou():
    data = _parse_json_response('{"decisao": "ignored", "wtp": 0, "sentimento": -0.3, "objecoes": [], "confianca": 0.8, "raciocinio": "ok"}')
    assert data["decisao"] == "ignorou"


def test_objecao_map_price_to_budget():
    data = _parse_json_response('{"decisao": "ignorou", "wtp": 0, "sentimento": -0.3, "objecoes": ["price"], "confianca": 0.8, "raciocinio": "ok"}')
    assert data["objecoes"] == ["budget"]


def test_objecao_map_multiple():
    data = _parse_json_response('{"decisao": "ignorou", "wtp": 0, "sentimento": -0.3, "objecoes": ["price", "trust", "hard"], "confianca": 0.8, "raciocinio": "ok"}')
    assert data["objecoes"] == ["budget", "skepticism", "complexity"]


def test_objecao_already_valid():
    data = _parse_json_response('{"decisao": "ignorou", "wtp": 0, "sentimento": -0.3, "objecoes": ["budget", "timing"], "confianca": 0.8, "raciocinio": "ok"}')
    assert data["objecoes"] == ["budget", "timing"]


def test_parse_json_not_found_raises():
    with pytest.raises(ValueError, match="JSON nao encontrado"):
        _parse_json_response("no json here")


def test_parse_json_invalid_raises():
    with pytest.raises(ValueError):
        _parse_json_response("{invalid json}")
