from unittest.mock import MagicMock, patch

import pytest

from apps.communication.services.whatsapp_service import WhatsAppService
from apps.communication.utils.telefone import normalizar_telefone_whatsapp


class TestNormalizarTelefone:
    def test_celular_com_mascara(self):
        assert normalizar_telefone_whatsapp("(69) 99999-8888") == "556999998888"

    def test_ja_com_ddi(self):
        assert normalizar_telefone_whatsapp("556999998888") == "556999998888"

    def test_vazio(self):
        assert normalizar_telefone_whatsapp("") == ""


@pytest.mark.django_db
class TestWhatsAppService:
    @pytest.mark.parametrize(
        "provider,env",
        [
            ("http", {"WHATSAPP_API_URL": "https://hook.test/send"}),
            (
                "meta",
                {
                    "WHATSAPP_PROVIDER": "meta",
                    "WHATSAPP_API_TOKEN": "token",
                    "WHATSAPP_PHONE_NUMBER_ID": "123",
                },
            ),
            (
                "evolution",
                {
                    "WHATSAPP_PROVIDER": "evolution",
                    "WHATSAPP_API_URL": "https://evo.test/message/sendText/inst",
                    "WHATSAPP_API_TOKEN": "key",
                },
            ),
            (
                "waha",
                {
                    "WHATSAPP_PROVIDER": "waha",
                    "WHATSAPP_API_URL": "https://waha.test",
                    "WHATSAPP_API_TOKEN": "secret",
                },
            ),
        ],
    )
    def test_configurado(self, settings, provider, env):
        for key, val in env.items():
            setattr(settings, key, val)
        settings.WHATSAPP_PROVIDER = provider
        assert WhatsAppService.configurado() is True

    def test_simulado_sem_config(self, settings):
        settings.WHATSAPP_API_URL = ""
        settings.WHATSAPP_PROVIDER = "http"
        assert WhatsAppService.enviar("69999998888", "Olá") is False

    @patch("apps.communication.services.whatsapp_service.urllib.request.urlopen")
    def test_envio_http(self, mock_urlopen, settings):
        settings.WHATSAPP_API_URL = "https://hook.test/send"
        settings.WHATSAPP_PROVIDER = "http"
        resp = MagicMock()
        resp.status = 200
        resp.__enter__ = MagicMock(return_value=resp)
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp

        assert WhatsAppService.enviar("69999998888", "Teste") is True

    @patch("apps.communication.services.whatsapp_service.urllib.request.urlopen")
    def test_envio_waha(self, mock_urlopen, settings):
        settings.WHATSAPP_PROVIDER = "waha"
        settings.WHATSAPP_API_URL = "https://waha.test"
        settings.WHATSAPP_API_TOKEN = "secret"
        settings.WHATSAPP_WAHA_SESSION = "default"
        resp = MagicMock()
        resp.status = 200
        resp.__enter__ = MagicMock(return_value=resp)
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp

        assert WhatsAppService.enviar("69999998888", "Olá WAHA") is True
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://waha.test/api/sendText"
        assert req.get_header("X-api-key") == "secret"
