"""Pitch templates por nicho baseados no documento EMIVE.

Fontes autorizadas: APENAS AGREGADO_EMPRESA.md e BLUEPRINT_SIMULACOES.md.

Estrutura:
- DOR_POR_NICHO: dor especifica de cada nicho em Sao Luis
- BENEFICIOS_EMIVE: beneficios mapeados do documento (8 equipamentos)
- TOM_DE_VOZ: 8 atributos do manual de marca
- SCRIPTS_ABORDAGEM: 3 scripts do AGREGADO (Mercado A, C avisado, C nao avisado)
- CENARIOS_TREINAMENTO: 5 cenarios do BLUEPRINT
- OBJECAO_RESPOSTA: objecoes do blueprint + respostas
"""
from __future__ import annotations

from simulation_army_v2.personas_v5 import PersonaV5


class _SafeFormatDict(dict):
    """Dict subclass that returns empty string for missing keys in str.format_map.

    Prevents KeyError when a SCRIPTS_ABORDAGEM template has a placeholder
    not provided in the format call.
    """

    def __missing__(self, key: str) -> str:
        return ""


# === DOR POR NICHO (adaptado de Sao Luis) ===
DOR_POR_NICHO: dict[str, str] = {
    # Perenes
    "loja_roupas": "Arrombamento noturno com quebra de vitrine e roubo de estoque",
    "loja_calcados": "Arrombamento noturno com quebra de vitrine e roubo de estoque",
    "bar": "Movimento noturno com caixa aberto, saida de clientes e risco de assalto",
    "autopecas": "Estoque valioso de pecas e ferramentas, arrombamento noturno de deposito",
    "mercearia": "Furto de clientes em corredores, caixa exposto, estoque perecivel",
    "farmacia": "Furto de medicamentos controlados, compliance, caixa exposto",
    "hamburgueria": "Caixa noturno, saida de caixa com valores, movimento intenso",
    "oficina": "Ferramentas caras expostas, veiculos de clientes, arrombamento noturno",
    # Novos perenes
    "mercadinho": "Furto de clientes em corredores, caixa exposto, estoque perecivel",
    "clinica": "Equipamentos caros, medicamentos controlados, acesso de pacientes e funcionarios",
    "consultorio_odonto": "Equipamentos odontologicos caros, acesso de pacientes, medicamentos",
    "pet_shop": "Furto de racao e produtos, animais valiosos, caixa exposto",
    "barbearia": "Equipamentos profissionais, caixa exposto, movimento intenso",
    "salao": "Equipamentos e produtos caros, caixa exposto, fluxo de clientes",
    "academia": "Equipamentos caros, acessos de alunos, vestuarios, caixa",
    # Novos volateis
    "restaurante": "Caixa noturno, saida de caixa com valores, estoque de bebidas e alimentos",
    # Automotivo (perenes, alto valor)
    "estacionamento": "Furto de veiculos e acessorios, saida de caixa, vandalismo noturno",
    "mecanica_diesel": "Ferramentas e pecas caras expostas, veiculos de clientes, arrombamento noturno",
    "lava_jato": "Caixa exposto, equipamentos de pressao, produtos quimicos, furto noturno",
    "borracharia": "Estoque de pneus valioso, ferramentas, caixa exposto, arrombamento",
    # Saude (perenes, alto valor)
    "laboratorio": "Equipamentos de alto valor, medicamentos controlados, dados de pacientes, acesso restrito",
    "clinica_veterinaria": "Medicamentos controlados, equipamentos, animais internados, acesso de clientes",
    "fisioterapia": "Equipamentos caros, acesso de pacientes, medicamentos, horarios vagos",
    "optica": "Estoque de oculos e lentes de alto valor, arrombamento de vitrine, caixa exposto",
    # Servicos pessoais (perenes)
    "estetica": "Equipamentos de alto valor (laser, radiofrequencia), produtos caros, caixa exposto",
    "estudio_tatuagem": "Equipamentos profissionais, tintas e materiais, caixa exposto, acesso de clientes",
}

# === BENEFICIOS EMIVE (do AGREGADO_EMPRESA.md, mapeados para objecoes do BLUEPRINT) ===
BENEFICIOS_EMIVE: dict[str, str] = {
    "anti_falso_alarme": "Sensor com acelerometro de 5 niveis que filtra barulhos externos (caminhao de som, latidos, rojoes)",
    "sem_obras": "Tecnologia sem fio criptografada, instalacao sem furadeiras e fios espalhados",
    "redundancia_4_canais": "Central inviolavel com 4 canais: Wifi, Ethernet, GPRS e linha telefonica. Se um cai, o outro mantem",
    "audio_bidirecional": "Camera com microfone e alto-falante integrados. Voce fala e ouve o ambiente de qualquer lugar",
    "inibicao_36x": "Placa visivel da Emive gera 36 vezes mais seguranca. Criminosos veem e desistem antes de agir",
    "senha_coacao": "Teclado com senha silenciosa de emergencia. Se assaltarem na entrada, voce aciona ajuda sem eles saberem",
    "app_com_extras": "App Emive com arme/desarme remoto, cameras ao vivo, deslocamento monitorado e alerta de esquecimento",
    "autonomia_10h": "Bateria interna de ate 10 horas. Se cortarem a energia, o sistema continua funcionando",
}

