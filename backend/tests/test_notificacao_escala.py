import pytest
from django.core import mail

from apps.communication.models import CanalMensagem, Mensagem
from apps.scheduling.models import FuncaoEscala
from apps.scheduling.services.escala_service import EscalaService
from apps.scheduling.services.notificacao_escala_service import NotificacaoEscalaService

pytestmark = pytest.mark.django_db


class TestNotificacaoEscala:
    def test_notificar_escala_cria_mensagem(self, coordenador, missa_domingo, coroinha, responsavel):
        from apps.membership.models import Responsavel

        Responsavel.objects.filter(pk=responsavel.pk).update(email="pai@test.org")
        escala = EscalaService.montar(
            data=__import__("datetime").date(2026, 7, 1),
            missa_id=missa_domingo.id,
            modo="SorteioAutomatico",
            quantidade=1,
            usuario=coordenador,
        )
        EscalaService.atribuir_funcoes(escala, {FuncaoEscala.CRUZ.value: coroinha.id})

        mensagem = NotificacaoEscalaService.notificar(escala, coordenador, canal=CanalMensagem.EMAIL)
        assert mensagem is not None
        assert mensagem.escala_id == escala.id
        assert mensagem.destinatarios.filter(pk=coroinha.id).exists()

        mensagem.refresh_from_db()
        assert mensagem.simulacao is False
        assert len(mail.outbox) == 1
        assert "João Teste" in mail.outbox[0].body
        assert "Cruz" in mail.outbox[0].body

    def test_montar_com_notificacao_automatica(self, coordenador, missa_domingo, coroinha):
        escala, mensagem = EscalaService.montar_com_notificacao(
            data=__import__("datetime").date(2026, 7, 2),
            missa_id=missa_domingo.id,
            modo="SorteioAutomatico",
            quantidade=1,
            usuario=coordenador,
            notificar=True,
        )
        assert escala.itens.count() == 1
        assert isinstance(mensagem, Mensagem)

    def test_montar_sem_notificacao(self, coordenador, missa_domingo, coroinha):
        escala, mensagem = EscalaService.montar_com_notificacao(
            data=__import__("datetime").date(2026, 7, 3),
            missa_id=missa_domingo.id,
            modo="SorteioAutomatico",
            quantidade=1,
            usuario=coordenador,
            notificar=False,
        )
        assert mensagem is None
        assert escala.mensagens_notificacao.count() == 0

    def test_notificar_via_api(self, client_coordenador, coordenador, missa_domingo, coroinha):
        from datetime import date
        from rest_framework import status

        escala = EscalaService.montar(
            data=date(2026, 7, 4),
            missa_id=missa_domingo.id,
            modo="SorteioAutomatico",
            quantidade=1,
            usuario=coordenador,
        )
        res = client_coordenador.post(f"/api/v1/escalas/{escala.id}/notificar/", {}, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data["canal"] in (CanalMensagem.WHATSAPP, CanalMensagem.EMAIL)

    def test_montar_api_com_notificar(self, client_coordenador, missa_domingo, coroinha):
        from rest_framework import status

        res = client_coordenador.post(
            "/api/v1/escalas/montar/",
            {
                "data": "2026-07-05",
                "missa_id": missa_domingo.id,
                "modo": "SorteioAutomatico",
                "quantidade": 1,
                "notificar": True,
            },
            format="json",
        )
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data.get("notificacao") is not None
        assert res.data["notificacao_enviada"] is True
