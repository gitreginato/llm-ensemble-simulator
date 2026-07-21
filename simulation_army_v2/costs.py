"""Calculo de custo em USD por modelo e por run.

Tabela de precos por modelo (USD por 1M tokens).
Fonte: paginas de pricing oficiais (evidencia nivel A) e free tiers (evidencia S: teste real $0).

Categorias:
- free: modelos free tier, custo $0 (kilocode free, devin, gocat free tiers)
- paid: modelos pagos, preco por 1M tokens (input, output)
"""
from __future__ import annotations

# Precos em USD por 1M tokens (input, output).
# Modelos free = (0.0, 0.0).
# Modelos pagos: fonte = pagina de pricing oficial.
# Modelos com preco desconhecido = None (custo nao calculado).
PRICING: dict[str, tuple[float | None, float | None]] = {
    # === GOCAT (HTTP) ===
    # Cohere
    "command-r-plus-08-2024": (2.5, 10.0),  # cohere.com/pricing
    "command-a-03-2025": (2.0, 8.0),  # cohere.com/pricing
    # Groq
    "llama-3.3-70b-versatile": (0.59, 0.79),  # groq.com/pricing
    "qwen/qwen3.6-27b": (0.29, 0.39),  # groq.com/pricing (estimado, qwen-2.5-32b)
    # Gemini
    "gemini-2.5-flash": (0.075, 0.30),  # ai.google.dev/pricing
    # Nvidia
    "deepseek-ai/deepseek-v4-flash": (0.13, 0.30),  # build.nvidia.com (estimado)
    # SambaNova
    "Meta-Llama-3.3-70B-Instruct": (0.6, 1.2),  # sambanova.ai/pricing (estimado)
    # Kilo via gocat (free)
    "tencent/hy3:free": (0.0, 0.0),
    "kilo-auto/free": (0.0, 0.0),
    # SiliconFlow
    "deepseek-ai/DeepSeek-V3": (0.27, 1.10),  # siliconflow.cn/pricing

    # === KILOCODE (subprocess, free) ===
    "kilo/cohere/north-mini-code:free": (0.0, 0.0),
    "kilo/kilo-auto/free": (0.0, 0.0),
    "kilo/kwaipilot/kat-coder-pro-v2.5:free": (0.0, 0.0),
    "kilo/nvidia/nemotron-3-super-120b-a12b:free": (0.0, 0.0),
    "kilo/nvidia/nemotron-3-ultra-550b-a55b:free": (0.0, 0.0),
    "kilo/openrouter/free": (0.0, 0.0),
    "kilo/poolside/laguna-m.1:free": (0.0, 0.0),
    "kilo/poolside/laguna-xs-2.1:free": (0.0, 0.0),
    "kilo/stepfun/step-3.7-flash:free": (0.0, 0.0),
    "kilo/tencent/hy3:free": (0.0, 0.0),

    # === DEVIN (subprocess, free) ===
    "glm-5-2": (0.0, 0.0),
    "swe-1-7": (0.0, 0.0),
}


def calculate_cost_usd(
    model: str,
    prompt_tokens: int | None,
    completion_tokens: int | None,
) -> float | None:
    """Calcula custo em USD para 1 request.

    Custo = (prompt_tokens / 1_000_000) * preco_input
          + (completion_tokens / 1_000_000) * preco_output.

    Retorna None se:
    - modelo nao esta na tabela
    - tokens sao None (ex: devin CLI nao expoe tokens)
    - preco do modelo e None (desconhecido)
    """
    if prompt_tokens is None or completion_tokens is None:
        return None
    pricing = PRICING.get(model)
    if pricing is None:
        return None
    price_in, price_out = pricing
    if price_in is None or price_out is None:
        return None
    return (prompt_tokens / 1_000_000) * price_in + (completion_tokens / 1_000_000) * price_out


def calculate_run_cost(metadados_modelos: list[dict]) -> dict:
    """Calcula custo total e por modelo para 1 run do ensemble.

    metadados_modelos: lista de dicts com modelo, prompt_tokens, completion_tokens.
    Retorna {"custo_total_usd": float, "custo_por_modelo": {modelo: float}}.
    """
    custo_por_modelo: dict[str, float] = {}
    custo_total = 0.0
    for m in metadados_modelos:
        if "erro" in m:
            continue
        model = m.get("modelo", "")
        cost = calculate_cost_usd(
            model,
            m.get("prompt_tokens"),
            m.get("completion_tokens"),
        )
        if cost is not None:
            custo_por_modelo[model] = custo_por_modelo.get(model, 0.0) + cost
            custo_total += cost
    return {"custo_total_usd": round(custo_total, 6), "custo_por_modelo": custo_por_modelo}
