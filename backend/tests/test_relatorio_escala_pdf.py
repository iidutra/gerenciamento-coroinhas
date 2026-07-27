"""Testes do PDF paroquial de escala mensal."""

from datetime import date, time

import pytest

from apps.scheduling.models import DiaSemana, LocalCelebracao, Missa, TipoSlotMissa
from apps.scheduling.services.gerador_escala_mensal_service import GeradorEscalaMensalService
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

    def test_pdf_com_foto_cadastrada(self, coordenador, missas_mensais, coroinhas_grupo):
        from django.core.files.base import ContentFile

        from apps.membership.utils.avatar_placeholder import avatar_placeholder_png

        c = coroinhas_grupo[0]
        c.foto.save("foto-teste.png", ContentFile(avatar_placeholder_png(64).read()), save=True)

        GeradorEscalaMensalService.gerar(ano=2026, mes=7, usuario=coordenador, tamanho_grupo=9)
        pdf_sem = RelatorioEscalaService.exportar_mes_pdf(2026, 6)
        pdf_com = RelatorioEscalaService.exportar_mes_pdf(2026, 7)
        assert pdf_com[:4] == b"%PDF"
        assert len(pdf_com) >= len(pdf_sem)
