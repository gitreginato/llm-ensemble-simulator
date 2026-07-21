"""Bairros reais de Sao Luis-MA com perfil de risco e comercial.

Fontes:
- LeadJet: 95.066 empresas ativas, distribuicao por bairro
- SSP-MA: CVLI concentrado em Cidade Operaria, Coroadinho, Vila Embratel (42% das 4104 ocorrencias 2014-2019)
- G1: arrombamentos reais em Maranhao Novo, Joao Paulo, Cohama, Parque Jair, Vila Embratel
- Blog Estado: eixos comerciais Renascenca, Turu, Centro, Calhau, Cohama, Sao Cristovao, Sao Francisco, Vinhais, Olho DAgua

Cada bairro tem:
- empresas: numero aproximado de empresas ativas (LeadJet)
- risco: baixo / medio / alto / muito_alto (SSP-MA + G1)
- perfil: comercial_alto / comercial_medio / comercial_historico / residencial_comercial / periferia
- p_theft_base: probabilidade base de roubo recente (calibrado por risco)
- wtp_multiplier: multiplicador de WTP baseado no perfil comercial
"""
from __future__ import annotations

BAIRROS_SLZ: dict[str, dict] = {
    # === Alto fluxo comercial, menor risco relativo ===
    "Renascenca": {
        "empresas": 3865, "risco": "baixo", "perfil": "comercial_alto",
        "p_theft_base": 0.05, "wtp_multiplier": 1.15,
    },
    "Calhau": {
        "empresas": 3789, "risco": "medio", "perfil": "comercial_alto",
        "p_theft_base": 0.08, "wtp_multiplier": 1.10,
    },
    "Cohama": {
        "empresas": 2800, "risco": "medio", "perfil": "comercial_alto",
        "p_theft_base": 0.08, "wtp_multiplier": 1.10,
    },
    "Ponta do Farol": {
        "empresas": 700, "risco": "medio", "perfil": "comercial_alto",
        "p_theft_base": 0.07, "wtp_multiplier": 1.10,
    },
    # === Medio fluxo comercial ===
    "Turu": {
        "empresas": 4813, "risco": "medio", "perfil": "comercial_medio",
        "p_theft_base": 0.08, "wtp_multiplier": 1.00,
    },
    "Centro": {
        "empresas": 3259, "risco": "alto", "perfil": "comercial_historico",
        "p_theft_base": 0.15, "wtp_multiplier": 0.90,
    },
    "Sao Cristovao": {
        "empresas": 1500, "risco": "alto", "perfil": "comercial_medio",
        "p_theft_base": 0.15, "wtp_multiplier": 0.95,
    },
    "Vinhais": {
        "empresas": 1200, "risco": "medio", "perfil": "residencial_comercial",
        "p_theft_base": 0.08, "wtp_multiplier": 1.00,
    },
    "Joao Paulo": {
        "empresas": 1100, "risco": "alto", "perfil": "comercial_medio",
        "p_theft_base": 0.15, "wtp_multiplier": 0.95,
    },
    "Olho DAgua": {
        "empresas": 900, "risco": "alto", "perfil": "comercial_medio",
        "p_theft_base": 0.15, "wtp_multiplier": 0.95,
    },
    # === Periferia, risco alto (CVLI concentrado aqui) ===
    "Cidade Operaria": {
        "empresas": 800, "risco": "muito_alto", "perfil": "periferia",
        "p_theft_base": 0.25, "wtp_multiplier": 0.80,
    },
    "Coroadinho": {
        "empresas": 600, "risco": "muito_alto", "perfil": "periferia",
        "p_theft_base": 0.25, "wtp_multiplier": 0.80,
    },
    "Vila Embratel": {
        "empresas": 500, "risco": "muito_alto", "perfil": "periferia",
        "p_theft_base": 0.25, "wtp_multiplier": 0.80,
    },
}

# Sazonalidade de Sao Luis
# Fonte: conhecimento local + padrao de varejo
SAZONALIDADE_SLZ: dict[str, dict] = {
    "alta": {
        "meses": [6, 12],  # Sao Joao (junho), Natal (dezembro)
        "revenue_multiplier": 1.30,
        "p_theft_multiplier": 1.20,  # mais caixa = mais risco
    },
    "media": {
        "meses": [1, 2, 3, 4, 5, 7, 8, 9, 10, 11],
        "revenue_multiplier": 1.00,
        "p_theft_multiplier": 1.00,
    },
    "black_friday": {
        "meses": [11],  # novembro: Black Friday (pico de vendas varejo)
        "revenue_multiplier": 1.15,
        "p_theft_multiplier": 1.10,
    },
}


def get_sazonalidade(mes: int) -> dict:
    """Retorna multiplicadores de sazonalidade para o mes (1-12)."""
    if mes in SAZONALIDADE_SLZ["alta"]["meses"]:
        return SAZONALIDADE_SLZ["alta"]
    if mes in SAZONALIDADE_SLZ["black_friday"]["meses"]:
        return SAZONALIDADE_SLZ["black_friday"]
    return SAZONALIDADE_SLZ["media"]


def get_bairro(nome: str) -> dict:
    """Retorna dados do bairro ou um default generico."""
    return BAIRROS_SLZ.get(nome, {
        "empresas": 1000, "risco": "medio", "perfil": "comercial_medio",
        "p_theft_base": 0.10, "wtp_multiplier": 1.00,
    })


def listar_bairros_por_risco(risco: str) -> list[str]:
    """Lista bairros com determinado nivel de risco."""
    return [nome for nome, dados in BAIRROS_SLZ.items() if dados["risco"] == risco]


def listar_bairros_por_perfil(perfil: str) -> list[str]:
    """Lista bairros com determinado perfil comercial."""
    return [nome for nome, dados in BAIRROS_SLZ.items() if dados["perfil"] == perfil]
