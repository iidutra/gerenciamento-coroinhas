from django.core import mail

import pytest

from apps.communication.models import CanalMensagem
from apps.communication.services.comunicacao_service import ComunicacaoService
from apps.membership.models import Responsavel


@pytest.mark.django_db
def test_envio_email_real(coordenador, coroinha):
    responsavel = coroinha.responsaveis.first()
    Responsavel.objects.filter(pk=responsavel.pk).update(email="pai@test.org")

    msg = ComunicacaoService.enviar(
        canal=CanalMensagem.EMAIL,
        corpo="Olá {nome}, escala: {escala}",
        coroinha_ids=[coroinha.id],
        usuario=coordenador,
    )

    msg.refresh_from_db()
    assert msg.simulacao is False
    assert len(mail.outbox) == 1
    assert "João Teste" in mail.outbox[0].body


@pytest.mark.django_db
def test_envio_whatsapp_simulado(coordenador, coroinha):
    msg = ComunicacaoService.enviar(
        canal=CanalMensagem.WHATSAPP,
        corpo="Olá {nome}",
        coroinha_ids=[coroinha.id],
        usuario=coordenador,
    )

    msg.refresh_from_db()
    assert msg.simulacao is True


@pytest.mark.django_db
def test_preview_mensagem(coroinha):
    texto = ComunicacaoService.preview("Olá {nome}, idade {idade}", coroinha.id)
    assert "João Teste" in texto
    assert str(coroinha.idade) in texto