# === TOM DE VOZ (do AGREGADO_EMPRESA.md, 8 atributos) ===
TOM_DE_VOZ: list[str] = [
    "Seria mas amigavel",
    "Objetiva mas nao tecnica",
    "Assertiva mas nao pretensiosa",
    "Realista mas acolhedora",
    "Pontual mas empatica",
    "Agil mas atenciosa",
    "Segura mas nao arrogante",
    "Realista sem sensacionalismo",
]

# === SCRIPTS DE ABORDAGEM (do AGREGADO_EMPRESA.md) ===
SCRIPTS_ABORDAGEM: dict[str, str] = {
    "mercado_a": (
        "Bom dia {nome}, tudo certo? Estou te ligando porque iniciei um novo projeto "
        "e estou trabalhando com um Conceito Smart de Tecnologia. Fica um pouco vago "
        "pelo telefone, mas basicamente estou desenvolvendo projetos de tecnologia "
        "voltada para seguranca pessoal e patrimonial, uma ferramenta totalmente inovadora, "
        "muito usada em paises de 1 mundo. Lembrei de voce por conta da sua {imovel}. "
        "Quero ter o prazer de te apresentar, fica tranquilo que voce nao vai ter que "
        "comprar nada nao, a nao ser que queira. Mas o principal objetivo e seu feedback. "
        "Como esta sua agenda para batermos um papo de 15 a 20 minutos na semana que vem? "
        "Fica melhor pela manha ou tarde? Terca ou quarta?"
    ),
    "mercado_c_avisado": (
        "Bom dia, tudo bem? Quem fala e {vendedor}. Voce pode falar por um minuto? "
        "Estou entrando em contato por intermedio do {recomendante}. Acredito que ele "
        "tenha mencionado que eu ligaria. Ele chegou a avisa-lo? "
        "Que otimo. Estou ligando so para saber que dia podemos bater um papo rapido "
        "para apresentar o trabalho que desenvolvo. O {recomendante} falou que voce "
        "{perfil_conexao}. Para voce fica melhor terca ou quarta? Manha ou tarde?"
    ),
    "mercado_c_nao_avisado": (
        "Bom dia, tudo bem? Quem fala e {vendedor}. Voce pode falar por um minuto? "
        "Estou ligando por indicacao do {recomendante}. Provavelmente na correria ele "
        "nao teve tempo de te avisar, mas no proximo contato de voces ele certamente "
        "comentara. Eu desenvolvi um trabalho para ele envolvendo tecnologia, seguranca "
        "e geracao de dados. E um pouco dificil explicar por telefone por ser algo "
        "personalizado, mas ele me disse que voces sao amigos. "
        "Gostaria de saber sua disponibilidade de 15 a 20 minutos para uma apresentacao "
        "rapida, sem compromisso comercial. Fica melhor segunda ou quarta? Manha ou tarde?"
    ),
}

