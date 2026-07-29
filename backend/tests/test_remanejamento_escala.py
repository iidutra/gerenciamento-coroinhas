"""Testes de remanejamento Kanban da escala mensal."""

from datetime import date, time

import pytest
from rest_framework import status

from apps.membership.models import Coroinha, StatusCoroinha
from apps.scheduling.models import (
    DiaSemana,
    Escala,
    EscalaItem,
    EscalaMensal,
    GrupoMensal,
    GrupoMensalMembro,
    LocalCelebracao,
    Missa,
    TipoSlotMissa,
)
from apps.scheduling.services.gerador_escala_mensal_service import GeradorEscalaMensalService
from apps.scheduling.services.remanejamento_escala_service import RemanejamentoEscalaService

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
    lista = []
    for i in range(36):
        lista.append(
            Coroinha.objects.create(
                nome=f"Coroinha {i + 1:02d}",
                data_nascimento=date(2010 + (i % 8), 1, 15),
                status=StatusCoroinha.ATIVO,
                antigo=(i % 3 == 0),
            )
        )
    return lista


class TestRemanejamentoGrupo:
    def test_mover_coroinha_entre_grupos_sincroniza_escalas(
        self, coordenador, missas_mensais, coroinhas_grupo
    ):
        GeradorEscalaMensalService.gerar(ano=2026, mes=8, usuario=coordenador, tamanho_grupo=9)
        escala_mensal = EscalaMensal.objects.get(ano=2026, mes=8)
        grupo1 = GrupoMensal.objects.get(escala_mensal=escala_mensal, numero=1)
        coroinha = grupo1.membros.order_by("ordem").first().coroinha

        escala_grupo1 = Escala.objects.filter(escala_mensal=escala_mensal, grupo_numero=1).first()
        assert escala_grupo1.itens.filter(coroinha=coroinha).exists()

        RemanejamentoEscalaService.mover_grupo(escala_mensal, coroinha.id, 2)

        assert not GrupoMensalMembro.objects.filter(grupo=grupo1, coroinha=coroinha).exists()
        assert GrupoMensalMembro.objects.filter(
            grupo__escala_mensal=escala_mensal,
            grupo__numero=2,
            coroinha=coroinha,
        ).exists()
        assert not escala_grupo1.itens.filter(coroinha=coroinha).exists()
        escala_grupo2 = Escala.objects.filter(escala_mensal=escala_mensal, grupo_numero=2).first()
        assert escala_grupo2.itens.filter(coroinha=coroinha).exists()

    def test_api_remanejar_grupo(self, client_coordenador, coordenador, missas_mensais, coroinhas_grupo):
        GeradorEscalaMensalService.gerar(ano=2026, mes=8, usuario=coordenador)
        escala_mensal = EscalaMensal.objects.get(ano=2026, mes=8)
        coroinha_id = (
            GrupoMensalMembro.objects.filter(grupo__escala_mensal=escala_mensal, grupo__numero=1)
            .first()
            .coroinha_id
        )
        res = client_coordenador.patch(
            "/api/v1/escalas/mensal/remanejar-grupo/",
            {
                "ano": 2026,
                "mes": 8,
                "coroinha_id": coroinha_id,
                "grupo_destino": 3,
            },
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        assert "escala_mensal" in res.data
        assert "escalas" in res.data


class TestRemanejamentoCelebracao:
    def test_mover_coroinha_entre_celebracoes(self, coordenador, missas_mensais, coroinhas_grupo):
        GeradorEscalaMensalService.gerar(ano=2026, mes=8, usuario=coordenador, tamanho_grupo=9)
        escala_mensal = EscalaMensal.objects.get(ano=2026, mes=8)
        origem = Escala.objects.filter(escala_mensal=escala_mensal, grupo_numero=1).first()
        destino = Escala.objects.filter(
            escala_mensal=escala_mensal,
            missa__tipo_slot=TipoSlotMissa.SEXTA_ADORACAO,
        ).first()
        coroinha_id = origem.itens.first().coroinha_id

        RemanejamentoEscalaService.mover_celebracao(
            coroinha_id=coroinha_id,
            escala_origem_id=origem.id,
            escala_destino_id=destino.id,
        )

        assert not EscalaItem.objects.filter(escala=origem, coroinha_id=coroinha_id).exists()
        assert EscalaItem.objects.filter(escala=destino, coroinha_id=coroinha_id).exists()

    def test_remover_coroinha_da_celebracao(self, coordenador, missas_mensais, coroinhas_grupo):
        GeradorEscalaMensalService.gerar(ano=2026, mes=8, usuario=coordenador, tamanho_grupo=9)
        escala_mensal = EscalaMensal.objects.get(ano=2026, mes=8)
        origem = Escala.objects.filter(
            escala_mensal=escala_mensal,
            missa__tipo_slot=TipoSlotMissa.SEXTA_ADORACAO,
        ).first()
        coroinha_id = origem.itens.first().coroinha_id
        total_antes = origem.itens.count()

        RemanejamentoEscalaService.mover_celebracao(
            coroinha_id=coroinha_id,
            escala_origem_id=origem.id,
            escala_destino_id=None,
        )

        origem.refresh_from_db()
        assert origem.itens.count() == total_antes - 1

    def test_api_mover_coroinha(self, client_coordenador, coordenador, missas_mensais, coroinhas_grupo):
        GeradorEscalaMensalService.gerar(ano=2026, mes=8, usuario=coordenador)
        escala_mensal = EscalaMensal.objects.get(ano=2026, mes=8)
        origem = Escala.objects.filter(escala_mensal=escala_mensal, grupo_numero=1).first()
        destino = Escala.objects.filter(
            escala_mensal=escala_mensal,
            missa__tipo_slot=TipoSlotMissa.SEXTA_ADORACAO,
        ).first()
        coroinha_id = origem.itens.first().coroinha_id

        res = client_coordenador.patch(
            f"/api/v1/escalas/{origem.id}/mover-coroinha/",
            {"coroinha_id": coroinha_id, "escala_destino_id": destino.id},
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        assert "origem" in res.data
        assert "destino" in res.data
