"""Layout paroquial da escala mensal (PDF)."""

import io
from collections import defaultdict

from reportlab.lib.units import mm
from reportlab.platypus import Image as RLImage, Paragraph, Table

from apps.membership.models import Coroinha
from apps.scheduling.models import Escala, EscalaItem, EscalaMensal, TipoSlotMissa

FOTO_MM = 7
FOTO_PT = FOTO_MM * mm

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

SECOES_PDF = [
    (TipoSlotMissa.SEXTA_ADORACAO, "SEXTA 18h", "Adoração ao Santíssimo seguida de Missa"),
    (TipoSlotMissa.SABADO_NOITE, "SÁBADO 18h30", "Grupos rotativos"),
    (TipoSlotMissa.DOMINGO_MANHA, "DOMINGO 08h", "Grupos rotativos"),
    (TipoSlotMissa.DOMINGO_NOITE, "DOMINGO 18h30", "Grupos rotativos"),
    (TipoSlotMissa.QUARTA_VOLUNTARIOS, "QUARTA 19h", "Voluntários"),
    (TipoSlotMissa.COMUNIDADE_DOMINGO, "COMUNIDADE — DOMINGO 10h30", "Comunidade Santo Antônio"),
    (TipoSlotMissa.DIA_13, "DIA 13", "Memória mensal de Nossa Senhora de Fátima"),
    (TipoSlotMissa.OUTRO, "OUTRAS CELEBRAÇÕES", ""),
]


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
    data_txt = escala.data.strftime("%d/%m")
    if escala.grupo_numero is not None:
        return f"{data_txt} — GRUPO {escala.grupo_numero}"
    if escala.missa.tipo_slot == TipoSlotMissa.DIA_13:
        return f"{data_txt} — {escala.missa.horario.strftime('%H:%M')}"
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


def foto_flowable(coroinha: Coroinha) -> RLImage | None:
    """Miniatura apenas se a foto já estiver cadastrada."""
    if not coroinha.foto or not coroinha.foto.name:
        return None
    try:
        with coroinha.foto.open("rb") as arquivo:
            buf = io.BytesIO(arquivo.read())
        return RLImage(buf, width=FOTO_PT, height=FOTO_PT, kind="proportional")
    except Exception:
        return None


def linha_coroinha_flowable(coroinha: Coroinha | None, texto: str, estilo) -> list:
    """Linha com foto opcional à esquerda do nome."""
    paragrafo = Paragraph(texto, estilo)
    if coroinha is None:
        return [paragrafo]
    foto = foto_flowable(coroinha)
    if not foto:
        return [paragrafo]
    tabela = Table([[foto, paragrafo]], colWidths=[FOTO_PT + 1 * mm, None])
    tabela.setStyle(
        [
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]
    )
    return [tabela]


def itens_coroinha_escala(escala: Escala) -> list[tuple[str, Coroinha | None]]:
    if escala.voluntarios:
        return [("Voluntários", None)]
    itens: list[EscalaItem] = list(escala.itens.all())
    if not itens:
        return [("—", None)]
    if escala.grupo_numero is not None:
        return [(f"{i + 1}. {item.coroinha.nome}", item.coroinha) for i, item in enumerate(itens)]
    return [(item.coroinha.nome, item.coroinha) for item in itens]
