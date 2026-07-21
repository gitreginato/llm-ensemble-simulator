#!/usr/bin/env python3
"""Estima tokens por simulacao do LaunchSimulation sem chamar API."""
import json
import sys
from pathlib import Path

# Adiciona o backend ao path para importar os prompts/templates
sys.path.insert(0, str(Path(__file__).parent / "launch-simulation" / "backend"))

try:
    import tiktoken
except ImportError:
    print("tiktoken nao disponivel")
    sys.exit(1)


def load_product(variant_path: Path) -> dict:
    product = {}
    with open(variant_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            product[k.strip()] = v.strip()
    product["price_usd"] = float(product["price_usd"])
    product["num_agents"] = int(product["num_agents"])
    return product


def count_tokens(text: str) -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def estimate_researcher(product: dict) -> tuple[int, int]:
    """Estima tokens do researcher: query expansion, quality check, synthesis."""
    # Query expansion prompt
    from app.agents.researcher import QUERY_EXPANSION_PROMPT, SYNTHESIS_PROMPT, QUALITY_CHECK_PROMPT
    
    query_input = (
        f"Product: {product['name']}\n"
        f"Description: {product['description']}\n"
        f"Target Market: {product['target_market']}\n\n"
        "Generate 3 search queries as instructed."
    )
    q_in = count_tokens(QUERY_EXPANSION_PROMPT) + count_tokens(query_input)
    q_out = 200  # 3 queries em JSON
    
    # Quality check (usa resultados formatados, estimamos 2000 tokens)
    qc_in = count_tokens(QUALITY_CHECK_PROMPT) + 2000
    qc_out = 150
    
    # Synthesis (usa resultados formatados, estimamos 3000 tokens)
    syn_in = count_tokens(SYNTHESIS_PROMPT) + 3000
    syn_out = 1000
    
    return q_in + qc_in + syn_in, q_out + qc_out + syn_out


def estimate_ethnographer(product: dict) -> tuple[int, int]:
    """Estima tokens do ethnographer."""
    from app.agents.ethnographer import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, BATCH_SIZE
    from app.models.schemas import Archetype, Channel
    
    total = product["num_agents"]
    archetypes = ", ".join(f'"{a.value}"' for a in Archetype)
    channels = ", ".join(f'"{c.value}"' for c in Channel)
    
    # Prompt de uma batch tipica (8 personas)
    count = min(BATCH_SIZE, total)
    prompt = USER_PROMPT_TEMPLATE.format(
        name=product["name"],
        price_usd=product["price_usd"],
        channel=product["channel"],
        description=product["description"][:600],
        target_market=product["target_market"] or "General consumer market",
        market_research="Live market context placeholder with synthesized competitors, pricing and audience pain points. " * 80,  # ~1200 tokens
        count=count,
        start_idx=1,
        end_idx=count,
        archetypes=archetypes,
        channels=channels,
    )
    in_per_batch = count_tokens(SYSTEM_PROMPT) + count_tokens(prompt)
    
    # Output: 8 personas completas (estimamos 260 tokens cada com base em sample real)
    out_per_batch = count * 260
    
    num_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
    return in_per_batch * num_batches, out_per_batch * num_batches


def estimate_launcher(num_agents: int) -> tuple[int, int]:
    """Estima tokens do launcher (reasoning batches)."""
    from app.agents.launcher import BATCH_SYSTEM, REASONING_BATCH_SIZE
    
    num_batches = (num_agents + REASONING_BATCH_SIZE - 1) // REASONING_BATCH_SIZE
    
    # Cada batch: 10 agents * ~150 tokens de contexto cada + prompt
    in_per_batch = count_tokens(BATCH_SYSTEM) + 10 * 150 + 500
    out_per_batch = 10 * 40  # 40 tokens por reasoning
    
    return in_per_batch * num_batches, out_per_batch * num_batches


def estimate_conversador(num_agents: int) -> tuple[int, int]:
    """Estima tokens do conversador."""
    from app.agents.conversador import BATCH_SYSTEM, POST_BATCH_SIZE
    
    # Assumimos ~60% de agentes ativos
    active = int(num_agents * 0.6)
    num_batches = (active + POST_BATCH_SIZE - 1) // POST_BATCH_SIZE
    
    in_per_batch = count_tokens(BATCH_SYSTEM) + 5 * 250 + 500
    out_per_batch = 5 * 200  # post + sentiment + upvotes + replies
    
    return in_per_batch * num_batches, out_per_batch * num_batches


def estimate_chronicler(num_agents: int) -> tuple[int, int]:
    """Estima tokens do chronicler."""
    from app.agents.chronicler import SYSTEM_PROMPT
    
    # Input: 30 interactions + 18 posts + prompt
    in_tokens = count_tokens(SYSTEM_PROMPT) + num_agents * 120 + int(num_agents * 0.6) * 150
    out_tokens = 1500  # 5 objecoes + 4 insights em JSON
    
    return in_tokens, out_tokens


def main():
    variant = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("scenarios/devincriator/variant_a.txt")
    product = load_product(variant)
    
    r_in, r_out = estimate_researcher(product)
    e_in, e_out = estimate_ethnographer(product)
    l_in, l_out = estimate_launcher(product["num_agents"])
    c_in, c_out = estimate_conversador(product["num_agents"])
    ch_in, ch_out = estimate_chronicler(product["num_agents"])
    
    total_in = r_in + e_in + l_in + c_in + ch_in
    total_out = r_out + e_out + l_out + c_out + ch_out
    total = total_in + total_out
    
    print(f"Variante: {variant}")
    print(f"Agents: {product['num_agents']}")
    print()
    print("Tokens por etapa:")
    print(f"  Researcher:    in={r_in:6,}  out={r_out:6,}")
    print(f"  Ethnographer:  in={e_in:6,}  out={e_out:6,}")
    print(f"  Launcher:      in={l_in:6,}  out={l_out:6,}")
    print(f"  Conversador:   in={c_in:6,}  out={c_out:6,}")
    print(f"  Chronicler:    in={ch_in:6,}  out={ch_out:6,}")
    print(f"  TOTAL:         in={total_in:6,}  out={total_out:6,}  = {total:6,} tokens")
    print()
    print("Custo estimado (OpenRouter Gemini 2.5 Flash Lite: $0.10/M in, $0.40/M out):")
    cost = (total_in / 1e6 * 0.10) + (total_out / 1e6 * 0.40)
    print(f"  ${cost:.4f} por simulacao")
    print(f"  ${cost * 12:.4f} para 12 simulacoes")


if __name__ == "__main__":
    main()
