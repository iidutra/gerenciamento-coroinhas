import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db

URL = "/api/v1/auth/login/coroinha"


def test_login_por_nome_e_data(api_client, coroinha):
    res = api_client.post(
        URL, {"nome": "João", "data_nascimento": "2012-03-15"}, format="json"
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.data["usuario"]["tipo_perfil"] == "Coroinha"
    assert res.data["usuario"]["coroinha_id"] == coroinha.id
    assert res.data["access"]


def test_login_ignora_acento(api_client, coroinha):
    res = api_client.post(
        URL, {"nome": "joao", "data_nascimento": "2012-03-15"}, format="json"
    )
    assert res.status_code == status.HTTP_200_OK


def test_login_reaproveita_usuario(api_client, coroinha):
    from apps.identity.models import Usuario

    api_client.post(URL, {"nome": "João", "data_nascimento": "2012-03-15"}, format="json")
    api_client.post(URL, {"nome": "João", "data_nascimento": "2012-03-15"}, format="json")
    assert Usuario.objects.filter(coroinha=coroinha).count() == 1


def test_login_data_incorreta_falha(api_client, coroinha):
    res = api_client.post(
        URL, {"nome": "João", "data_nascimento": "2010-01-01"}, format="json"
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
