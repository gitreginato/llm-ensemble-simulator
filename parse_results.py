#!/usr/bin/env python3
"""Parseia run_all_scenarios.log e gera relatorio comparativo."""
import re
from pathlib import Path
from collections import defaultdict

LOG_PATH = Path("run_all_scenarios.log")


def extract_blocks(text: str) -> list[dict]:
    """Extrai cada simulacao do log como bloco."""
    blocks = []
    # Split por launchsim header
    pattern = r"(═+\s+LaunchSim\s+·\s+.*?)(?=═+\s+LaunchSim|\Z)"
    matches = re.findall(pattern, text, re.DOTALL)
    for match in matches:
        block = match.strip()
        if not block:
            continue
        # Nome do produto
        name_match = re.search(r"LaunchSim\s+·\s+(.*)", block)
        name = name_match.group(1).strip() if name_match else "Unknown"
        # Metricas
        metrics = {}
        for key in ["Viewed", "Clicked", "Purchased", "Conversion", "Avg sentiment"]:
            m = re.search(rf"{key}\s+:\s+(.+)", block)
            if m:
                metrics[key] = m.group(1).strip()
        # Objecoes
        objections = []
        obj_section = re.search(r"TOP OBJECTIONS\s+═+\s+(.*?)(?=STRATEGIC INSIGHTS|═+\s+DONE|$)", block, re.DOTALL)
        if obj_section:
            obj_text = obj_section.group(1)
            for line in obj_text.splitlines():
                m = re.search(r"#\d+\s+\[(\d+)x\]\s+(.+)", line)
                if m:
                    objections.append((int(m.group(1)), m.group(2).strip()))
        # Insights
        insights = []
        ins_section = re.search(r"STRATEGIC INSIGHTS\s+═+\s+(.*?)(?=═+\s+DONE|═+\s+Full results|$)", block, re.DOTALL)
        if ins_section:
            for line in ins_section.group(1).splitlines():
                line = line.strip()
                if line.startswith(("1.", "2.", "3.", "4.", "5.")):
                    insights.append(line[2:].strip())
        blocks.append({
            "name": name,
            "metrics": metrics,
            "objections": objections,
            "insights": insights,
        })
    return blocks


def main():
    text = LOG_PATH.read_text(encoding="utf-8")
    blocks = extract_blocks(text)
    print(f"Simulacoes encontradas: {len(blocks)}")

    # Map variant names
    variant_map = {
        "Owl Regent Studio - Identidade Visual para Padarias e Confeitarias de Bairro": ("devincriator", "a", "Padarias/confeitarias"),
        "Owl Regent Studio - Identidade Visual para Saloes de Beleza e Esteticas": ("devincriator", "b", "Saloes de beleza/esteticas"),
        "Owl Regent Studio - Identidade Visual para Bares e Lanchonetes de Bairro": ("devincriator", "c", "Bares/lanchonetes"),
        "Owl Regent Studio - Identidade Visual para Profissionais Liberais (Personal Trainer, Consultor, Nutricionista)": ("devincriator", "d", "Profissionais liberais"),
        "Owl Regent Studio - Identidade Visual para Lojas de Roupas e Boutiques de Bairro": ("devincriator", "e", "Lojas de roupas/boutiques"),
        "Owl Regent Studio - Identidade Visual para Food Trucks e Quiosques de Praia": ("devincriator", "f", "Food trucks/quiosques"),
        "SLZ Seguranca Inteligente para Padarias e Mercearias de Sao Luis - Protecao do Estoque e Abertura Segura": ("slz_n8n", "a", "Padarias/mercearias"),
        "SLZ Seguranca Inteligente para Saloes de Beleza e Esteticas de Sao Luis - Protecao no Horario Noturno": ("slz_n8n", "b", "Saloes de beleza/esteticas"),
        "SLZ Seguranca Inteligente para Lojas de Roupas e Calcados de Sao Luis - Protecao de Vitrine e Estoque": ("slz_n8n", "c", "Lojas de roupas/calcados"),
        "SLZ Seguranca Inteligente para Bares e Restaurantes de Sao Luis - Protecao de Caixa e Horario Noturno": ("slz_n8n", "d", "Bares/restaurantes"),
        "SLZ Seguranca Inteligente para Farmacias e Drogarias de Sao Luis - Protecao de Medicamentos Controlados e Caixa": ("slz_n8n", "e", "Farmacias/drogarias"),
        "SLZ Seguranca Inteligente para Residencias de Sao Luis - Tranquilidade para a Familia 24h": ("slz_n8n", "f", "Residencias"),
    }

    # Criar report
    lines = ["# Relatorio Comparativo - Simulacoes de Mercado\n"]
    lines.append(f"Total de simulacoes: {len(blocks)}\n")
    lines.append("\n")

    # DevinCriator
    lines.append("## DevinCriator / Owl Regent Studio\n\n")
    lines.append("| Var | Segmento | Viewed | Clicked | Purchased | Conversao | Sentimento | Principal objecao | Insight chave |\n")
    lines.append("|-----|----------|--------|---------|-----------|-----------|------------|-------------------|---------------|\n")
    for b in blocks:
        if b["name"] not in variant_map:
            continue
        proj, var, segmento = variant_map[b["name"]]
        if proj != "devincriator":
            continue
        m = b["metrics"]
        viewed = m.get("Viewed", "")
        clicked = m.get("Clicked", "")
        purchased = m.get("Purchased", "")
        conv = m.get("Conversion", "")
        sent = m.get("Avg sentiment", "")
        obj = b["objections"][0][1] if b["objections"] else ""
        ins = b["insights"][0] if b["insights"] else ""
        lines.append(f"| {var} | {segmento} | {viewed} | {clicked} | {purchased} | {conv} | {sent} | {obj} | {ins} |\n")

    # SLZ
    lines.append("\n## SLZ N8N Stack\n\n")
    lines.append("| Var | Segmento | Viewed | Clicked | Purchased | Agendamento* | Sentimento | Principal objecao | Insight chave |\n")
    lines.append("|-----|----------|--------|---------|-----------|--------------|------------|-------------------|---------------|\n")
    for b in blocks:
        if b["name"] not in variant_map:
            continue
        proj, var, segmento = variant_map[b["name"]]
        if proj != "slz_n8n":
            continue
        m = b["metrics"]
        viewed = m.get("Viewed", "")
        clicked = m.get("Clicked", "")
        purchased = m.get("Purchased", "")
        conv = m.get("Conversion", "")
        sent = m.get("Avg sentiment", "")
        obj = b["objections"][0][1] if b["objections"] else ""
        ins = b["insights"][0] if b["insights"] else ""
        lines.append(f"| {var} | {segmento} | {viewed} | {clicked} | {purchased} | {conv} | {sent} | {obj} | {ins} |\n")

    # Top objecoes consolidadas
    all_objections = defaultdict(int)
    for b in blocks:
        for freq, obj in b["objections"]:
            all_objections[obj] += freq

    lines.append("\n## Top objecoes consolidadas (todos os projetos)\n\n")
    for obj, freq in sorted(all_objections.items(), key=lambda x: x[1], reverse=True)[:10]:
        lines.append(f"- {obj}: {freq}x\n")

    # Salvar
    report_path = Path("RELATORIO-SIMULACOES.md")
    report_path.write_text("".join(lines), encoding="utf-8")
    print(f"Relatorio salvo em: {report_path}")


if __name__ == "__main__":
    main()
