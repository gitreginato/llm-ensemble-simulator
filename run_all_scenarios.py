#!/usr/bin/env python3
"""
Roda todas as variantes de todos os projetos em sequência.

Uso:
    python run_all_scenarios.py

Requisitos:
    - Backend .env configurado em launch-simulation/backend/.env
    - Venv: /home/lucas/Projetos/simulacao-multi-agent/.venv
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
RUNNER = ROOT / "run_scenario.py"

PROJECTS = {
    "devincriator": ["a", "b", "c", "d", "e", "f"],
    "slz_n8n": ["a", "b", "c", "d", "e", "f"],
}


def main():
    failures = []
    for project, variants in PROJECTS.items():
        for variant in variants:
            print(f"\n{'='*60}")
            print(f"Executando: {project} / variante {variant}")
            print(f"{'='*60}\n")
            result = subprocess.run(
                [str(VENV_PYTHON), str(RUNNER), project, variant],
                cwd=ROOT,
            )
            if result.returncode != 0:
                failures.append(f"{project}/{variant}")

    print(f"\n{'='*60}")
    print("RESUMO")
    print(f"{'='*60}")
    if failures:
        print(f"Falhas: {', '.join(failures)}")
        sys.exit(1)
    else:
        print("Todas as simulações completadas com sucesso.")


if __name__ == "__main__":
    main()
