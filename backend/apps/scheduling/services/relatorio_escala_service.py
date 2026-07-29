import csv
import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from apps.scheduling.models import FuncaoEscala
from apps.scheduling.services.relatorio_escala_pdf_layout import (
    MESES_PT,
    ORIENTACOES_GERAIS_V6,
    agrupar_escalas_por_dia,
    carregar_dados_mes,
    linhas_coroinhas_v6,
    linha_titulo_v6,
    rotulo_dia_semana_curto,
)

BURGUNDY = colors.HexColor("#5C1C24")
CREME = colors.HexColor("#FAF8F5")
CREME_ESCURO = colors.HexColor("#F0EBE3")
CINZA_TEXTO = colors.HexColor("#333333")
CINZA_CLARO = colors.HexColor("#666666")
BORDA = colors.HexColor("#D8D0C8")


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
                "TituloV6",
                parent=base["Heading1"],
                fontSize=22,
                leading=26,
                alignment=TA_CENTER,
                textColor=BURGUNDY,
                spaceAfter=4,
                fontName="Helvetica-Bold",
            ),
            "subtitulo": ParagraphStyle(
                "SubV6",
                parent=base["Normal"],
                fontSize=12,
                leading=15,
                alignment=TA_CENTER,
                textColor=CINZA_TEXTO,
                spaceAfter=10,
            ),
            "legenda": ParagraphStyle(
                "LegendaV6",
                parent=base["Normal"],
                fontSize=8,
                leading=10,
                alignment=TA_CENTER,
                textColor=CINZA_CLARO,
                spaceAfter=8,
            ),
            "grupo_titulo": ParagraphStyle(
                "GrupoTituloV6",
                parent=base["Normal"],
                fontSize=10,
                fontName="Helvetica-Bold",
                textColor=BURGUNDY,
                spaceAfter=4,
            ),
            "secao_sub": ParagraphStyle(
                "SecaoSubV6",
                parent=base["Normal"],
                fontSize=9,
                textColor=CINZA_CLARO,
                alignment=TA_CENTER,
                spaceAfter=8,
            ),
            "dia_num": ParagraphStyle(
                "DiaNum",
                parent=base["Normal"],
                fontSize=20,
                leading=22,
                fontName="Helvetica-Bold",
                textColor=BURGUNDY,
                alignment=TA_CENTER,
            ),
            "dia_semana": ParagraphStyle(
                "DiaSemana",
                parent=base["Normal"],
                fontSize=9,
                leading=11,
                fontName="Helvetica-Bold",
                textColor=CINZA_TEXTO,
                alignment=TA_LEFT,
            ),
            "celebracao_titulo": ParagraphStyle(
                "CelebracaoTitulo",
                parent=base["Normal"],
                fontSize=10,
                leading=13,
                fontName="Helvetica-Bold",
                textColor=BURGUNDY,
                spaceAfter=3,
            ),
            "nome": ParagraphStyle(
                "NomeCoroinha",
                parent=base["Normal"],
                fontSize=9,
                leading=12,
                textColor=CINZA_TEXTO,
                leftIndent=0,
                spaceAfter=1,
            ),
            "orientacoes_titulo": ParagraphStyle(
                "OrientacoesTitulo",
                parent=base["Normal"],
                fontSize=11,
                fontName="Helvetica-Bold",
                textColor=BURGUNDY,
                spaceAfter=6,
            ),
            "orientacao": ParagraphStyle(
                "Orientacao",
                parent=base["Normal"],
                fontSize=9,
                leading=13,
                textColor=CINZA_TEXTO,
                leftIndent=8,
                spaceAfter=3,
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
    def _desenhar_cabecalho_rodape(canvas, doc, ano: int, mes: int):
        mes_nome = MESES_PT[mes]
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(CINZA_CLARO)
        topo = doc.pagesize[1] - 10 * mm
        canvas.drawString(doc.leftMargin, topo, f"SANTUÁRIO DE FÁTIMA  Escala de Coroinhas · {mes_nome} de {ano}")
        canvas.drawRightString(
            doc.pagesize[0] - doc.rightMargin,
            topo,
            f"Documento oficial · Uso interno  Página {canvas.getPageNumber()}",
        )
        canvas.restoreState()

    @staticmethod
    def _celula_grupo(grupo, estilos, largura_col: float) -> Table:
        linhas = [[Paragraph(f"Grupo {grupo.numero}", estilos["grupo_titulo"])]]
        for membro in grupo.membros.all().order_by("ordem"):
            linhas.append([Paragraph(f"{membro.ordem:02d}. {membro.coroinha.nome}", estilos["nome"])])
        if len(linhas) == 1:
            linhas.append([Paragraph("—", estilos["nome"])])
        return Table(linhas, colWidths=[largura_col - 8])

    @staticmethod
    def _tabela_grupos(escala_mensal, estilos, largura_util: float) -> Table:
        grupos = list(escala_mensal.grupos.all().order_by("numero"))
        largura_col = largura_util / 2
        celulas = [RelatorioEscalaService._celula_grupo(g, estilos, largura_col) for g in grupos]
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
                    ("BOX", (0, 0), (-1, -1), 0.75, BURGUNDY),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDA),
                    ("BACKGROUND", (0, 0), (-1, -1), CREME),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        return tabela

    @staticmethod
    def _nota_legenda_celebracoes(estilos) -> Paragraph:
        return Paragraph(
            "Nas missas: <b>S. Antônio</b> = comunidade · <b>Solenidade</b> = dia 13 · "
            "<b>Novena</b> = quarta voluntários",
            estilos["legenda"],
        )

    @staticmethod
    def _linha_celebracao(dia, escala, idx: int, estilos) -> Table:
        dia_label = f"{dia.day:02d}" if idx == 0 else ""
        semana_label = rotulo_dia_semana_curto(dia) if idx == 0 else ""

        linhas_conteudo = [[Paragraph(linha_titulo_v6(escala), estilos["celebracao_titulo"])]]
        for nome in linhas_coroinhas_v6(escala):
            linhas_conteudo.append([Paragraph(nome, estilos["nome"])])
        conteudo = Table(linhas_conteudo, colWidths=[140 * mm])
        conteudo.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )

        tabela = Table(
            [
                [
                    Paragraph(dia_label, estilos["dia_num"]),
                    Paragraph(semana_label, estilos["dia_semana"]),
                    conteudo,
                ]
            ],
            colWidths=[14 * mm, 22 * mm, 140 * mm],
            hAlign="LEFT",
        )
        tabela.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.25, BORDA),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        return tabela

    @staticmethod
    def _secao_orientacoes(estilos) -> list:
        elementos = [
            Spacer(1, 10),
            Paragraph("ORIENTAÇÕES GERAIS", estilos["orientacoes_titulo"]),
        ]
        for texto in ORIENTACOES_GERAIS_V6:
            elementos.append(Paragraph(f"• {texto}", estilos["orientacao"]))
        return elementos

    @staticmethod
    def exportar_mes_pdf(ano: int, mes: int) -> bytes:
        escalas, escala_mensal = carregar_dados_mes(ano, mes)
        dias = agrupar_escalas_por_dia(escalas)

        buffer = io.BytesIO()
        mes_nome = MESES_PT[mes]

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=14 * mm,
            rightMargin=14 * mm,
            topMargin=18 * mm,
            bottomMargin=14 * mm,
            title=f"Escala Coroinhas {mes_nome}/{ano}",
        )
        largura_util = doc.width

        estilos = RelatorioEscalaService._estilos_pdf()

        def on_page(canvas, document):
            RelatorioEscalaService._desenhar_cabecalho_rodape(canvas, document, ano, mes)

        elementos = [
            Paragraph("Escala de Coroinhas", estilos["titulo"]),
            Paragraph(f"{mes_nome} de {ano} · Santuário de Fátima", estilos["subtitulo"]),
        ]

        if escala_mensal and escala_mensal.grupos.exists():
            elementos.append(
                Paragraph("Grupos do mês (sábado e domingo)", estilos["secao_sub"])
            )
            elementos.append(RelatorioEscalaService._tabela_grupos(escala_mensal, estilos, largura_util))
            elementos.append(RelatorioEscalaService._nota_legenda_celebracoes(estilos))
            elementos.append(Spacer(1, 10))

        elementos.append(Paragraph("Cronograma do mês", estilos["grupo_titulo"]))
        elementos.append(Spacer(1, 4))

        if not escalas:
            elementos.append(Paragraph("Nenhuma escala montada neste período.", estilos["normal"]))
        else:
            for dia, escalas_dia in dias:
                for idx, escala in enumerate(escalas_dia):
                    elementos.append(
                        RelatorioEscalaService._linha_celebracao(dia, escala, idx, estilos)
                    )
            elementos.extend(RelatorioEscalaService._secao_orientacoes(estilos))

        doc.build(elementos, onFirstPage=on_page, onLaterPages=on_page)
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
