import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestUsuarioStaff:
    def test_coordenador_lista_usuarios(self, client_coordenador, secretario):
        res = client_coordenador.get("/api/v1/usuarios-staff/")
        assert res.status_code == status.HTTP_200_OK
        emails = [u["email"] for u in res.data]
        assert secretario.email in emails

    def test_secretario_nao_gerencia_usuarios(self, client_secretario):
        res = client_secretario.get("/api/v1/usuarios-staff/")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_coordenador_cria_padre(self, client_coordenador):
        res = client_coordenador.post(
            "/api/v1/usuarios-staff/",
            {
                "nome": "Pe. Novo",
                "email": "padre.novo@test.org",
                "tipo_perfil": "Padre",
                "senha": "senha123",
            },
            format="json",
        )
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data["tipo_perfil"] == "Padre"