# === OBJECOES E RESPOSTAS (do BLUEPRINT + AGREGADO + novas) ===
OBJECAO_RESPOSTA: dict[str, str] = {
    "existing_solution": (
        "Entendo que voce ja tem cameras. A diferenca e que o sistema Emive tem "
        "monitoramento humano 24h com acao imediata, nao so gravacao. Alem disso, "
        "as cameras tem audio bidirecional. Mas o melhor e ver na visita, posso "
        "passar la para te mostrar a diferenca?"
    ),
    "budget": (
        "Entendo o seu ponto sobre mensalidade. O valor da Central 24h e que ela "
        "substitui o custo de um seguranca privado, que seria bem mais caro. "
        "Na visita eu te mostro como funciona, sem compromisso."
    ),
    "ticket_alto": (
        "Entendo que o compromisso de 3 anos parece grande. Mas a mensalidade e "
        "menor que um seguranca privado e o sistema e seu durante todo o contrato. "
        "Na visita eu te mostro o custo-beneficio real, sem compromisso."
    ),
    "contract_fear": (
        "Faz sentido ter cuidado com fidelidade. O contrato de 3 anos existe porque "
        "o sistema e seu: equipamentos instalados sem custo de obra. A multa so "
        "existe se cancelar antes, e proporcional aos meses restantes. Na visita eu "
        "te explico com calma, sem compromisso."
    ),
    "skepticism": (
        "Faz sentido ter duvidas. O {recomendante} nao recomendaria se nao "
        "acreditasse que seria realmente interessante, concorda? Ele falou muito "
        "bem de voce e acredito que essa apresentacao rapida possa ser bastante util."
    ),
    "need_lack": (
        "Entendo, o seu bairro parece tranquilo. A verdade e que a seguranca "
        "eletronica funciona como prevencao, nao so como reacao. A placa da Emive "
        "sozinha ja inibe 36 vezes mais tentativas. Vale uma conversa rapida?"
    ),
    "timing": (
        "Sem problemas, entendo a correria. Sao so 15 a 20 minutos, sem compromisso. "
        "Na semana que vem fica melhor? Manha ou tarde?"
    ),
    "complexity": (
        "A instalacao e sem obras, sem furadeiras e fios. Tudo sem fio criptografado. "
        "Em ate 24h esta tudo funcionando. Posso te mostrar na visita?"
    ),
    "area_externa": (
        "Entendo que voce quer cameras externas. O sistema Emive e focado em area interna "
        "com monitoramento 24h, audio bidirecional e sensores. Para o externo, a placa "
        "visivel ja inibe 36x mais tentativas. Na visita eu te mostro como o interno "
        "resolve a maior parte do problema, sem compromisso."
    ),
    "concorrencia_local": (
        "Faz sentido, sei que tem instaladores locais atuando. A diferenca do Emive e "
        "o monitoramento humano 24h com central propria, nao so instalacao. O "
        "{recomendante} trocou por isso. Vale uma visita de 15 minutos para ver a "
        "diferenca?"
    ),
}

# === CENARIOS DE TREINAMENTO (do BLUEPRINT) ===
CENARIOS_TREINAMENTO: dict[str, dict] = {
    "CEN-01": {
        "nome": "Prospeccao Mercado A",
        "objetivo": "Agendar visita inicial com amigo proximo para pedir feedback",
        "objecao_cliente": "Acha que e uma tentativa de empurrar produtos e diz que esta sem tempo",
    },
    "CEN-02": {
        "nome": "Lead Frio (Mercado C Nao Avisado)",
        "objetivo": "Agendar visita utilizando o nome de um amigo em comum como gancho",
        "objecao_cliente": "Desconfianca inicial, pergunta de onde conseguiu o numero, diz que o bairro e seguro",
    },
    "CEN-03": {
        "nome": "Dono de Comercio (Indoor)",
        "objetivo": "Agendar visita para projeto comercial de seguranca indoor",
        "objecao_cliente": "Alega que ja tem cameras de monitoramento proprio e que a equipe interna cuida de tudo",
    },
    "CEN-04": {
        "nome": "Objecao de Preco (Mensalidade)",
        "objetivo": "Superar a barreira da taxa de monitoramento mensal explicando o valor da Central 24h",
        "objecao_cliente": "Nao quero um boleto fixo todo mes. Se o alarme tocar, eu mesmo chamo a policia",
    },
    "CEN-05": {
        "nome": "Objecao Tecnica (Pet/Fios)",
        "objetivo": "Explicar a tecnologia de sensores de vibracao/presenca e instalacao sem fios",
        "objecao_cliente": "Medo de disparos falsos causados por animais de estimacao ou quebra-quebra na instalacao",
    },
}


