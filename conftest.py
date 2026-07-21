"""Configura pytest path para importar simulation_army_v2 do repo root."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
