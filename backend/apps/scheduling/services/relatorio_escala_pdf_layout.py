"""Layout paroquial da escala mensal (PDF)."""

import re
from collections import defaultdict
from datetime import date, time, timedelta

from reportlab.platypus import Paragraph

from apps.membership.models import Coroinha
from apps.scheduling.models import (
    Escala,
    EscalaItem,
    EscalaMensal,
    LocalCelebracao,
    Missa,
    TipoSlotMissa,
)

MESES_PT = [
    "",
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]

DIAS_SEMANA_PT = [
    "Segunda-feira",
    "Terça-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "Sábado",
    "Domingo",
]

SLOTS_FIM_DE_SEMANA = {
    TipoSlotMissa.SEXTA_ADORACAO,
    TipoSlotMissa.SABADO_NOITE,
    TipoSlotMissa.DOMINGO_MANHA,
    TipoSlotMissa.DOMINGO_NOITE,
    TipoSlotMissa.COMUNIDADE_DOMINGO,
}

ORDEM_SLOT_FDS = {
    TipoSlotMissa.SEXTA_ADORACAO: 1,
    TipoSlotMissa.SABADO_NOITE: 2,
    TipoSlotMissa.DOMINGO_MANHA: 3,
    TipoSlotMissa.COMUNIDADE_DOMINGO: 4,
    TipoSlotMissa.DOMINGO_NOITE: 5,
}

SECOES_EXTRAS_PDF = [
    (TipoSlotMissa.QUARTA_VOLUNTARIOS, "QUARTA-FEIRA · 19h", "Voluntários — sem nomes fixos"),
    (TipoSlotMissa.DIA_13, "DIA 13", "Memória de Nossa Senhora de Fátima"),
    (TipoSlotMissa.OUTRO, "OUTRAS CELEBRAÇÕES", ""),
]

TITULO_SOLENIDADE_DIA_13 = "Solenidade de Nossa Senhora de Fátima"


LOCAIS_CELEBRACAO = {
    LocalCelebracao.SANTUARIO: "N. Sra. de Fátima",
    LocalCelebracao.COMUNIDADE: "Santo Antônio",
}


def local_celebracao(escala: Escala) -> str:
    if escala.missa.tipo_slot == TipoSlotMissa.COMUNIDADE_DOMINGO:
        return "Santo Antônio"
    return LOCAIS_CELEBRACAO.get(escala.missa.local, "N. Sra. de Fátima")


def horario_celebracao(escala: Escala) -> str:
    return formatar_horario_curto(escala.missa.horario)


def formatar_data_legivel(data: date) -> str:
    """Ex.: Sábado, 5 de agosto"""
    dia_semana = DIAS_SEMANA_PT[data.weekday()]
    mes = MESES_PT[data.month].lower()
    return f"{dia_semana}, {data.day} de {mes}"


def formatar_horario_curto(horario: time) -> str:
    if horario.minute == 0:
        return f"{horario.hour}h"
    return f"{horario.hour}h{horario.minute:02d}"


def agrupar_escalas_por_slot(escalas: list[Escala]) -> dict[str, list[Escala]]:
    por_slot: dict[str, list[Escala]] = defaultdict(list)
    for escala in escalas:
        slot = escala.missa.tipo_slot or TipoSlotMissa.OUTRO
        por_slot[slot].append(escala)
    for lista in por_slot.values():
        lista.sort(key=lambda e: (e.data, e.missa.horario))
    return por_slot


def eh_missa_dia13(missa: Missa) -> bool:
    if missa.tipo_slot == TipoSlotMissa.DIA_13:
        return True
    if missa.dia_mes == 13:
        return True
    return bool(re.search(r"dia\s*13", missa.nome or "", re.I))


def slot_da_escala(escala: Escala) -> str:
    if eh_missa_dia13(escala.missa):
        return TipoSlotMissa.DIA_13
    return escala.missa.tipo_slot or TipoSlotMissa.OUTRO


def chave_fim_de_semana(data: date) -> date:
    """Sábado de referência do bloco sexta–sábado–domingo."""
    wd = data.weekday()
    if wd == 4:
        return data + timedelta(days=1)
    if wd == 6:
        return data - timedelta(days=1)
    return data