def gerar_pitch(p: PersonaV5, canal: str = "phone_call",
                mercado: str = "mercado_c_nao_avisado",
                recomendante: str = "um amigo em comum",
                vendedor: str = "Reginato") -> str:
    """Gera pitch template para uma persona (sem LLM).

    Args:
        p: PersonaV5 com dados do cliente
        canal: phone_call ou whatsapp
        mercado: mercado_a, mercado_c_avisado, mercado_c_nao_avisado
        recomendante: nome de quem recomendou
        vendedor: nome do vendedor

    Returns:
        Narrativa de pitch em texto.
    """
    dor = DOR_POR_NICHO.get(p.segment, "protecao do seu patrimonio")
    nome = p.owner_name.split()[0]

    # Use generic label when segment is not a known nicho
    segment_label = p.segment.replace('_', ' ') if p.segment in DOR_POR_NICHO else "seu negocio"

    # Script de abordagem (format_map with SafeDict prevents KeyError on unknown placeholders)
    script = SCRIPTS_ABORDAGEM.get(mercado, SCRIPTS_ABORDAGEM["mercado_c_nao_avisado"])
    abordagem = script.format_map(
        _SafeFormatDict(
            nome=nome,
            vendedor=vendedor,
            recomendante=recomendante,
            imovel=f"{segment_label} no {p.bairro}",
            perfil_conexao=f"tem uma {segment_label} no {p.bairro}",
        )
    )

    # Beneficios relevantes baseados no perfil
    beneficios = []
    if p.has_existing_security == "diy_cameras":
        beneficios.append(BENEFICIOS_EMIVE["audio_bidirecional"])
        beneficios.append(BENEFICIOS_EMIVE["inibicao_36x"])
    elif p.has_existing_security == "none":
        beneficios.append(BENEFICIOS_EMIVE["inibicao_36x"])
        beneficios.append(BENEFICIOS_EMIVE["sem_obras"])
    elif p.has_existing_security == "full_system":
        beneficios.append(BENEFICIOS_EMIVE["redundancia_4_canais"])
        beneficios.append(BENEFICIOS_EMIVE["autonomia_10h"])
    else:
        beneficios.append(BENEFICIOS_EMIVE["anti_falso_alarme"])
        beneficios.append(BENEFICIOS_EMIVE["app_com_extras"])

    # Dor especifica do nicho
    dor_msg = f"Para sua {segment_label} no {p.bairro}, o foco e {dor.lower()}."

    # Fechamento (sempre agendamento, nunca preco por telefone)
    if canal == "whatsapp":
        fechamento = (
            f"Posso te mandar mais detalhes por aqui e agendar uma visita rapida de "
            f"15 a 20 minutos, sem compromisso? Fica melhor terca ou quarta?"
        )
    else:
        fechamento = (
            f"Como esta sua agenda para batermos um papo de 15 a 20 minutos? "
            f"Fica melhor pela manha ou tarde? Terca ou quarta?"
        )

    # Monta narrativa
    pitch = f"{abordagem}\n\n{dor_msg}\n\n"
    if beneficios:
        pitch += "O que torna o sistema Emive diferente:\n"
        for b in beneficios[:2]:  # Max 2 beneficios para nao poluir
            pitch += f"- {b}\n"
    pitch += f"\n{fechamento}"

    return pitch


def gerar_objecao_resposta(objecao: str, recomendante: str = "recomendante") -> str:
    """Gera resposta para uma objecao baseada no blueprint.

    Args:
        objecao: existing_solution, budget, skepticism, need_lack, timing, complexity
        recomendante: nome de quem recomendou

    Returns:
        Resposta a objecao.
    """
    resposta = OBJECAO_RESPOSTA.get(objecao, OBJECAO_RESPOSTA["skepticism"])
    return resposta.replace("{recomendante}", recomendante)


def avaliar_competencias(pitch: str, decisao: str, objecoes: list[str] | None) -> dict[str, int]:
    """Avalia 5 competencias do blueprint (0-10) baseado no pitch gerado.

    Como e programatico (sem LLM), a avaliacao e heuristica:
    - Conexao e Rapport: cita nome do cliente e recomendante?
    - Foco no Agendamento: cita "15 a 20 minutos" e pergunta dia/horario?
    - Geracao de Curiosidade: cita "Conceito Smart" ou "tecnologia de 1 mundo"?
    - Contorno de Objecoes: tem resposta para cada objecao?
    - Fechamento e Compromisso: cita "agenda fechada" ou "sem compromisso"?
    """
    scores = {}

    # Conexao e Rapport
    scores["conexao_rapport"] = 8 if "amigo" in pitch.lower() or "recomend" in pitch.lower() else 5

    # Foco no Agendamento
    if "15 a 20 minutos" in pitch and ("terca" in pitch.lower() or "quarta" in pitch.lower()):
        scores["foco_agendamento"] = 9
    elif "15 a 20 minutos" in pitch:
        scores["foco_agendamento"] = 7
    else:
        scores["foco_agendamento"] = 4

    # Geracao de Curiosidade
    if "conceito smart" in pitch.lower() or "1 mundo" in pitch.lower():
        scores["geracao_curiosidade"] = 8
    else:
        scores["geracao_curiosidade"] = 5

    # Contorno de Objecoes
    if objecoes:
        # Para cada objecao, verifica se existe resposta
        respostas_encontradas = 0
        for obj in objecoes:
            if obj in OBJECAO_RESPOSTA:
                respostas_encontradas += 1
        scores["contorno_objecoes"] = min(10, 5 + respostas_encontradas)
    else:
        scores["contorno_objecoes"] = 7  # Sem objecoes = nao precisou contornar

    # Fechamento e Compromisso
    if "sem compromisso" in pitch.lower():
        scores["fechamento_compromisso"] = 8
    else:
        scores["fechamento_compromisso"] = 5

    return scores
