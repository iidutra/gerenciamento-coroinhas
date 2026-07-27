import csv
import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.scheduling.models import FuncaoEscala, TipoSlotMissa
from apps.scheduling.services.relatorio_escala_pdf_layout import (
    MESES_PT,
    SECOES_PDF,
    agrupar_escalas_por_slot,
    carregar_dados_mes,
    linhas_nomes_escala,
    texto_cabecalho_entrada,
)

BURGUNDY = colors.HexColor("#5C1C24")
CREME = colors.HexColor("#FAF8F5")


class RelatorioEscalaService:
    @staticmethod
    def _escalas_mes(ano: int, mes: int):
        escalas, _ = carregar_dados_mes(ano, mes)
        return escalas

    @staticmethod
    def exportar_mes_pdf(ano: int, mes: int) -> bytes:
        escalas, escala_mensal = carregar_dados_mes(ano, mes)
        por_slot = agrupar_escalas_por_slot(escalas)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=14 * mm,
            rightMargin=14 * mm,
            topMargin=12 * mm,
            bottomMargin=12 * mm,
            title=f"Escala Coroinhas {MESES_PT[mes]}/{ano}",
        )

        styles = getSampleStyleSheet()
        titulo = ParagraphStyle(
            "TituloParoquial",
            parent=styles["Heading1"],
            fontSize=15,
            leading=18,
            alignment=TA_CENTER,
            textColor=BURGUNDY,
            spaceAfter=4,
            fontName="Helvetica-Bold",
        )
        subtitulo = ParagraphStyle(
            "SubParoquial",
            parent=styles["Normal"],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#444444"),
            spaceAfter=10,
        )
        secao = ParagraphStyle(
            "SecaoHorario",
            parent=styles["Heading2"],
            fontSize=11,
            textColor=BURGUNDY,
            spaceBefore=10,
            spaceAfter=2,
            fontName="Helvetica-Bold",
        )
        secao_sub = ParagraphStyle(
            "SecaoSub",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#666666"),
            spaceAfter=6,
        )
        entrada_titulo = ParagraphStyle(
            "EntradaTitulo",
            parent=styles["Normal"],
            fontSize=9,
            fontName="Helvetica-Bold",
            textColor=BURGUNDY,
            spaceBefore=4,
            spaceAfter=1,
        )
        lista = ParagraphStyle(
            "ListaNomes",
            parent=styles["Normal"],
            fontSize=9,
            leading=11,
            leftIndent=8,
            spaceAfter=2,
        )
        normal = ParagraphStyle(
            "NormalCompacto",
            parent=styles["Normal"],
            fontSize=9,
            leading=11,
        )

        mes_nome = MESES_PT[mes].upper()
        elementos = [
            Paragraph("ESCALA DOS COROINHAS", titulo),
            Paragraph(f"MÊS DE {mes_nome} {ano}", titulo),
            Paragraph("Santuário de Fátima — Pastoral dos Coroinhas", subtitulo),
        ]

        if escala_mensal and escala_mensal.grupos.exists():
            elementos.append(Paragraph("GRUPOS DO MÊS", secao))
            elementos.append(Spacer(1, 2))
            grupos = list(escala_mensal.grupos.all().order_by("numero"))
            colunas = []
            for grupo in grupos:
                linhas = [Paragraph(f"<b>GRUPO {grupo.numero}</b>", normal)]
                for membro in grupo.membros.all().order_by("ordem"):
                    linhas.append(Paragraph(f"{membro.ordem}. {membro.coroinha.nome}", lista))
                colunas.append(linhas)
            while len(colunas) < 4:
                colunas.append([Paragraph("", normal)])

            tabela_grupos = Table(
                [[colunas[0], colunas[1]], [colunas[2], colunas[3]]],
                colWidths=[90 * mm, 90 * mm],
            )
            tabela_grupos.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("BOX", (0, 0), (-1, -1), 0.5, BURGUNDY),
                        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#DDDDDD")),
                        ("BACKGROUND", (0, 0), (-1, -1), CREME),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            elementos.append(tabela_grupos)
            elementos.append(Spacer(1, 8))

        if not escalas:
            elementos.append(Paragraph("Nenhuma escala montada neste período.", normal))
        else:
            elementos.append(Paragraph("SANTUÁRIO DE FÁTIMA", secao))
            elementos.append(Spacer(1, 4))

            for slot, titulo_secao, subtitulo_secao in SECOES_PDF:
                if slot == TipoSlotMissa.COMUNIDADE_DOMINGO:
                    continue
                lista_escalas = por_slot.get(slot, [])
                if not lista_escalas:
                    continue

                elementos.append(Paragraph(titulo_secao, secao))
                if subtitulo_secao:
                    elementos.append(Paragraph(subtitulo_secao, secao_sub))

                for escala in lista_escalas:
                    elementos.append(Paragraph(texto_cabecalho_entrada(escala), entrada_titulo))
                    for linha in linhas_nomes_escala(escala):
                        elementos.append(Paragraph(linha, lista))

            comunidade = por_slot.get(TipoSlotMissa.COMUNIDADE_DOMINGO, [])
            if comunidade:
                elementos.append(Spacer(1, 6))
                elementos.append(Paragraph("COMUNIDADE SANTO ANTÔNIO", secao))
                elementos.append(Paragraph("Domingo 10h30", secao_sub))
                for escala in comunidade:
                    elementos.append(Paragraph(texto_cabecalho_entrada(escala), entrada_titulo))
                    for linha in linhas_nomes_escala(escala):
                        elementos.append(Paragraph(linha, lista))

            outros = por_slot.get(TipoSlotMissa.OUTRO, [])
            if outros:
                elementos.append(Paragraph("OUTRAS CELEBRAÇÕES", secao))
                for escala in outros:
                    cab = f"{escala.data.strftime('%d/%m')} — {escala.missa.nome}"
                    elementos.append(Paragraph(cab, entrada_titulo))
                    for linha in linhas_nomes_escala(escala):
                        elementos.append(Paragraph(linha, lista))

        doc.build(elementos)
        return buffer.getvalue()

    @staticmethod
    def exportar_mes_csv(ano: int, mes: int) -> str:
        escalas = RelatorioEscalaService._escalas_mes(ano, mes)

        headers = ["Data", "Missa", "Horário", "Grupo", "Coroinhas"]
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=";")
        writer.writerow(headers)

        for escala in escalas:
            nomes = ", ".join(item.coroinha.nome for item in escala.itens.all())
            if escala.voluntarios:
                nomes = "Voluntários"
            writer.writerow(
                [
                    escala.data.strftime("%d/%m/%Y"),
                    escala.missa.nome,
                    escala.missa.horario.strftime("%H:%M"),
                    escala.grupo_numero or "",
                    nomes,
                ]
            )

        return "\ufeff" + buffer.getvalue()

    @staticmethod
    def exportar_mes_json(ano: int, mes: int) -> dict:
        escalas, escala_mensal = carregar_dados_mes(ano, mes)

        grupos = []
        if escala_mensal:
            for grupo in escala_mensal.grupos.all().order_by("numero"):
                grupos.append(
                    {
                        "numero": grupo.numero,
                        "membros": [
                            {"ordem": m.ordem, "nome": m.coroinha.nome}
                            for m in grupo.membros.all().order_by("ordem")
                        ],
                    }
                )

        linhas = []
        for escala in escalas:
            itens = list(escala.itens.all())
            funcoes_label = {
                FuncaoEscala(item.funcao).label: item.coroinha.nome
                for item in itens
                if item.funcao
            }
            linhas.append(
                {
                    "data": escala.data.isoformat(),
                    "missa": escala.missa.nome,
                    "horario": escala.missa.horario.strftime("%H:%M"),
                    "tipo_slot": escala.missa.tipo_slot,
                    "grupo_numero": escala.grupo_numero,
                    "voluntarios": escala.voluntarios,
                    "funcoes": funcoes_label,
                    "coroinhas": [item.coroinha.nome for item in itens],
                }
            )

        return {"ano": ano, "mes": mes, "grupos": grupos, "escalas": linhas}
