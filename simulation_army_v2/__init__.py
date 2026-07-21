"""Simulation Army v2: ensemble heterogeneo de LLMs para simulacao de mercado.

Pipeline de 3 camadas:
1. Fan-out: N modelos processam a persona independentemente (async)
2. Sintetizador: 1 modelo frontier agrega as N respostas em decisao unica
3. Metricas: entropia, KL, pairwise disagreement, IC95%

Schema de decisao definido em schema.py.
"""
