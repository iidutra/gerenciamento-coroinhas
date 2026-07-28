"""Layout paroquial da escala mensal (PDF)."""

from collections import defaultdict
from datetime import date, time, timedelta

from reportlab.platypus import Paragraph

from apps.membership.models import Coroinha
from apps.scheduling.models import Escala, EscalaItem, EscalaMensal, LocalCelebracao, TipoSlotMissa

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


def slot_da_escala(escala: Escala) -> str:
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
