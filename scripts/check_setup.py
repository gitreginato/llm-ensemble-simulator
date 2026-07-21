#!/usr/bin/env python3
"""Smoke test: verifica que o ambiente Simulation Army v2 esta pronto.

Checa: deps Python, gocat /health, 4 modelos do ensemble respondem 200.
Uso: .venv/bin/python scripts/check_setup.py
"""
import os
import sys
import httpx

GOCAT_URL = os.getenv("GOCAT_BASE_URL", "http://127.0.0.1:8080")
GOCAT_KEY = os.getenv("GOCAT_API_KEY", "local-dev-key-change-me")

ENSEMBLE_MODELS = [
    ("gpt-4o-mini", "github", "pragmatico"),
    ("command-r-plus-08-2024", "cohere", "conservador"),
    ("llama-3.3-70b-versatile", "groq", "conversacional"),
    ("gpt-4o-mini", "github", "sintetizador"),
]


def check_deps() -> bool:
    deps = {"httpx": None, "pydantic": None, "scipy": None, "numpy": None, "yaml": None}
    for mod in deps:
        try:
            m = __import__(mod)
            deps[mod] = getattr(m, "__version__", "?")
        except ImportError as e:
            print(f"[FAIL] dep {mod}: {e}")
            return False
    print(f"[OK] deps: {deps}")
    return True


def check_gocat() -> bool:
    try:
        r = httpx.get(f"{GOCAT_URL}/health", timeout=5)
        if r.status_code != 200:
            print(f"[FAIL] gocat /health status={r.status_code} body={r.text[:100]}")
            return False
        data = r.json()
        if data.get("status") == "ok":
            print(f"[OK] gocat /health: {data}")
            return True
        print(f"[FAIL] gocat /health: status field not 'ok': {data}")
        return False
    except Exception as e:
        print(f"[FAIL] gocat /health: {e}")
        return False


def check_model(model: str, role: str) -> bool:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Responda apenas: OK"}],
        "max_tokens": 10,
    }
    headers = {"Authorization": f"Bearer {GOCAT_KEY}", "Content-Type": "application/json"}
    try:
        r = httpx.post(f"{GOCAT_URL}/v1/chat/completions", json=payload, headers=headers, timeout=30)
        if r.status_code != 200:
            try:
                err = r.json().get("error", {}).get("message", r.text[:100])
            except Exception:
                err = r.text[:100]
            print(f"[FAIL] {model} ({role}): status={r.status_code} err={err}")
            return False
        data = r.json()
        choices = data.get("choices", [])
        if not choices:
            print(f"[FAIL] {model} ({role}): choices vazio")
            return False
        content = choices[0].get("message", {}).get("content", "")
        if "OK" not in content.strip().upper():
            print(f"[FAIL] {model} ({role}): resposta inesperada '{content.strip()}'")
            return False
        print(f"[OK] {model} ({role}): '{content.strip()}'")
        return True
    except Exception as e:
        print(f"[FAIL] {model} ({role}): {e}")
        return False


def main() -> int:
    print("=== Simulation Army v2 - Setup Check ===\n")
    ok = True
    print("[1/3] Dependencias Python:")
    ok &= check_deps()
    print("\n[2/3] Gocat gateway:")
    ok &= check_gocat()
    print("\n[3/3] Modelos do ensemble:")
    for model, provider, role in ENSEMBLE_MODELS:
        ok &= check_model(model, role)
    print(f"\n{'='*40}\nRESULTADO: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
