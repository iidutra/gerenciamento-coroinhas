"""Testes do PDF paroquial de escala mensal."""

from datetime import date, time

import pytest

from apps.scheduling.models import (
    DiaSemana,
    Escala,
    LocalCelebracao,
    Missa,
    ModoEscala,
    TipoSlotMissa,
)
from apps.scheduling.services.gerador_escala_mensal_service import GeradorEscalaMensalService
from apps.scheduling.services.relatorio_escala_pdf_layout import (
    agrupar_escalas_por_dia,
    linha_titulo_v6,
    titulo_celebracao_v6,
)
from apps.scheduling.services.relatorio_escala_service import RelatorioEscalaService

pytestmark = pytest.mark.django_db


@pytest.fixture
def missas_mensais(db):
    slots = [
        ("Sábado 18h30", DiaSemana.SABADO, TipoSlotMissa.SABADO_NOITE, time(18, 30)),
        ("Domingo 08h", DiaSemana.DOMINGO, TipoSlotMissa.DOMINGO_MANHA, time(8, 0)),
        ("Domingo 18h30", DiaSemana.DOMINGO, TipoSlotMissa.DOMINGO_NOITE, time(18, 30)),
        ("Sexta 18h", DiaSemana.SEXTA, TipoSlotMissa.SEXTA_ADORACAO, time(18, 0)),
        ("Quarta 19h", DiaSemana.QUARTA, TipoSlotMissa.QUARTA_VOLUNTARIOS, time(19, 0)),
        (
            "Comunidade — Domingo 10h30",
            DiaSemana.DOMINGO,
            TipoSlotMissa.COMUNIDADE_DOMINGO,
            time(10, 30),
        ),
    ]
    for nome, dia, slot, horario in slots:
        local = (
            LocalCelebracao.COMUNIDADE
            if slot == TipoSlotMissa.COMUNIDADE_DOMINGO
            else LocalCelebracao.SANTUARIO
        )
        Missa.objects.create(
            nome=nome,
            dia_semana=dia,
            horario=horario,
            ativa=True,
            tipo_slot=slot,
            local=local,
        )


@pytest.fixture
def coroinhas_grupo(db):
    from apps.membership.models import Coroinha, StatusCoroinha, Turma

    lista = []
    for i in range(36):
        lista.append(
            Coroinha.objects.create(
                nome=f"Coroinha {i + 1:02d}",
                data_nascimento=date(2010 + (i % 8), 1, 15),
                turma=Turma.INTERMEDIARIO,
                status=StatusCoroinha.ATIVO,
                antigo=(i % 3 == 0),
            )
        )
    return lista


class TestPdfParoquial:
    def test_texto_cabecalho_formato_completo(self, db):
        missa = Missa.objects.create(
            nome="Domingo 08h",
            dia_semana=DiaSemana.DOMINGO,
            horario=time(8, 0),
            ativa=True,
            tipo_slot=TipoSlotMissa.DOMINGO_MANHA,
            local=LocalCelebracao.SANTUARIO,
        )
        escala = Escala.objects.create(
            data=date(2026, 8, 2),
            missa=missa,
            modo=ModoEscala.GRUPO_MENSAL,
            grupo_numero=2,
        )
        assert linha_titulo_v6(escala) == "8h Missa da Manhã Grupo 2"

    def test_texto_cabecalho_comunidade_santo_antonio(self, db):
        missa = Missa.objects.create(
            nome="Comunidade — Domingo 10h30",
            dia_semana=DiaSemana.DOMINGO,
            horario=time(10, 30),
            ativa=True,
            tipo_slot=TipoSlotMissa.COMUNIDADE_DOMINGO,
            local=LocalCelebracao.COMUNIDADE,
        )
        escala = Escala.objects.create(
            data=date(2026, 8, 2),
            missa=missa,
            modo=ModoEscala.SELECAO_MANUAL,
        )
        assert linha_titulo_v6(escala) == "10h30 Comunidade Santo Antônio"

    def test_titulo_missa_dia_13(self, db):
        for hora, esperado in [(6, "Missa das 6h"), (9, "Missa das 9h"), (12, "Missa das 12h"), (18, "Missa das 18h")]:
            missa = Missa.objects.create(
                nome=f"Dia 13 — {hora:02d}h",
                dia_mes=13,
                horario=time(hora, 0),
                ativa=True,
                tipo_slot=TipoSlotMissa.DIA_13,
                local=LocalCelebracao.SANTUARIO,
            )
            escala = Escala.objects.create(
                data=date(2026, 8, 13),
                missa=missa,
                modo=ModoEscala.SELECAO_MANUAL,
            )
            assert titulo_celebracao_v6(escala) == esperado
            assert linha_titulo_v6(escala) == esperado

    def test_pdf_contem_estrutura_paroquial(self, coordenador, missas_mensais, coroinhas_grupo):
        GeradorEscalaMensalService.gerar(ano=2026, mes=7, usuario=coordenador, tamanho_grupo=9)
        pdf = RelatorioEscalaService.exportar_mes_pdf(2026, 7)
        assert pdf[:4] == b"%PDF"
        assert len(pdf) > 4000
        data = RelatorioEscalaService.exportar_mes_json(2026, 7)
        assert len(data["grupos"]) == 4
        slots = {e["tipo_slot"] for e in data["escalas"]}
        assert TipoSlotMissa.SEXTA_ADORACAO in slots
        assert TipoSlotMissa.SABADO_NOITE in slots

    def test_json_inclui_grupos(self, coordenador, missas_mensais, coroinhas_grupo):
        GeradorEscalaMensalService.gerar(ano=2026, mes=7, usuario=coordenador, tamanho_grupo=9)
        data = RelatorioEscalaService.exportar_mes_json(2026, 7)
        assert len(data["grupos"]) == 4
        assert len(data["escalas"]) > 0

    def test_pdf_gera_com_coroinhas_cadastrados(self, coordenador, missas_mensais, coroinhas_grupo):
        GeradorEscalaMensalService.gerar(ano=2026, mes=7, usuario=coordenador, tamanho_grupo=9)
        pdf = RelatorioEscalaService.exportar_mes_pdf(2026, 7)
        assert pdf[:4] == b"%PDF"
        assert len(pdf) > 4000

    def test_cronograma_pdf_ordem_cronologica(self, coordenador, missas_mensais, coroinhas_grupo):
        GeradorEscalaMensalService.gerar(ano=2026, mes=7, usuario=coordenador, tamanho_grupo=9)
        escalas = list(Escala.objects.select_related("missa").order_by("data", "missa__horario"))
        dias = agrupar_escalas_por_dia(escalas)
        assert dias
        datas = [dia for dia, _ in dias]
        assert datas == sorted(datas)
        for _dia, escalas_dia in dias:
            ordem = [e.missa.tipo_slot for e in escalas_dia]
            assert TipoSlotMissa.COMUNIDADE_DOMINGO not in ordem or ordem.index(
                TipoSlotMissa.COMUNIDADE_DOMINGO
            ) < ordem.index(TipoSlotMissa.DOMINGO_NOITE) if TipoSlotMissa.DOMINGO_NOITE in ordem else True
