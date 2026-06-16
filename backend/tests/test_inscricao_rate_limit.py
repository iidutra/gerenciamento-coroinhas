import pytest
from django.test import override_settings
from rest_framework import status

pytestmark = pytest.mark.django_db

PAYLOAD = {
    "coroinha": {
        "nome": "Maria Inscrição",
        "data_nascimento": "2014-05-10",
    },
    "responsavel": {
        "cpf": "390.533.447-05",
        "nome_mae": "Mãe Maria",
    },
}


class TestInscricaoRateLimit:
    @override_settings(INSCRICOES_ABERTAS=True, INSCRICAO_RATE_LIMIT_ATTEMPTS=2, INSCRICAO_RATE_LIMIT_WINDOW=60)
    def test_bloqueia_apos_limite(self, api_client):
        headers = {"HTTP_X_FORWARDED_FOR": "10.0.0.42"}
        for _ in range(2):
            res = api_client.post("/api/v1/inscricoes/publica", PAYLOAD, format="json", **headers)
            assert res.status_code == status.HTTP_201_CREATED

        res = api_client.post("/api/v1/inscricoes/publica", PAYLOAD, format="json", **headers)
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "Muitas inscrições" in res.data["detail"]
