"""Layout paroquial da escala mensal (PDF)."""

from collections import defaultdict
from datetime import date

from reportlab.platypus import Paragraph

from apps.membership.models import Coroinha
from apps.scheduling.models import Escala, EscalaItem, EscalaMensal, TipoSlotMissa

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

SECOES_PDF = [
    (TipoSlotMissa.SEXTA_ADORACAO, "SEXTA-FEIRA · 18h", "Adoração ao Santíssimo e Missa"),
    (TipoSlotMissa.SABADO_NOITE, "SÁBADO · 18h30", "Missas com grupos rotativos"),
    (TipoSlotMissa.DOMINGO_MANHA, "DOMINGO · 08h", "Missas com grupos rotativos"),
    (TipoSlotMissa.DOMINGO_NOITE, "DOMINGO · 18h30", "Missas com grupos rotativos"),
    (TipoSlotMissa.QUARTA_VOLUNTARIOS, "QUARTA-FEIRA · 19h", "Voluntários — sem nomes fixos"),
    (TipoSlotMissa.COMUNIDADE_DOMINGO, "COMUNIDADE · DOMINGO 10h30", "Comunidade Santo Antônio"),
    (TipoSlotMissa.DIA_13, "DIA 13", "Memória de Nossa Senhora de Fátima"),
    (TipoSlotMissa.OUTRO, "OUTRAS CELEBRAÇÕES", ""),
]


def formatar_data_legivel(data: date) -> str:
    """Ex.: Sábado, 5 de agosto"""
    dia_semana = DIAS_SEMANA_PT[data.weekday()]
    mes = MESES_PT[data.month].lower()
    return f"{dia_semana}, {data.day} de {mes}"


def agrupar_escalas_por_slot(escalas: list[Escala]) -> dict[str, list[Escala]]:
    por_slot: dict[str, list[Escala]] = defaultdict(list)
    for escala in escalas:
        slot = escala.missa.tipo_slot or TipoSlotMissa.OUTRO
        por_slot[slot].append(escala)
    for lista in por_slot.values():
        lista.sort(key=lambda e: (e.data, e.missa.horario))
    return por_slot


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
    data_txt = formatar_data_legivel(escala.data)
    if escala.grupo_numero is not None:
        return f"{data_txt}  ·  GRUPO {escala.grupo_numero}"
    if escala.missa.tipo_slot == TipoSlotMissa.DIA_13:
        hora = escala.missa.horario.strftime("%H:%M")
        return f"{data_txt}  ·  {hora}"
    return data_txt


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
