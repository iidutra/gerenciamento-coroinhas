from datetime import date

import pytest
from rest_framework import status

from apps.scheduling.models import FuncaoEscala
from apps.scheduling.services.escala_service import EscalaService
from apps.scheduling.services.relatorio_escala_service import RelatorioEscalaService

pytestmark = pytest.mark.django_db


class TestEscalaService:
    def test_montar_escala_automatica(self, coordenador, missa_domingo, coroinha):
        escala = EscalaService.montar(
            data=date(2026, 6, 15),
            missa_id=missa_domingo.id,
            modo="SorteioAutomatico",
            quantidade=1,
            usuario=coordenador,
        )
        assert escala.itens.count() == 1
        assert escala.itens.first().coroinha_id == coroinha.id

    def test_montar_escala_duplicada_falha(self, coordenador, missa_domingo, coroinha):
        EscalaService.montar(
            data=date(2026, 6, 15),
            missa_id=missa_domingo.id,
            modo="SorteioAutomatico",
            quantidade=1,
            usuario=coordenador,
        )
        with pytest.raises(ValueError, match="Já existe escala"):
            EscalaService.montar(
                data=date(2026, 6, 15),
                missa_id=missa_domingo.id,
                modo="SorteioAutomatico",
                quantidade=1,
                usuario=coordenador,
            )

    def test_atribuir_duas_velas(self, coordenador, missa_domingo, coroinha):
        coroinha2 = coroinha.__class__.objects.create(
            nome="Maria Teste",
            data_nascimento=date(2013, 5, 10),
            turma=coroinha.turma,
            status=coroinha.status,
        )
        escala = EscalaService.montar(
            data=date(2026, 6, 20),
            missa_id=missa_domingo.id,
            modo="SorteioAutomatico",
            quantidade=2,
            usuario=coordenador,
        )
        EscalaService.atribuir_funcoes(
            escala,
            {
                FuncaoEscala.VELA_1.value: coroinha.id,
                FuncaoEscala.VELA_2.value: coroinha2.id,
            },
        )
        funcoes = set(escala.itens.exclude(funcao__isnull=True).values_list("funcao", flat=True))
        assert funcoes == {FuncaoEscala.VELA_1, FuncaoEscala.VELA_2}

    def test_mesmo_coroinha_duas_funcoes_falha(self, coordenador, missa_domingo, coroinha):
        escala = EscalaService.montar(
            data=date(2026, 6, 22),
            missa_id=missa_domingo.id,
            modo="SorteioAutomatico",
            quantidade=1,
            usuario=coordenador,
        )
        with pytest.raises(ValueError, match="duas funções"):
            EscalaService.atribuir_funcoes(
                escala,
                {FuncaoEscala.VELA_1.value: coroinha.id, FuncaoEscala.CRUZ.value: coroinha.id},
            )