def rotulo_semana(chave_sabado: date) -> str:
    sex = chave_sabado - timedelta(days=1)
    dom = chave_sabado + timedelta(days=1)
    if sex.month == dom.month:
        mes = MESES_PT[dom.month].lower()
        return f"{sex.day} a {dom.day} de {mes}"
    mes_sex = MESES_PT[sex.month].lower()
    mes_dom = MESES_PT[dom.month].lower()
    return f"{sex.day} de {mes_sex} a {dom.day} de {mes_dom}"


def agrupar_escalas_por_semana(
    escalas: list[Escala],
) -> tuple[list[tuple[int, date, list[Escala]]], list[tuple[str, str, list[Escala]]]]:
    por_semana: dict[date, list[Escala]] = defaultdict(list)
    extras_por_slot: dict[str, list[Escala]] = defaultdict(list)

    for escala in escalas:
        slot = slot_da_escala(escala)
        if slot in SLOTS_FIM_DE_SEMANA:
            por_semana[chave_fim_de_semana(escala.data)].append(escala)
        else:
            extras_por_slot[slot].append(escala)

    semanas: list[tuple[int, date, list[Escala]]] = []
    for idx, (chave, lista) in enumerate(sorted(por_semana.items())):
        lista.sort(
            key=lambda e: (
                ORDEM_SLOT_FDS.get(slot_da_escala(e), 99),
                e.data,
                e.missa.horario,
            )
        )
        semanas.append((idx + 1, chave, lista))

    extras: list[tuple[str, str, list[Escala]]] = []
    for slot, titulo, subtitulo in SECOES_EXTRAS_PDF:
        lista = extras_por_slot.get(slot, [])
        if lista:
            lista.sort(key=lambda e: (e.data, e.missa.horario))
            extras.append((titulo, subtitulo, lista))

    return semanas, extras


ORDEM_SLOT_CRONO = {
    TipoSlotMissa.SEXTA_ADORACAO: 1,
    TipoSlotMissa.SABADO_NOITE: 2,
    TipoSlotMissa.DOMINGO_MANHA: 3,
    TipoSlotMissa.COMUNIDADE_DOMINGO: 4,
    TipoSlotMissa.DOMINGO_NOITE: 5,
    TipoSlotMissa.QUARTA_VOLUNTARIOS: 6,
    TipoSlotMissa.DIA_13: 7,
    TipoSlotMissa.OUTRO: 8,
}

LEGENDA_CATEGORIAS_V6 = ["Grupo 1", "Grupo 2", "Grupo 3", "Grupo 4", "S. Antônio", "Solenidade", "Novena"]

ORIENTACOES_GERAIS_V6 = [
    "Chegada com 30 minutos de antecedência em todas as celebrações.",
    "Meninas: cabelos presos e trajes adequados ao ambiente da sacristia.",
    "Meninos: trajes adequados ao ambiente da sacristia.",
    "Sapatos preferencialmente pretos e vestes limpas e passadas.",
    "Em caso de impedimento, avisar com antecedência para reorganização.",
    "Dúvidas e trocas: falar com Igor ou Giaritssa.",
]


def chave_ordem_escala(escala: Escala) -> tuple:
    slot = slot_da_escala(escala)
    return (
        escala.data,
        escala.missa.horario,
        ORDEM_SLOT_CRONO.get(slot, 99),
    )


def agrupar_escalas_por_dia(escalas: list[Escala]) -> list[tuple[date, list[Escala]]]:
    """Cronograma v6: todas as celebrações por data (comunidade inline no domingo)."""
    por_dia: dict[date, list[Escala]] = defaultdict(list)
    for escala in escalas:
        por_dia[escala.data].append(escala)
    return [
        (dia, sorted(lista, key=chave_ordem_escala))
        for dia, lista in sorted(por_dia.items())
    ]


def rotulo_dia_semana_curto(data: date) -> str:
    return DIAS_SEMANA_PT[data.weekday()].upper().replace("-FEIRA", "")


def tag_celebracao(escala: Escala) -> str:
    slot = slot_da_escala(escala)
    if slot == TipoSlotMissa.COMUNIDADE_DOMINGO:
        return "Santo Antônio"
    if slot == TipoSlotMissa.QUARTA_VOLUNTARIOS:
        return "Novena"
    if slot == TipoSlotMissa.DIA_13:
        return "Solenidade"
    if escala.grupo_numero is not None:
        return f"Grupo {escala.grupo_numero}"
    return ""


