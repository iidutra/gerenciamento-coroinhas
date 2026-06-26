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
                "nome_pai": "Pai Lucas",
                "telefone_pai": "69999990000",
                "nome_mae": "Mãe Lucas",
                "telefone_mae": "69999991111",
                "endereco": "Rua A, 100",
                "faz_catequese": True,
                "etapa_catequese": "Crisma",
                "faz_iam": True,
            },
            format="json",
        )
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data["nome"] == "Lucas Manual"
        assert res.data["faz_catequese"] is True
        assert res.data["etapa_catequese"] == "Crisma"
        assert res.data["faz_iam"] is True
        assert res.data["nome_mae"] == "Mãe Lucas"

    def test_coordenador_edita_e_exclui_coroinha(self, client_coordenador, coroinha):
        res = client_coordenador.patch(
            f"/api/v1/coroinhas/{coroinha.id}/",
            {"status": "Inativo", "faz_iam": True, "nome_pai": "Novo Pai"},
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        assert res.data["status"] == "Inativo"
        assert res.data["faz_iam"] is True
        assert res.data["nome_pai"] == "Novo Pai"

        res = client_coordenador.delete(f"/api/v1/coroinhas/{coroinha.id}/")
        assert res.status_code == status.HTTP_204_NO_CONTENT


class TestInscricaoSemCpf:
    def _abrir_inscricoes(self):
        from apps.membership.models import ConfiguracaoParoquial

        ConfiguracaoParoquial.get()
        ConfiguracaoParoquial.objects.filter(pk=1).update(inscricoes_abertas=True)

    def test_inscricao_publica_sem_cpf(self, api_client, client_coordenador):
        self._abrir_inscricoes()
        payload = {
            "coroinha": {
                "nome": "Ana Sem CPF",
                "data_nascimento": "2014-02-10",
                "endereco": "Rua B, 200",
                "faz_catequese": True,
                "etapa_catequese": "PrimeiraEucaristia",
                "faz_iam": False,
            },
            "responsavel": {
                "nome_mae": "Mãe Ana",
                "telefone_mae": "69988887777",
                "nome_pai": "Pai Ana",
            },
        }
        criada = api_client.post("/api/v1/inscricoes/publica", payload, format="json")
        assert criada.status_code == status.HTTP_201_CREATED

        res = client_coordenador.post(
            f"/api/v1/inscricoes/{criada.data['id']}/aprovar/",
            {"notificar": False},
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK

        from apps.membership.models import Coroinha

        coro = Coroinha.objects.get(id=res.data["coroinha_id"])
        assert coro.nome == "Ana Sem CPF"
        assert coro.nome_mae == "Mãe Ana"
        assert coro.telefone_mae == "69988887777"
        assert coro.faz_catequese is True
        assert coro.etapa_catequese == "PrimeiraEucaristia"
        assert coro.responsaveis.count() == 0
