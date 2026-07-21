"""Loader do config YAML do Simulation Army v2."""
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator


class ModelRole(BaseModel):
    model: str
    provider: str
    role: str
    role_description: str = ""
    # Fonte da chamada: "gocat" (HTTP) ou "kilocode" (subprocess CLI).
    # Default "gocat" para compatibilidade com scenarios existentes.
    source: str = "gocat"


class EnsembleConfig(BaseModel):
    models: list[ModelRole] = Field(..., min_length=1)

    @model_validator(mode="after")
    def _modelos_unicos(self) -> "EnsembleConfig":
        seen = set()
        for m in self.models:
            key = (m.model, m.provider)
            if key in seen:
                raise ValueError(f"ensemble: modelo duplicado {key}")
            seen.add(key)
        return self


class SynthesizerConfig(BaseModel):
    model: str
    provider: str


class BenchmarkConfig(BaseModel):
    conversao_geral_min: float = Field(..., ge=0, le=1)
    conversao_geral_max: float = Field(..., ge=0, le=1)
    agendamento_min: float = Field(..., ge=0, le=1)
    agendamento_max: float = Field(..., ge=0, le=1)
    whatsapp_reply_min: float = Field(..., ge=0, le=1)
    whatsapp_reply_max: float = Field(..., ge=0, le=1)
    fontes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _min_menor_que_max(self) -> "BenchmarkConfig":
        pairs = [
            (self.conversao_geral_min, self.conversao_geral_max, "conversao_geral"),
            (self.agendamento_min, self.agendamento_max, "agendamento"),
            (self.whatsapp_reply_min, self.whatsapp_reply_max, "whatsapp_reply"),
        ]
        for lo, hi, name in pairs:
            if lo >= hi:
                raise ValueError(f"benchmark {name}_min ({lo}) >= {name}_max ({hi})")
        return self


class GocatConfig(BaseModel):
    base_url: str = "http://127.0.0.1:8080"
    api_key_env: str = "GOCAT_API_KEY"
    api_key_default: str = "local-dev-key-change-me"
    timeout_seconds: int = Field(30, ge=1)
    max_retries: int = Field(2, ge=1)


class ExecutionConfig(BaseModel):
    seeds: list[int] = Field(default_factory=lambda: [42], min_length=1)
    delay_between_personas_seconds: float = Field(2.0, ge=0)
    delay_between_models_seconds: float = Field(0.5, ge=0)
    mes: int = Field(7, ge=1, le=12)
    devin_timeout_seconds: int = Field(90, ge=1)
    cline_timeout_seconds: int = Field(120, ge=1)
    kilocode_timeout_seconds: int = Field(90, ge=1)


class ScenarioConfig(BaseModel):
    code: str
    name: str
    project: str
    product_name: str
    description: str
    price_brl: float = Field(..., ge=0)
    price_model: str
    target_segment: str
    channel: str
    value_proposition: str
    pain_focus: str
    num_agents: int = Field(30, ge=1)
    persona_version: str = "v4"


class ArmyConfig(BaseModel):
    """Config completo do Simulation Army v2."""

    scenario: ScenarioConfig
    ensemble: EnsembleConfig
    synthesizer: SynthesizerConfig
    benchmark: BenchmarkConfig
    gocat: GocatConfig
    execution: ExecutionConfig


def load_config(path: str | Path) -> ArmyConfig:
    """Carrega config YAML e valida com pydantic."""
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return ArmyConfig(**raw)
