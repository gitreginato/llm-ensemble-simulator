"""Testes para pitch_templates.py."""
from simulation_army_v2.pitch_templates import (
    BENEFICIOS_EMIVE,
    CENARIOS_TREINAMENTO,
    DOR_POR_NICHO,
    OBJECAO_RESPOSTA,
    SCRIPTS_ABORDAGEM,
    TOM_DE_VOZ,
    avaliar_competencias,
    gerar_objecao_resposta,
    gerar_pitch,
)
from simulation_army_v2.personas_v5 import generate_personas_v5


def test_dor_por_nicho_tem_26_nichos():
    assert len(DOR_POR_NICHO) == 26
    for nicho in ["loja_roupas", "bar", "farmacia", "oficina",
                   "clinica", "consultorio_odonto", "pet_shop", "academia",
                   "estacionamento", "mecanica_diesel", "lava_jato", "borracharia",
                   "laboratorio", "clinica_veterinaria", "fisioterapia", "optica",
                   "estetica", "estudio_tatuagem"]:
        assert nicho in DOR_POR_NICHO


def test_beneficios_emive_tem_8():
    assert len(BENEFICIOS_EMIVE) == 8
    assert "anti_falso_alarme" in BENEFICIOS_EMIVE
    assert "sem_obras" in BENEFICIOS_EMIVE
    assert "redundancia_4_canais" in BENEFICIOS_EMIVE


def test_tom_de_voz_tem_8_atributos():
    assert len(TOM_DE_VOZ) == 8


def test_scripts_abordagem_tem_3_mercados():
    assert "mercado_a" in SCRIPTS_ABORDAGEM
    assert "mercado_c_avisado" in SCRIPTS_ABORDAGEM
    assert "mercado_c_nao_avisado" in SCRIPTS_ABORDAGEM


def test_cenarios_treinamento_tem_5():
    assert len(CENARIOS_TREINAMENTO) == 5
    for cen_id in ["CEN-01", "CEN-02", "CEN-03", "CEN-04", "CEN-05"]:
        assert cen_id in CENARIOS_TREINAMENTO


def test_objecao_resposta_tem_10():
    assert len(OBJECAO_RESPOSTA) == 10
    for obj in ["existing_solution", "budget", "skepticism", "need_lack",
                "timing", "complexity", "ticket_alto", "contract_fear",
                "area_externa", "concorrencia_local"]:
        assert obj in OBJECAO_RESPOSTA


def test_gerar_pitch_persona():
    personas = generate_personas_v5(n=5, seed=42)
    pitch = gerar_pitch(personas[0])
    assert len(pitch) > 100
    assert "15 a 20 minutos" in pitch


def test_gerar_pitch_whatsapp():
    personas = generate_personas_v5(n=5, seed=42)
    pitch = gerar_pitch(personas[0], canal="whatsapp")
    assert "whatsapp" in pitch.lower() or "aqui" in pitch.lower()


def test_gerar_pitch_mercado_a():
    personas = generate_personas_v5(n=5, seed=42)
    pitch = gerar_pitch(personas[0], mercado="mercado_a")
    assert "feedback" in pitch.lower() or "conceito smart" in pitch.lower()


def test_gerar_pitch_nao_menciona_preco():
    """Regra do blueprint: nunca explicar precos por telefone."""
    personas = generate_personas_v5(n=10, seed=42)
    for p in personas:
        pitch = gerar_pitch(p)
        assert "294" not in pitch, "Pitch nao deve mencionar o valor da mensalidade"
        assert "R$" not in pitch or "R$ 1" not in pitch  # so visita R$ 1 ok


def test_gerar_pitch_cita_bairro():
    personas = generate_personas_v5(n=5, seed=42)
    for p in personas:
        pitch = gerar_pitch(p)
        assert p.bairro in pitch, f"Pitch deve citar bairro {p.bairro}"


def test_gerar_objecao_resposta_existing_solution():
    resposta = gerar_objecao_resposta("existing_solution")
    assert "monitoramento" in resposta.lower() or "24h" in resposta.lower()


def test_gerar_objecao_resposta_budget():
    resposta = gerar_objecao_resposta("budget")
    assert "mensalidade" in resposta.lower() or "central" in resposta.lower()


def test_gerar_objecao_resposta_desconhecida():
    """Objecao desconhecida usa default (skepticism)."""
    resposta = gerar_objecao_resposta("objecao_inexistente")
    assert len(resposta) > 10


def test_avaliar_competencias_5_metricas():
    pitch = "Bom dia Joao, Conceito Smart de Tecnologia. 15 a 20 minutos, sem compromisso. Terca ou quarta?"
    scores = avaliar_competencias(pitch, "agendou", [])
    assert "conexao_rapport" in scores
    assert "foco_agendamento" in scores
    assert "geracao_curiosidade" in scores
    assert "contorno_objecoes" in scores
    assert "fechamento_compromisso" in scores
    assert all(0 <= v <= 10 for v in scores.values())


def test_avaliar_competencias_pitch_bom():
    pitch = (
        "Bom dia Joao, tudo certo? Conceito Smart de Tecnologia, "
        "tecnologia de 1 mundo. Quero te apresentar, sem compromisso. "
        "15 a 20 minutos, terca ou quarta? Manha ou tarde?"
    )
    scores = avaliar_competencias(pitch, "agendou", [])
    assert scores["foco_agendamento"] >= 9
    assert scores["geracao_curiosidade"] >= 8
    assert scores["fechamento_compromisso"] >= 8


def test_avaliar_competencias_pitch_ruim():
    pitch = "Compre nosso sistema de seguranca agora."
    scores = avaliar_competencias(pitch, "ignorou", ["budget"])
    assert scores["foco_agendamento"] < 7
    assert scores["geracao_curiosidade"] < 7
