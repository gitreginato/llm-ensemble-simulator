"""Schema pydantic para decisao de persona e decisao agregada do Simulation Army v2.

DecisaoPersona: resposta de 1 modelo para 1 persona.
DecisaoAggregada: saida do sintetizador apos agregar N DecisaoPersona.

Categorias de objecao reutilizadas do advanced_simulation.py para compatibilidade:
budget, timing, existing_solution, skepticism, complexity, need_lack.
"""
from typing import Literal

from pydantic import BaseModel, Field, model_validator

# Estagios do funil AIDA simplificados para o schema v2.
# "ignorou" = nem visualizou (awareness false).
# "visualizou" = awareness true mas nao clicou.
# "clicou" = interest true mas nao agendou.
# "agendou" = purchased true (conversao final).
DecisaoFunil = Literal["visualizou", "clicou", "agendou", "ignorou"]

# Categorias de objecao, alinhadas com advanced_simulation.py:399.
# "none" removido: lista vazia = sem objecoes (evita misturar none com objecoes reais).
CategoriaObjecao = Literal[
    "budget",
    "timing",
    "existing_solution",
    "skepticism",
    "complexity",
    "need_lack",
    "area_externa",
    "concorrencia_local",
    "contract_fear",
    "ticket_alto",
]


class DecisaoPersona(BaseModel):
    """Resposta de 1 modelo do ensemble para 1 persona."""

    decisao: DecisaoFunil = Field(..., description="Estagio final do funil atingido")
    wtp: float = Field(..., ge=0, description="Willingness to pay em R$")
    sentimento: float = Field(..., ge=-1.0, le=1.0, description="Sentimento -1 a +1")
    objecoes: list[CategoriaObjecao] = Field(
        default_factory=list, description="Categorias de objecao citadas (sem duplicatas)"
    )
    confianca: float = Field(
        ..., ge=0.0, le=1.0, description="Auto-avaliacao de confianca do modelo 0 a 1"
    )
    raciocinio: str = Field(..., min_length=1, description="Justificativa 1-3 frases")
    modelo: str = Field(..., description="Nome do modelo (preenchido pelo orquestrador)")

    @model_validator(mode="after")
    def _dedup_objecoes(self) -> "DecisaoPersona":
        if len(self.objecoes) != len(set(self.objecoes)):
            self.objecoes = list(dict.fromkeys(self.objecoes))
        return self


class ConcordanciaPar(BaseModel):
    """Par de modelos e se concordaram na decisao final."""

    modelo_a: str
    modelo_b: str
    concordam: bool

    @model_validator(mode="after")
    def _modelos_distintos(self) -> "ConcordanciaPar":
        if self.modelo_a == self.modelo_b:
            raise ValueError("modelo_a e modelo_b devem ser distintos")
        return self


class DecisaoAggregada(BaseModel):
    """Saida do sintetizador de consenso apos agregar N DecisaoPersona."""

    decisao_final: DecisaoFunil = Field(..., description="Decisao agregada do funil")
    wtp_medio: float = Field(..., ge=0, description="Media de WTP em R$")
    sentimento_medio: float = Field(..., ge=-1.0, le=1.0, description="Sentimento medio")
    objecoes_consolidadas: list[CategoriaObjecao] = Field(
        default_factory=list, description="Objecoes citadas por qualquer modelo"
    )
    divergence_score: float = Field(
        ..., ge=0.0, le=1.0, description="0=unanime, 1=split total"
    )
    concordancia: list[ConcordanciaPar] = Field(
        default_factory=list, description="Pares de modelos e concordancia"
    )
    confianca_agregada: float = Field(..., ge=0.0, le=1.0)
    raciocinio_sintese: str = Field(..., min_length=1, description="Sintese do consenso")


def divergence_score_from_decisoes(decisoes: list[DecisaoPersona]) -> float:
    """Calcula divergence score: 0 se todas iguais, 1 se todas diferentes.

    Formula: (n_distintas - 1) / (n_total - 1) para n_total > 1, else 0.0.
    Raise ValueError se lista vazia (mascara falha de coleta).
    """
    if len(decisoes) == 0:
        raise ValueError("divergence_score: lista de decisoes vazia")
    if len(decisoes) == 1:
        return 0.0
    distintas = len({d.decisao for d in decisoes})
    return (distintas - 1) / (len(decisoes) - 1)