def titulo_celebracao_v6(escala: Escala) -> str:
    slot = slot_da_escala(escala)
    horario = horario_celebracao(escala)
    if slot == TipoSlotMissa.SABADO_NOITE:
        return f"{horario} Missa"
    if slot == TipoSlotMissa.DOMINGO_MANHA:
        return f"{horario} Missa da Manhã"
    if slot == TipoSlotMissa.DOMINGO_NOITE:
        return f"{horario} Missa da Noite"
    if slot == TipoSlotMissa.COMUNIDADE_DOMINGO:
        return f"{horario} Comunidade"
    if slot == TipoSlotMissa.SEXTA_ADORACAO:
        return f"{horario} Adoração + Missa"
    if slot == TipoSlotMissa.QUARTA_VOLUNTARIOS:
        return "Noite Novena"
    if slot == TipoSlotMissa.DIA_13:
        hora = escala.missa.horario.hour
        if hora == 6:
            return "Missa das 6h"
        if hora == 9:
            return "Missa das 9h"
        if hora == 12:
            return "Missa das 12h"
        return "Missa das 18h"
    return f"{horario} {escala.missa.nome}"


def linha_titulo_v6(escala: Escala) -> str:
    titulo = titulo_celebracao_v6(escala)
    slot = slot_da_escala(escala)
    tag = tag_celebracao(escala)
    if slot == TipoSlotMissa.QUARTA_VOLUNTARIOS:
        return f"{titulo} {tag}" if tag else titulo
    if slot == TipoSlotMissa.DIA_13:
        return titulo
    if escala.grupo_numero is not None:
        return f"{titulo} Grupo {escala.grupo_numero}"
    if tag:
        return f"{titulo} {tag}"
    return titulo


def dia_tem_solenidade(escalas_dia: list[Escala]) -> bool:
    return any(slot_da_escala(e) == TipoSlotMissa.DIA_13 for e in escalas_dia)


def linhas_coroinhas_v6(escala: Escala) -> list[str]:
    if escala.voluntarios:
        return ["01 Participação aberta — Voluntários"]
    itens = list(escala.itens.all())
    if not itens:
        return ["—"]
    return [f"{idx + 1:02d} {item.coroinha.nome}" for idx, item in enumerate(itens)]


def separar_escalas_cronologico_pdf(escalas: list[Escala]) -> tuple[list[Escala], list[Escala]]:
    """Compatibilidade: retorna cronológico com comunidade inline no fluxo principal."""
    ordenadas = sorted(escalas, key=chave_ordem_escala)
    return ordenadas, []


def linhas_nomes_escala(escala: Escala) -> list[str]:
    if escala.voluntarios:
        return ["Voluntários"]
    itens = list(escala.itens.all())
    if not itens:
        return ["—"]
    if escala.grupo_numero is not None:
        return [f"{i + 1}. {item.coroinha.nome}" for i, item in enumerate(itens)]
    nomes = [item.coroinha.nome for item in itens]
    return [" · ".join(nomes)]


def texto_cabecalho_entrada(escala: Escala) -> str:
    """Ex.: Domingo, 3 de agosto · Santo Antônio · 10h30"""
    partes = [formatar_data_legivel(escala.data), local_celebracao(escala), horario_celebracao(escala)]
    if escala.grupo_numero is not None:
        partes.append(f"GRUPO {escala.grupo_numero}")
    return "  ·  ".join(partes)


def carregar_dados_mes(ano: int, mes: int) -> tuple[list[Escala], EscalaMensal | None]:
    escalas = list(
        Escala.objects.filter(data__year=ano, data__month=mes)
        .select_related("missa")
        .prefetch_related("itens__coroinha")
        .order_by("data", "missa__horario")
    )
    escala_mensal = (
        EscalaMensal.objects.filter(ano=ano, mes=mes)
        .prefetch_related("grupos__membros__coroinha")
        .first()
    )
    return escalas, escala_mensal


def linha_coroinha_flowable(coroinha: Coroinha | None, texto: str, estilo) -> list:
    return [Paragraph(texto, estilo)]


def itens_coroinha_escala(escala: Escala) -> list[tuple[str, Coroinha | None]]:
    if escala.voluntarios:
        return [("Voluntários", None)]
    itens: list[EscalaItem] = list(escala.itens.all())
    if not itens:
        return [("—", None)]
    if escala.grupo_numero is not None:
        return [(f"{i + 1}. {item.coroinha.nome}", item.coroinha) for i, item in enumerate(itens)]
    return [(item.coroinha.nome, item.coroinha) for item in itens]
