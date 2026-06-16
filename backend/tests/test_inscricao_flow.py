import pytest
from django.test import override_settings
from rest_framework import status

pytestmark = pytest.mark.django_db

PAYLOAD = {
    "coroinha": {
        "nome": "Pedro Inscrição",
        "data_nascimento": "2015-08-20",
    },
    "responsavel": {
        "cpf": "390.533.447-05",
        "nome_mae": "Mãe Pedro",
        "whatsapp": "69999998888",
        "email": "mae@example.com",
    },
}


class TestInscricoesAbertas:
    @override_settings(INSCRICOES_ABERTAS=False)
    def test_bloqueia_inscricao_publica_fechada(self, api_client):
        res = api_client.post("/api/v1/inscricoes/publica", PAYLOAD, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "não estão abertas" in res.data["detail"]

    def test_abre_via_config_paroquial(self, api_client):
        from apps.membership.models import ConfiguracaoParoquial

        config = ConfiguracaoParoquial.get()
        config.inscricoes_abertas = True
        config.save(update_fields=["inscricoes_abertas"])

        res = api_client.get("/api/v1/config/publica")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["inscricoes_abertas"] is True

        res = api_client.post("/api/v1/inscricoes/publica", PAYLOAD, format="json")
        assert res.status_code == status.HTTP_201_CREATED

    @override_settings(INSCRICOES_ABERTAS=True)
    def test_config_publica_env_override(self, api_client):
        res = api_client.get("/api/v1/config/publica")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["inscricoes_abertas"] is True

    def test_coordenador_alterna_inscricoes(self, client_coordenador):
        res = client_coordenador.patch(
            "/api/v1/config/inscricoes",
            {"inscricoes_abertas": True},
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        assert res.data["inscricoes_abertas"] is True

        res = client_coordenador.get("/api/v1/config/inscricoes")
        assert res.data["inscricoes_abertas"] is True

        res = client_coordenador.patch(
            "/api/v1/config/inscricoes",
            {"inscricoes_abertas": False},
            format="json",
        )
        assert res.data["inscricoes_abertas"] is False


class TestInscricaoAprovacao:
    def test_aprovar_com_mensagem(self, client_coordenador):
        from apps.membership.models import ConfiguracaoParoquial
        from rest_framework.test import APIClient

        ConfiguracaoParoquial.get()
        ConfiguracaoParoquial.objects.filter(pk=1).update(inscricoes_abertas=True)

        pub = APIClient()
        criada = pub.post("/api/v1/inscricoes/publica", PAYLOAD, format="json")
        assert criada.status_code == status.HTTP_201_CREATED
        inscricao_id = criada.data["id"]

        res = client_coordenador.post(
            f"/api/v1/inscricoes/{inscricao_id}/aprovar/",
            {"mensagem": "Bem-vindo ao grupo!", "notificar": False},
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        assert "coroinha_id" in res.data

    def test_coordenador_cadastra_coroinha_direto(self, client_coordenador):
        res = client_coordenador.post(
            "/api/v1/coroinhas/",
            {
                "nome": "Lucas Manual",
                "data_nascimento": "2013-01-15",
                "turma": "Iniciante",
                "status": "EmFormacao",
                "batizado": True,
                "primeira_eucaristia": False,
                "crisma": False,
            },
            format="json",
        )
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data["nome"] == "Lucas Manual"
