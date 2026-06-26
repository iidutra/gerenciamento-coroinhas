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


@pytest.mark.django_db
def test_whatsapp_usa_telefone_mae_primeiro(monkeypatch):
    """Cadastro simplificado (sem responsável): mãe primeiro, pai como fallback."""
    from datetime import date

    from apps.membership.models import Coroinha

    coroinha = Coroinha.objects.create(
        nome="Maria Simples",
        data_nascimento=date(2014, 5, 1),
        telefone_mae="69911112222",
        telefone_pai="69933334444",
    )

    enviados = []
    monkeypatch.setattr(
        "apps.communication.services.comunicacao_service.EnvioService.enviar_whatsapp",
        lambda tel, texto: enviados.append(tel) or True,
    )

    ok = ComunicacaoService._enviar_whatsapp_coroinha(coroinha, "Olá")
    assert ok is True
    assert enviados == ["69911112222"]


@pytest.mark.django_db
def test_whatsapp_fallback_telefone_pai(monkeypatch):
    from datetime import date

    from apps.membership.models import Coroinha

    coroinha = Coroinha.objects.create(
        nome="Pedro Só Pai",
        data_nascimento=date(2014, 5, 1),
        telefone_pai="69955556666",
    )

    enviados = []
    monkeypatch.setattr(
        "apps.communication.services.comunicacao_service.EnvioService.enviar_whatsapp",
        lambda tel, texto: enviados.append(tel) or True,
    )

    ComunicacaoService._enviar_whatsapp_coroinha(coroinha, "Olá")
    assert enviados == ["69955556666"]
