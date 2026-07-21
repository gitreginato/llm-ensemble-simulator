#!/usr/bin/env python3
"""Executa simulacoes avancadas de funil bidirecional."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.advanced_simulation import ScenarioConfig, run_scenario, build_report

ROOT = Path(__file__).parent.parent
OUTPUT_DIR = ROOT / "advanced_results"
OUTPUT_DIR.mkdir(exist_ok=True)


SCENARIOS = [
    # DevinCriator
    ScenarioConfig(
        project="devincriator",
        code="DC-AUTO-01",
        name="Identidade Visual para Lava-Jatos e Estetica Automotiva de Bairro",
        product_name="Owl Regent Studio - Lava-Jatos e Estetica Automotiva",
        description=(
            "Servico de branding para lava-jatos, estetica automotiva e polimento de bairro em Sao Luis. "
            "Criamos logotipo com cara de performance e cuidado, paleta escura/cromada, tipografia forte, "
            "aplicacao em faixada, banner de rua, posts para Instagram, cartao de visita e capa de destaque. "
            "Diferencial: deixa o lava-jato com cara de centro automotivo profissional, nao de esquina. "
            "Kit essencial: R$ 244. Kit completo: R$ 497. Entrega em 5 dias uteis."
        ),
        price_brl=244.0,
        price_model="one_time",
        target_segment="lava_jato",
        channel="social_media",
        value_proposition="Deixa o lava-jato com cara de centro automotivo profissional, atraindo clientes que pagam mais por estetica.",
        pain_focus="Lava-jatos de bairro tem fachada feia, posts amadores, nao passam confianca para servicos de polimento e higienizacao.",
    ),
    ScenarioConfig(
        project="devincriator",
        code="DC-AUTO-02",
        name="Identidade Visual para Oficinas Mecanicas de Bairro",
        product_name="Owl Regent Studio - Oficinas Mecanicas",
        description=(
            "Branding para oficinas mecanicas e autoeletricas de bairro em Sao Luis. "
            "Logotipo com estilo robusto e confiavel, paleta industrial, tipografia legivel, "
            "aplicacao em fachada, uniforme, cartao de visita, posts de antes/depois e capa do WhatsApp Business. "
            "Diferencial: comunicacao tecnica sem parecer amador. Kit essencial R$ 244, completo R$ 497."
        ),
        price_brl=244.0,
        price_model="one_time",
        target_segment="oficina",
        channel="social_media",
        value_proposition="Transmite confianca mecanica e profissionalismo para quem deixa o carro na oficina.",
        pain_focus="Oficinas de bairro perdem clientes para redes porque parecem desorganizadas e sem marca propria.",
    ),
    ScenarioConfig(
        project="devincriator",
        code="DC-VAL-01",
        name="Identidade Visual para Padarias e Confeitarias de Bairro",
        product_name="Owl Regent Studio - Padarias e Confeitarias",
        description=(
            "Servico de branding especializado para padarias e confeitarias de bairro. "
            "Logotipo artesanal, paleta quente, aplicacao em sacolas de pao, etiquetas, cardapio, posts Instagram. "
            "Kit essencial R$ 244, completo R$ 497. Entrega em 5 dias uteis."
        ),
        price_brl=244.0,
        price_model="one_time",
        target_segment="padaria",
        channel="social_media",
        value_proposition="Transforma a padaria em marca de bairro reconhecida, aumentando venda por impulso e fidelidade.",
        pain_focus="Padarias usam sacolas sem marca e perdem vendas para concorrentes que parecem mais artesanais.",
    ),
    ScenarioConfig(
        project="devincriator",
        code="DC-VAL-02",
        name="Identidade Visual para Food Trucks e Quiosques",
        product_name="Owl Regent Studio - Food Trucks e Quiosques",
        description=(
            "Branding para food trucks e quiosques de praia. Criamos identidade visual forte, visivel de longe, "
            "aplicada em lona, menu-board, embalagens e redes sociais. Kit essencial R$ 244, completo R$ 497."
        ),
        price_brl=244.0,
        price_model="one_time",
        target_segment="food_truck",
        channel="social_media",
        value_proposition="Marca reconhecivel de longe que atrai fila e facilita posts virais.",
        pain_focus="Food trucks competem visualmente com redes e precisam ser encontrados no meio da rua/praia.",
    ),

    # SLZ N8N Stack
    ScenarioConfig(
        project="slz_n8n",
        code="SLZ-AUTO-01",
        name="SLZ Seguranca Inteligente para Lojas de Carros Usados e Multimarcas",
        product_name="SLZ Seguranca Inteligente - Lojas de Carros Usados",
        description=(
            "Sistema de seguranca inteligente franquia EMIVE para lojas de carros usados e multimarcas em Sao Luis. "
            "Cobertura de estacionamento externo, vitrine de chaves, escritorio e caixa. "
            "Monitoramento 24h com verificacao por imagem, alertas por WhatsApp, botao de panico e pronta-resposta. "
            "Visita tecnica diagnostica: R$ 0,20. Proposta personalizada sem compromisso."
        ),
        price_brl=0.20,
        price_model="visit",
        target_segment="carros_usados",
        channel="word_of_mouth",
        value_proposition="Protege estoque de veiculos e chaves contra furto e vandalismo com monitoramento real, nao so cameras decorativas.",
        pain_focus="Lojas de carros usados tem estoque valioso exposto, pouca seguranca estruturada e medo de invasao noturna.",
    ),
    ScenarioConfig(
        project="slz_n8n",
        code="SLZ-AUTO-02",
        name="SLZ Seguranca Inteligente para Oficinas Mecanicas",
        product_name="SLZ Seguranca Inteligente - Oficinas Mecanicas",
        description=(
            "Sistema de seguranca inteligente para oficinas mecanicas em Sao Luis. "
            "Protege ferramentas, estoque de pecas, caixa e area de estacionamento de clientes. "
            "Cameras com analytics, alarme monitorado, controle de acesso, alertas no WhatsApp. "
            "Visita tecnica diagnostica: R$ 0,20. Mensalidades a partir de valores competitivos."
        ),
        price_brl=0.20,
        price_model="visit",
        target_segment="oficina",
        channel="word_of_mouth",
        value_proposition="Evita perda de ferramentas caras e pecas do estoque, com monitoramento que realmente aciona resposta.",
        pain_focus="Oficinas tem ferramentas caras, pecas no estoque e pouca protecao fora do horario comercial.",
    ),
    ScenarioConfig(
        project="slz_n8n",
        code="SLZ-AUTO-03",
        name="SLZ Seguranca Inteligente para Lava-Jatos e Estetica Automotiva",
        product_name="SLZ Seguranca Inteligente - Lava-Jatos",
        description=(
            "Seguranca inteligente para lava-jatos e estetica automotiva em Sao Luis. "
            "Monitoramento de equipamentos de pressao, aspiradores, produtos quimicos e chaves dos clientes. "
            "Alarme e cameras com alerta no celular do dono. Visita tecnica diagnostica: R$ 0,20."
        ),
        price_brl=0.20,
        price_model="visit",
        target_segment="lava_jato",
        channel="word_of_mouth",
        value_proposition="Protege equipamentos caros e chaves de clientes enquanto o dono descansa.",
        pain_focus="Lava-jatos deixam chaves de clientes, equipamentos e produtos desprotegidos durante a noite.",
    ),
]


def main():
    all_results = []
    for scenario in SCENARIOS:
        result = run_scenario(scenario)
        all_results.append(result)

        # Salvar JSON individual
        json_path = OUTPUT_DIR / f"{scenario.code}.json"
        json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  JSON salvo: {json_path}")

    # Salvar relatorio consolidado
    report = build_report(all_results)
    report_path = OUTPUT_DIR / "RELATORIO-AVANCADO.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"\nRelatorio salvo: {report_path}")

    # Salvar resultados consolidados
    consolidated_path = OUTPUT_DIR / "all_results.json"
    consolidated_path.write_text(json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Resultados consolidados: {consolidated_path}")


if __name__ == "__main__":
    main()
