"""Testes de remanejamento Kanban da escala mensal."""

from datetime import date, time, timedelta

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
from apps.scheduling.services.escala_service import EscalaService
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
        destino = Escala.objects.filter(
            escala_mensal=escala_mensal,
            missa__tipo_slot=TipoSlotMissa.SEXTA_ADORACAO,
        ).first()
        origem = Escala.objects.filter(
            escala_mensal=escala_mensal,
            missa__tipo_slot=TipoSlotMissa.DOMINGO_NOITE,
            data=destino.data + timedelta(days=2),
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


class TestTransferenciaComunidadeAdoracao:
    def test_mover_para_comunidade_reduz_domingo_manha(
        self, coordenador, missas_mensais, coroinhas_grupo
    ):
        GeradorEscalaMensalService.gerar(ano=2026, mes=8, usuario=coordenador, tamanho_grupo=9)
        escala_mensal = EscalaMensal.objects.get(ano=2026, mes=8)
        dom_manha = Escala.objects.filter(
            escala_mensal=escala_mensal,
            missa__tipo_slot=TipoSlotMissa.DOMINGO_MANHA,
        ).first()
        comunidade = Escala.objects.filter(
            escala_mensal=escala_mensal,
            missa__tipo_slot=TipoSlotMissa.COMUNIDADE_DOMINGO,
            data=dom_manha.data,
        ).first()
        assert dom_manha.itens.count() == 9

        coroinha_id = dom_manha.itens.first().coroinha_id
        RemanejamentoEscalaService.transferir_para_celebracao(
            escala_mensal, coroinha_id, comunidade.id, grupo_numero=dom_manha.grupo_numero
        )

        dom_manha.refresh_from_db()
        comunidade.refresh_from_db()
        assert dom_manha.itens.count() == 8
        assert comunidade.itens.filter(coroinha_id=coroinha_id).exists()

    def test_mover_para_sexta_reduz_domingo_noite(
        self, coordenador, missas_mensais, coroinhas_grupo
    ):
        GeradorEscalaMensalService.gerar(ano=2026, mes=8, usuario=coordenador, tamanho_grupo=9)
        escala_mensal = EscalaMensal.objects.get(ano=2026, mes=8)
        dom_noite = Escala.objects.filter(
            escala_mensal=escala_mensal,
            missa__tipo_slot=TipoSlotMissa.DOMINGO_NOITE,
        ).first()
        sexta = Escala.objects.filter(
            escala_mensal=escala_mensal,
            missa__tipo_slot=TipoSlotMissa.SEXTA_ADORACAO,
            data=dom_noite.data - timedelta(days=2),
        ).first()
        assert dom_noite.itens.count() == 9

        coroinha_id = dom_noite.itens.first().coroinha_id
        RemanejamentoEscalaService.transferir_para_celebracao(
            escala_mensal, coroinha_id, sexta.id, grupo_numero=dom_noite.grupo_numero
        )

        dom_noite.refresh_from_db()
        sexta.refresh_from_db()
        assert dom_noite.itens.count() == 8
        assert sexta.itens.filter(coroinha_id=coroinha_id).exists()

    def test_sincronizar_grupo_respeita_comunidade(
        self, coordenador, missas_mensais, coroinhas_grupo
    ):
        GeradorEscalaMensalService.gerar(ano=2026, mes=8, usuario=coordenador, tamanho_grupo=9)
        escala_mensal = EscalaMensal.objects.get(ano=2026, mes=8)
        dom_manha = Escala.objects.filter(
            escala_mensal=escala_mensal,
            missa__tipo_slot=TipoSlotMissa.DOMINGO_MANHA,
        ).first()
        comunidade = Escala.objects.filter(
            escala_mensal=escala_mensal,
            missa__tipo_slot=TipoSlotMissa.COMUNIDADE_DOMINGO,
            data=dom_manha.data,
        ).first()
        ids_transferir = list(dom_manha.itens.values_list("coroinha_id", flat=True)[:2])
        EscalaService.definir_membros(comunidade, ids_transferir)

        RemanejamentoEscalaService.sincronizar_escalas_grupo(
            escala_mensal, dom_manha.grupo_numero
        )
        dom_manha.refresh_from_db()
        assert dom_manha.itens.count() == 7
        for cid in ids_transferir:
            assert comunidade.itens.filter(coroinha_id=cid).exists()
            assert not dom_manha.itens.filter(coroinha_id=cid).exists()


class TestRemoverDoGrupo:
    def test_remover_do_grupo_sai_de_todas_escalas(
        self, coordenador, missas_mensais, coroinhas_grupo
    ):
        GeradorEscalaMensalService.gerar(ano=2026, mes=8, usuario=coordenador, tamanho_grupo=9)
        escala_mensal = EscalaMensal.objects.get(ano=2026, mes=8)
        grupo1 = GrupoMensal.objects.get(escala_mensal=escala_mensal, numero=1)
        coroinha = grupo1.membros.order_by("ordem").first().coroinha

        assert EscalaItem.objects.filter(
            escala__escala_mensal=escala_mensal, coroinha=coroinha
        ).exists()

        RemanejamentoEscalaService.remover_do_grupo(escala_mensal, coroinha.id)

        assert not GrupoMensalMembro.objects.filter(
            grupo__escala_mensal=escala_mensal, coroinha=coroinha
        ).exists()
        assert not EscalaItem.objects.filter(
            escala__escala_mensal=escala_mensal, coroinha=coroinha
        ).exists()

    def test_api_remover_grupo(self, client_coordenador, coordenador, missas_mensais, coroinhas_grupo):
        GeradorEscalaMensalService.gerar(ano=2026, mes=8, usuario=coordenador)
        escala_mensal = EscalaMensal.objects.get(ano=2026, mes=8)
        coroinha_id = (
            GrupoMensalMembro.objects.filter(grupo__escala_mensal=escala_mensal, grupo__numero=2)
            .first()
            .coroinha_id
        )
        res = client_coordenador.patch(
            "/api/v1/escalas/mensal/remover-grupo/",
            {"ano": 2026, "mes": 8, "coroinha_id": coroinha_id},
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        assert not GrupoMensalMembro.objects.filter(
            grupo__escala_mensal=escala_mensal, coroinha_id=coroinha_id
        ).exists()


class TestComunidadeFixa:
    def test_comunidade_fixa_excluida_da_geracao(
        self, coordenador, missas_mensais, coroinhas_grupo
    ):
        from apps.membership.models import ComunidadeFixa

        Coroinha.objects.filter(pk=coroinhas_grupo[0].pk).update(
            comunidade_fixa=ComunidadeFixa.SANTA_TEREZINHA
        )
        Coroinha.objects.filter(pk=coroinhas_grupo[1].pk).update(
            comunidade_fixa=ComunidadeFixa.NOSSA_SENHORA_AUXILIADORA
        )

        GeradorEscalaMensalService.gerar(ano=2026, mes=8, usuario=coordenador, tamanho_grupo=8)
        escala_mensal = EscalaMensal.objects.get(ano=2026, mes=8)
        ids_grupos = set(
            GrupoMensalMembro.objects.filter(grupo__escala_mensal=escala_mensal).values_list(
                "coroinha_id", flat=True
            )
        )
        assert coroinhas_grupo[0].id not in ids_grupos
        assert coroinhas_grupo[1].id not in ids_grupos

    def test_nao_adiciona_comunidade_fixa_ao_grupo(
        self, coordenador, missas_mensais, coroinhas_grupo
    ):
        from apps.membership.models import ComunidadeFixa

        GeradorEscalaMensalService.gerar(ano=2026, mes=8, usuario=coordenador, tamanho_grupo=9)
        escala_mensal = EscalaMensal.objects.get(ano=2026, mes=8)
        fixo = coroinhas_grupo[-1]
        Coroinha.objects.filter(pk=fixo.pk).update(
            comunidade_fixa=ComunidadeFixa.SANTA_TEREZINHA
        )

        with pytest.raises(ValueError, match="escala fixa"):
            RemanejamentoEscalaService.mover_grupo(escala_mensal, fixo.id, 1)

