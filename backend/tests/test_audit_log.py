import pytest
from django.test import override_settings

from apps.identity.models import AuditAcao, AuditLog


@pytest.mark.django_db
def test_audit_login_sucesso(api_client, coordenador):
    assert AuditLog.objects.count() == 0
    response = api_client.post(
        "/api/v1/auth/login",
        {"identificador": "coord@test.org", "senha": "teste123"},
        format="json",
    )
    assert response.status_code == 200
    assert AuditLog.objects.filter(acao=AuditAcao.LOGIN_SUCESSO).count() == 1


@pytest.mark.django_db
def test_audit_login_falha(api_client):
    api_client.post(
        "/api/v1/auth/login",
        {"identificador": "coord@test.org", "senha": "errada"},
        format="json",
    )
    assert AuditLog.objects.filter(acao=AuditAcao.LOGIN_FALHA).count() == 1


@pytest.mark.django_db
@override_settings(INSCRICOES_ABERTAS=True)
def test_audit_inscricao_publica(api_client):
    payload = {
        "coroinha": {
            "nome": "Maria Nova",
            "data_nascimento": "2013-05-10",
            "turma": "Iniciante",
        },
        "responsavel": {
            "cpf": "390.533.447-05",
            "nome_mae": "Mãe Maria",
            "telefone_principal": "11999999999",
        },
    }
    response = api_client.post(
        "/api/v1/inscricoes/publica",
        payload,
        format="json",
        HTTP_X_FORWARDED_FOR="10.0.0.99",
    )
    assert response.status_code == 201
    assert AuditLog.objects.filter(acao=AuditAcao.INSCRICAO_CRIADA).count() == 1
