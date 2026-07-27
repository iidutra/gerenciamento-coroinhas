"""Testes do gerador de escala mensal."""

from datetime import date, time

import pytest
from rest_framework import status

from apps.membership.models import Coroinha, StatusCoroinha, Turma
from apps.scheduling.models import (
    DiaSemana,
    Escala,
    LocalCelebracao,
    Missa,
    TipoSlotMissa,
)
from apps.scheduling.services.gerador_escala_mensal_service import GeradorEscalaMensalService

pytestmark = pytest.mark.django_db


@pytest.fixture
def missas_mensais(db):
    """Missas usadas pelo gerador mensual (julho/2026)."""
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
        ("Dia 13 — 06h", None, TipoSlotMissa.DIA_13, time(6, 0)),
    ]
    missas = {}
    for nome, dia, slot, horario in slots:
        local = (
            LocalCelebracao.COMUNIDADE
            if slot == TipoSlotMissa.COMUNIDADE_DOMINGO
            else LocalCelebracao.SANTUARIO
        )
        m = Missa.objects.create(
            nome=nome,
            dia_semana=dia,
            dia_mes=13 if slot == TipoSlotMissa.DIA_13 else None,
            horario=horario,
            ativa=True,
            tipo_slot=slot,
            local=local,
        )
        missas[slot] = m
    return missas


@pytest.fixture
def coroinhas_grupo(db):
    """36 coroinhas ativos — mínimo para 4 grupos × 9."""
    lista = []
    for i in range(36):
        c = Coroinha.objects.create(
            nome=f"Coroinha {i + 1:02d}",
            data_nascimento=date(2010 + (i % 8), 1, 15),
            turma=Turma.INTERMEDIARIO,
            status=StatusCoroinha.ATIVO,
            antigo=(i % 3 == 0),
            endereco="Centro" if i % 2 == 0 else "Cohab",
        )
        lista.append(c)
    return lista


class TestGeradorEscalaMensal:
    def test_gera_mes_com_grupos(self, coordenador, missas_mensais, coroinhas_grupo):
        em = GeradorEscalaMensalService.gerar(
            ano=2026,
            mes=7,
            usuario=coordenador,
            tamanho_grupo=9,
        )
        assert em.grupos.count() == 4
        assert em.escalas.count() > 0

        sabados = Escala.objects.filter(
            data__year=2026,
            data__month=7,
            missa__tipo_slot=TipoSlotMissa.SABADO_NOITE,
        )
        assert sabados.exists()
        primeira = sabados.order_by("data").first()
        assert primeira.grupo_numero is not None
        assert primeira.itens.count() == 9

    def test_quarta_sem_coroinhas(self, coordenador, missas_mensais, coroinhas_grupo):
        GeradorEscalaMensalService.gerar(ano=2026, mes=7, usuario=coordenador, tamanho_grupo=9)
        quartas = Escala.objects.filter(
            data__year=2026,
            data__month=7,
            missa__tipo_slot=TipoSlotMissa.QUARTA_VOLUNTARIOS,
        )
        assert quartas.count() >= 4
        for escala in quartas:
            assert escala.voluntarios is True
            assert escala.itens.count() == 0
            assert "Voluntários" in escala.observacao

    def test_dia_13_nao_gerado(self, coordenador, missas_mensais, coroinhas_grupo):
        GeradorEscalaMensalService.gerar(ano=2026, mes=7, usuario=coordenador, tamanho_grupo=9)
        dia13 = Escala.objects.filter(
            data=date(2026, 7, 13),
            missa__tipo_slot=TipoSlotMissa.DIA_13,
        )
        assert dia13.count() == 0

    def test_tamanho_grupo_configuravel(self, coordenador, missas_mensais, coroinhas_grupo):
        em = GeradorEscalaMensalService.gerar(
            ano=2026,
            mes=8,
            usuario=coordenador,
            tamanho_grupo=6,
            substituir=True,
        )
        assert em.tamanho_grupo == 6
        sab = Escala.objects.filter(
            data__year=2026,
            data__month=8,
            missa__tipo_slot=TipoSlotMissa.SABADO_NOITE,
        ).first()
        assert sab.itens.count() == 6

    def test_mes_duplicado_falha(self, coordenador, missas_mensais, coroinhas_grupo):
        GeradorEscalaMensalService.gerar(ano=2026, mes=7, usuario=coordenador, tamanho_grupo=9)
        with pytest.raises(ValueError, match="Já existe escala mensal"):
            GeradorEscalaMensalService.gerar(ano=2026, mes=7, usuario=coordenador, tamanho_grupo=9)


class TestGerarMesAPI:
    def test_gerar_mes_via_api(self, client_coordenador, missas_mensais, coroinhas_grupo):
        res = client_coordenador.post(
            "/api/v1/escalas/gerar-mes/",
            {
                "ano": 2026,
                "mes": 7,
                "tamanho_grupo": 9,
                "quantidade_sexta": 2,
                "quantidade_comunidade": 2,
            },
            format="json",
        )
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data["total_escalas"] > 0
        assert len(res.data["grupos"]) == 4

    def test_padre_nao_gera_mes(self, client_padre, missas_mensais, coroinhas_grupo):
        res = client_padre.post(
            "/api/v1/escalas/gerar-mes/",
            {"ano": 2026, "mes": 7, "tamanho_grupo": 9},
            format="json",
        )
        assert res.status_code == status.HTTP_403_FORBIDDEN
