import csv
import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.scheduling.models import FuncaoEscala, TipoSlotMissa
from apps.scheduling.services.relatorio_escala_pdf_layout import (
    MESES_PT,
    SECOES_PDF,
    agrupar_escalas_por_slot,
    carregar_dados_mes,
    itens_coroinha_escala,
    linha_coroinha_flowable,
    texto_cabecalho_entrada,
)

BURGUNDY = colors.HexColor("#5C1C24")
CREME = colors.HexColor("#FAF8F5")
CREME_ESCURO = colors.HexColor("#F0EBE3")
CINZA_TEXTO = colors.HexColor("#333333")


class RelatorioEscalaService:
    @staticmethod
    def _escalas_mes(ano: int, mes: int):
        escalas, _ = carregar_dados_mes(ano, mes)
        return escalas

    @staticmethod
    def _estilos_pdf():
        base = getSampleStyleSheet()
        return {
            "titulo": ParagraphStyle(
                "TituloParoquial",
                parent=base["Heading1"],
                fontSize=20,
                leading=24,
                alignment=TA_CENTER,
                textColor=BURGUNDY,
                spaceAfter=6,
                fontName="Helvetica-Bold",
            ),
            "mes": ParagraphStyle(
                "MesParoquial",
                parent=base["Heading1"],
                fontSize=16,
                leading=20,
                alignment=TA_CENTER,
                textColor=BURGUNDY,
                spaceAfter=4,
                fontName="Helvetica-Bold",
            ),
            "subtitulo": ParagraphStyle(
                "SubParoquial",
                parent=base["Normal"],
                fontSize=11,
                alignment=TA_CENTER,
                textColor=CINZA_TEXTO,
                spaceAfter=14,
            ),
            "instrucao_titulo": ParagraphStyle(
                "InstrucaoTitulo",
                parent=base["Normal"],
                fontSize=11,
                fontName="Helvetica-Bold",
                textColor=BURGUNDY,
                spaceAfter=4,
            ),
            "instrucao": ParagraphStyle(
                "Instrucao",
                parent=base["Normal"],
                fontSize=10,
                leading=14,
                textColor=CINZA_TEXTO,
                leftIndent=4,
                spaceAfter=2,
            ),
            "secao": ParagraphStyle(
                "SecaoHorario",
                parent=base["Heading2"],
                fontSize=14,
                leading=17,
                textColor=colors.white,
                alignment=TA_LEFT,
                fontName="Helvetica-Bold",
                spaceBefore=0,
                spaceAfter=0,
            ),
            "secao_sub": ParagraphStyle(
                "SecaoSub",
                parent=base["Normal"],
                fontSize=10,
                textColor=CINZA_TEXTO,
                spaceAfter=8,
                leftIndent=2,
            ),
            "grupo_titulo": ParagraphStyle(
                "GrupoTitulo",
                parent=base["Normal"],
                fontSize=12,
                fontName="Helvetica-Bold",
                textColor=BURGUNDY,
                spaceAfter=4,
            ),
            "nome": ParagraphStyle(
                "NomeCoroinha",
                parent=base["Normal"],
                fontSize=11,
                leading=15,
                textColor=CINZA_TEXTO,
                leftIndent=6,
                spaceAfter=3,
            ),
            "data_cab": ParagraphStyle(
                "DataCab",
                parent=base["Normal"],
                fontSize=12,
                leading=15,
                fontName="Helvetica-Bold",
                textColor=BURGUNDY,
                spaceAfter=4,
            ),
            "normal": ParagraphStyle(
                "NormalLegivel",
                parent=base["Normal"],
                fontSize=11,
                leading=14,
                textColor=CINZA_TEXTO,
            ),
        }

    @staticmethod
    def _caixa_instrucoes(estilos) -> Table:
        linhas = [
            [Paragraph("Como ler esta escala", estilos["instrucao_titulo"])],
            [Paragraph("1. Veja abaixo em qual <b>GRUPO</b> você está (fins de semana).", estilos["instrucao"])],
            [Paragraph("2. Procure o <b>dia da semana</b> e o <b>horário</b> da sua missa.", estilos["instrucao"])],
            [Paragraph("3. Cada quadro mostra a data e os coroinhas escalados.", estilos["instrucao"])],
        ]
        tabela = Table(linhas, colWidths=[180 * mm])
        tabela.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, BURGUNDY),
                    ("BACKGROUND", (0, 0), (-1, -1), CREME_ESCURO),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        return tabela

    @staticmethod
    def _faixa_secao(titulo: str, estilos) -> Table:
        tabela = Table([[Paragraph(titulo, estilos["secao"])]], colWidths=[180 * mm])
        tabela.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), BURGUNDY),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        return tabela

    @staticmethod
    def _celula_grupo(grupo, estilos, largura_col: float) -> Table:
        linhas = [[Paragraph(f"GRUPO {grupo.numero}", estilos["grupo_titulo"])]]
        for membro in grupo.membros.all().order_by("ordem"):
            texto = f"{membro.ordem}. {membro.coroinha.nome}"
            linhas.append([Paragraph(texto, estilos["nome"])])
        return Table(linhas, colWidths=[largura_col - 24])

    @staticmethod
    def _tabela_grupos(escala_mensal, estilos, largura_col: float) -> Table:
        grupos = list(escala_mensal.grupos.all().order_by("numero"))
        celulas = [
            RelatorioEscalaService._celula_grupo(grupo, estilos, largura_col) for grupo in grupos
        ]
        while len(celulas) < 4:
            celulas.append(Table([[Paragraph("", estilos["normal"])]]))

        tabela = Table(
            [[celulas[0], celulas[1]], [celulas[2], celulas[3]]],
            colWidths=[largura_col, largura_col],
        )
        tabela.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOX", (0, 0), (-1, -1), 1, BURGUNDY),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
                    ("BACKGROUND", (0, 0), (-1, -1), CREME),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        return tabela

    @staticmethod
    def _caixa_escala(escala, estilos, largura: float):
        linhas = [[Paragraph(texto_cabecalho_entrada(escala), estilos["data_cab"])]]
        for texto, coroinha in itens_coroinha_escala(escala):
            for flow in linha_coroinha_flowable(coroinha, texto, estilos["nome"]):
                linhas.append([flow])

        tabela = Table(linhas, colWidths=[largura])
        tabela.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.75, BURGUNDY),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        return KeepTogether([tabela, Spacer(1, 6)])

    @staticmethod
    def _render_secao_escalas(elementos, titulo_secao, subtitulo_secao, escalas, estilos, largura_util):
        if not escalas:
            return
        elementos.append(Spacer(1, 10))
        elementos.append(RelatorioEscalaService._faixa_secao(titulo_secao, estilos))
        if subtitulo_secao:
            elementos.append(Spacer(1, 4))
            elementos.append(Paragraph(subtitulo_secao, estilos["secao_sub"]))
        elementos.append(Spacer(1, 6))
        for escala in escalas:
            elementos.append(RelatorioEscalaService._caixa_escala(escala, estilos, largura_util))

    @staticmethod
    def exportar_mes_pdf(ano: int, mes: int) -> bytes:
        escalas, escala_mensal = carregar_dados_mes(ano, mes)
        por_slot = agrupar_escalas_por_slot(escalas)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=16 * mm,
            rightMargin=16 * mm,
            topMargin=14 * mm,
            bottomMargin=14 * mm,
            title=f"Escala Coroinhas {MESES_PT[mes]}/{ano}",
        )
        largura_util = doc.width
        largura_col_grupo = largura_util / 2

        estilos = RelatorioEscalaService._estilos_pdf()
        mes_nome = MESES_PT[mes].upper()

        elementos = [
            Paragraph("ESCALA DOS COROINHAS", estilos["titulo"]),
            Paragraph(f"{mes_nome} de {ano}", estilos["mes"]),
            Paragraph("Santuário de Fátima — Pastoral dos Coroinhas", estilos["subtitulo"]),
            RelatorioEscalaService._caixa_instrucoes(estilos),
            Spacer(1, 12),
        ]

        if escala_mensal and escala_mensal.grupos.exists():
            elementos.append(RelatorioEscalaService._faixa_secao("GRUPOS DO MÊS (sábado e domingo)", estilos))
            elementos.append(Spacer(1, 6))
            elementos.append(
                Paragraph(
                    "Anote o número do seu grupo. Nos fins de semana, sirva com o grupo indicado abaixo.",
                    estilos["secao_sub"],
                )
            )
            elementos.append(RelatorioEscalaService._tabela_grupos(escala_mensal, estilos, largura_col_grupo))
            elementos.append(Spacer(1, 14))

        if not escalas:
            elementos.append(Paragraph("Nenhuma escala montada neste período.", estilos["normal"]))
        else:
            elementos.append(PageBreak())
            elementos.append(RelatorioEscalaService._faixa_secao("CRONOGRAMA DO MÊS — SANTUÁRIO DE FÁTIMA", estilos))
            elementos.append(Spacer(1, 8))

            for slot, titulo_secao, subtitulo_secao in SECOES_PDF:
                if slot == TipoSlotMissa.COMUNIDADE_DOMINGO:
                    continue
                RelatorioEscalaService._render_secao_escalas(
                    elementos,
                    titulo_secao,
                    subtitulo_secao,
                    por_slot.get(slot, []),
                    estilos,
                    largura_util,
                )

            comunidade = por_slot.get(TipoSlotMissa.COMUNIDADE_DOMINGO, [])
            if comunidade:
                elementos.append(PageBreak())
                RelatorioEscalaService._render_secao_escalas(
                    elementos,
                    "COMUNIDADE SANTO ANTÔNIO · DOMINGO 10h30",
                    "Missas na comunidade (fora do santuário).",
                    comunidade,
                    estilos,
                    largura_util,
                )

            outros = por_slot.get(TipoSlotMissa.OUTRO, [])
            if outros:
                RelatorioEscalaService._render_secao_escalas(
                    elementos,
                    "OUTRAS CELEBRAÇÕES",
                    "",
                    outros,
                    estilos,
                    largura_util,
                )

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
