#!/usr/bin/env python3
"""
Wrapper para rodar simulações do LaunchSimulation para diferentes cenários.

Uso:
    python run_scenario.py devincriator a
    python run_scenario.py slz_n8n b

Requisitos:
    - Backend .env configurado em launch-simulation/backend/.env
    - Venv ativado: /home/lucas/Projetos/simulacao-multi-agent/.venv
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
LAUNCH_DIR = ROOT / "launch-simulation"
SCENARIOS_DIR = ROOT / "scenarios"
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"


def run_scenario(project_name: str, variant: str):
    scenario_dir = SCENARIOS_DIR / project_name
    if not scenario_dir.exists():
        print(f"[ERRO] Projeto não encontrado: {scenario_dir}")
        print(f"Projetos disponíveis: {[d.name for d in SCENARIOS_DIR.iterdir() if d.is_dir()]}")
        sys.exit(1)

    input_src = scenario_dir / f"variant_{variant}.txt"
    if not input_src.exists():
        print(f"[ERRO] Variante não encontrada: {input_src}")
        print(f"Variantes disponíveis para {project_name}: {sorted([f.name for f in scenario_dir.glob('variant_*.txt')])}")
        sys.exit(1)

    input_dst = LAUNCH_DIR / "input.txt"

    print(f"[INFO] Copiando input de {input_src} -> {input_dst}")
    shutil.copy(input_src, input_dst)

    backend_dir = LAUNCH_DIR / "backend"
    backend_cmd = [str(VENV_PYTHON), "run.py"]

    print(f"[INFO] Iniciando backend em {backend_dir}...")
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Aguarda backend subir
    time.sleep(15)
    try:
        print(f"[INFO] Rodando simulação: {project_name} / variante {variant}")
        sim_cmd = [str(VENV_PYTHON), "simulate.py"]
        sim_proc = subprocess.run(
            sim_cmd,
            cwd=LAUNCH_DIR,
            capture_output=False,
            text=True,
        )
        if sim_proc.returncode != 0:
            print(f"[ERRO] Simulação falhou com código {sim_proc.returncode}")
    finally:
        print("[INFO] Parando backend...")
        backend_proc.terminate()
        try:
            backend_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_proc.kill()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Roda simulações LaunchSim")
    parser.add_argument("project", choices=["devincriator", "slz_n8n"], help="Projeto a simular")
    parser.add_argument("variant", help="Variante do cenário (a-f para devincriator, a-c para slz_n8n)")
    args = parser.parse_args()
    run_scenario(args.project, args.variant)
