import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


def test_health_publico(api_client):
    res = api_client.get("/api/v1/health")
    assert res.status_code == status.HTTP_200_OK
    assert res.data["status"] == "ok"
