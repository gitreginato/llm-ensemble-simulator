"""Edge case tests for run_sim_v0.py and gerar_relatorio_fase0.py.

Covers boundary and invalid-input scenarios that could cause crashes,
wrong results, or undefined behavior.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from scripts.gerar_relatorio_fase0 import gerar_mapa_prospeccao, gerar_relatorio_md
from scripts.run_sim_v0 import rodar_simulacao, salvar_resultados
from simulation_army_v2.modelo_probabilistico import ic_bayesiano
from simulation_army_v2.personas_v5 import SEGMENT_BASELINES_V5


# Helper: minimal analise_real mock with all required keys
ANALISE_REAL_MOCK = {
    "n_personas": 142,
    "informacao_mutua_features": [("recent_event", 0.1), ("segment", 0.05)],
    "entropia_global": {"h_bits": 1.0, "distribuicao": {"agendou": 19, "visualizou": 123}},
}


# === 1. rodar_simulacao with n=0 (empty simulation) ===

def test_rodar_simulacao_n_zero():
    """rodar_simulacao with n=0 must not crash and return sensible defaults."""
    result = rodar_simulacao(n=0)
    assert result["meta"]["n_personas"] == 0
    assert result["estatisticas"]["taxa_conversao"] == 0
    assert result["resultados"] == []
    assert result["por_nicho"] == {}
    assert result["por_bairro"] == {}
    # IC should be (0, 1) representing max uncertainty
    assert result["estatisticas"]["ic_95_bayesiano"] == [0.0, 1.0]


# === 2. rodar_simulacao with segment not in SEGMENT_BASELINES_V5 ===

def test_rodar_simulacao_invalid_segment():
    """rodar_simulacao with unknown segment must raise ValueError with clear message."""
    with pytest.raises(ValueError, match="segment"):
        rodar_simulacao(n=10, segment="nonexistent_segment_xyz")


# === 3. salvar_resultados with output_dir that doesn't exist ===

def test_salvar_resultados_creates_output_dir(tmp_path):
    """salvar_resultados must create nested output_dir if it doesn't exist."""
    nested = tmp_path / "nonexistent" / "deep" / "dir"
    result = rodar_simulacao(n=5)
    paths = salvar_resultados(result, str(nested))
    assert Path(paths["json_completo"]).exists()
    assert Path(paths["json_stats"]).exists()


# === 4. salvar_resultados with read-only output_dir ===

def test_salvar_resultados_readonly_dir(tmp_path):
    """salvar_resultados with read-only dir must raise PermissionError with clear message."""
    ro_dir = tmp_path / "readonly"
    ro_dir.mkdir()
    os.chmod(str(ro_dir), 0o444)
    result = {"meta": {"n_personas": 5, "segment": "test", "mes": 7}, "estatisticas": {}}
    try:
        with pytest.raises(PermissionError, match="output_dir"):
            salvar_resultados(result, str(ro_dir))
    finally:
        os.chmod(str(ro_dir), 0o755)


# === 5. gerar_mapa_prospeccao with empty resultados list ===

def test_gerar_mapa_prospeccao_empty_resultados():
    """gerar_mapa_prospeccao with empty resultados must return empty list, not crash."""
    result = {"resultados": []}
    mapa = gerar_mapa_prospeccao(result)
    assert mapa == []
    assert isinstance(mapa, list)


# === 6. gerar_relatorio_md with empty mapa ===

def test_gerar_relatorio_md_empty_mapa():
    """gerar_relatorio_md with empty mapa must not crash and produce valid markdown."""
    result = rodar_simulacao(n=5)
    relatorio = gerar_relatorio_md(result, [], ANALISE_REAL_MOCK)
    assert isinstance(relatorio, str)
    assert "Relatorio FASE 0" in relatorio


# === 7. gerar_relatorio_md with empty por_nicho (segment specified) ===

def test_gerar_relatorio_md_empty_por_nicho():
    """gerar_relatorio_md with empty por_nicho (segment specified) must not crash."""
    result = rodar_simulacao(n=10, segment="farmacia")
    assert result["por_nicho"] == {}
    mapa = gerar_mapa_prospeccao(result)
    relatorio = gerar_relatorio_md(result, mapa, ANALISE_REAL_MOCK)
    assert isinstance(relatorio, str)
    assert "Relatorio FASE 0" in relatorio


# === 8. gerar_relatorio_fase0.py main() when sim file doesn't exist ===

def test_main_missing_sim_file(tmp_path, monkeypatch):
    """main() must exit with non-zero code when sim file doesn't exist."""
    import scripts.gerar_relatorio_fase0 as mod

    monkeypatch.setattr(mod, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(sys, "argv", ["gerar_relatorio_fase0.py"])
    with pytest.raises(SystemExit) as exc_info:
        mod.main()
    assert exc_info.value.code != 0


# === 9. run_sim_v0.py CLI with --mes 13 (invalid month) ===

def test_cli_mes_13_rejected_by_argparse():
    """CLI with --mes 13 must be rejected by argparse (exit code 2, no traceback)."""
    result = subprocess.run(
        [sys.executable, "scripts/run_sim_v0.py", "-n", "5", "--mes", "13", "-o", "/tmp/test_mes13"],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "."},
    )
    assert result.returncode == 2
    assert "Traceback" not in result.stderr


# === 10. ic_bayesiano called with n_agendou > total ===

def test_ic_bayesiano_sucessos_gt_total():
    """ic_bayesiano with sucessos > total must not crash (defensive clamp)."""
    lo, hi = ic_bayesiano(5, 3)
    assert 0.0 <= lo <= hi <= 1.0