class TestEscalaAPI:
    def test_montar_via_api(self, client_coordenador, missa_domingo, coroinha):
        res = client_coordenador.post(
            "/api/v1/escalas/montar/",
            {
                "data": "2026-06-25",
                "missa_id": missa_domingo.id,
                "modo": "SorteioAutomatico",
                "quantidade": 1,
            },
            format="json",
        )
        assert res.status_code == status.HTTP_201_CREATED
        assert len(res.data["itens"]) == 1

    def test_padre_nao_monta_escala(self, client_padre, missa_domingo):
        res = client_padre.post(
            "/api/v1/escalas/montar/",
            {
                "data": "2026-06-26",
                "missa_id": missa_domingo.id,
                "modo": "SorteioAutomatico",
                "quantidade": 1,
            },
            format="json",
        )
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_excluir_escala(self, client_coordenador, coordenador, missa_domingo, coroinha):
        from apps.scheduling.models import Escala

        escala = EscalaService.montar(
            data=date(2026, 8, 3),
            missa_id=missa_domingo.id,
            modo="SorteioAutomatico",
            quantidade=1,
            usuario=coordenador,
        )
        res = client_coordenador.delete(f"/api/v1/escalas/{escala.id}/")
        assert res.status_code == status.HTTP_204_NO_CONTENT
        assert not Escala.objects.filter(id=escala.id).exists()

    def test_padre_nao_exclui_escala(self, client_padre, coordenador, missa_domingo, coroinha):
        escala = EscalaService.montar(
            data=date(2026, 8, 4),
            missa_id=missa_domingo.id,
            modo="SorteioAutomatico",
            quantidade=1,
            usuario=coordenador,
        )
        res = client_padre.delete(f"/api/v1/escalas/{escala.id}/")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_definir_membros_add_remove(self, client_coordenador, coordenador, missa_domingo, coroinha):
        coroinha2 = coroinha.__class__.objects.create(
            nome="Maria Teste",
            data_nascimento=date(2013, 5, 10),
            status=coroinha.status,
        )
        escala = EscalaService.montar(
            data=date(2026, 8, 5),
            missa_id=missa_domingo.id,
            modo="SelecaoManual",
            quantidade=1,
            usuario=coordenador,
            coroinha_ids=[coroinha.id],
        )
        # troca: remove coroinha, adiciona coroinha2
        res = client_coordenador.patch(
            f"/api/v1/escalas/{escala.id}/membros/",
            {"coroinha_ids": [coroinha2.id]},
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        ids = {i["coroinha_id"] for i in res.data["itens"]}
        assert ids == {coroinha2.id}


class TestNotificacaoFuncao:
    CORPO = "Olá {nome}, você está escalado para servir em {data} — {missa} ({horario}). Função: {funcao}."

    def test_sem_funcao_remove_frase(self, coordenador, missa_domingo, coroinha):
        from apps.communication.services.comunicacao_service import ComunicacaoService
        from apps.scheduling.models import Escala

        escala = EscalaService.montar(
            data=date(2026, 9, 1),
            missa_id=missa_domingo.id,
            modo="SorteioAutomatico",
            quantidade=1,
            usuario=coordenador,
        )
        escala = Escala.objects.prefetch_related("itens__coroinha", "missa").get(pk=escala.pk)
        texto = ComunicacaoService._render_para_coroinha(self.CORPO, coroinha, escala)
        assert "Função" not in texto
        assert texto.rstrip().endswith(").")

    def test_com_funcao_inclui_frase(self, coordenador, missa_domingo, coroinha):
        from apps.communication.services.comunicacao_service import ComunicacaoService
        from apps.scheduling.models import Escala

        escala = EscalaService.montar(
            data=date(2026, 9, 2),
            missa_id=missa_domingo.id,
            modo="SorteioAutomatico",
            quantidade=1,
            usuario=coordenador,
        )
        EscalaService.atribuir_funcoes(escala, {FuncaoEscala.CRUZ.value: coroinha.id})
        escala = Escala.objects.prefetch_related("itens__coroinha", "missa").get(pk=escala.pk)
        texto = ComunicacaoService._render_para_coroinha(self.CORPO, coroinha, escala)
        assert "Função: Cruz." in texto


class TestRelatorioPDF:
    def test_exportar_pdf_mes(self, coordenador, missa_domingo, coroinha):
        EscalaService.montar(
            data=date(2026, 6, 10),
            missa_id=missa_domingo.id,
            modo="SorteioAutomatico",
            quantidade=1,
            usuario=coordenador,
        )
        pdf = RelatorioEscalaService.exportar_mes_pdf(2026, 6)
        assert pdf[:4] == b"%PDF"
        assert len(pdf) > 500

    def test_exportar_pdf_via_api(self, client_coordenador, coordenador, missa_domingo, coroinha):
        EscalaService.montar(
            data=date(2026, 7, 5),
            missa_id=missa_domingo.id,
            modo="SorteioAutomatico",
            quantidade=1,
            usuario=coordenador,
        )
        res = client_coordenador.get("/api/v1/relatorios/escala-mes?ano=2026&mes=7&formato=pdf")
        assert res.status_code == status.HTTP_200_OK
        assert res["Content-Type"] == "application/pdf"
        assert res.content[:4] == b"%PDF"

    def test_padre_nao_exporta_pdf(self, client_padre):
        res = client_padre.get("/api/v1/relatorios/escala-mes?ano=2026&mes=7&formato=pdf")
        assert res.status_code == status.HTTP_403_FORBIDDEN
