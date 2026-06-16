import json
import urllib.error
import urllib.request

import structlog
from django.conf import settings

from apps.communication.utils.telefone import normalizar_telefone_whatsapp

logger = structlog.get_logger(__name__)


class WhatsAppService:
    @staticmethod
    def provider() -> str:
        return getattr(settings, "WHATSAPP_PROVIDER", "http").lower()

    @classmethod
    def configurado(cls) -> bool:
        provider = cls.provider()
        if provider == "meta":
            return bool(
                getattr(settings, "WHATSAPP_API_TOKEN", "")
                and getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "")
            )
        if provider == "waha":
            return bool(
                getattr(settings, "WHATSAPP_API_URL", "")
                and getattr(settings, "WHATSAPP_API_TOKEN", "")
            )
        return bool(getattr(settings, "WHATSAPP_API_URL", ""))

    @classmethod
    def status(cls) -> dict:
        return {
            "whatsapp_configurado": cls.configurado(),
            "whatsapp_provider": cls.provider(),
            "whatsapp_simulacao": not cls.configurado(),
        }

    @classmethod
    def enviar(cls, telefone: str, corpo: str) -> bool:
        numero = normalizar_telefone_whatsapp(
            telefone,
            pais=getattr(settings, "WHATSAPP_DEFAULT_COUNTRY_CODE", "55"),
        )
        if not numero:
            return False
        if not cls.configurado():
            logger.info("whatsapp_simulado", telefone=numero[:6] + "***")
            return False

        provider = cls.provider()
        if provider == "meta":
            return cls._enviar_meta(numero, corpo)
        if provider == "evolution":
            return cls._enviar_evolution(numero, corpo)
        if provider == "waha":
            return cls._enviar_waha(numero, corpo)
        return cls._enviar_http(numero, corpo)

    @classmethod
    def _request_json(cls, url: str, payload: dict, headers: dict | None = None) -> bool:
        merged = {"Content-Type": "application/json", **(headers or {})}
        token = getattr(settings, "WHATSAPP_API_TOKEN", "")
        if token and "Authorization" not in merged and "X-Api-Key" not in merged:
            merged["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers=merged,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                ok = 200 <= resp.status < 300
                if ok:
                    logger.info(
                        "whatsapp_enviado",
                        url=url.split("?")[0],
                        destino=payload.get("to") or payload.get("chatId", "")[:8] + "***",
                    )
                return ok
        except (urllib.error.URLError, TimeoutError) as exc:
            logger.warning("whatsapp_falha", erro=str(exc))
            return False

    @classmethod
    def _enviar_http(cls, numero: str, corpo: str) -> bool:
        return cls._request_json(
            settings.WHATSAPP_API_URL,
            {"to": numero, "message": corpo},
        )

    @classmethod
    def _enviar_evolution(cls, numero: str, corpo: str) -> bool:
        headers = {}
        token = getattr(settings, "WHATSAPP_API_TOKEN", "")
        if token:
            headers["apikey"] = token
        return cls._request_json(
            settings.WHATSAPP_API_URL,
            {"number": numero, "text": corpo},
            headers=headers,
        )

    @classmethod
    def _waha_base_url(cls) -> str:
        return getattr(settings, "WHATSAPP_API_URL", "").rstrip("/")

    @classmethod
    def _waha_headers(cls) -> dict:
        token = getattr(settings, "WHATSAPP_API_TOKEN", "")
        headers = {"Accept": "application/json"}
        if token:
            headers["X-Api-Key"] = token
        return headers

    @classmethod
    def _waha_get(cls, path: str, query: dict | None = None) -> dict | None:
        from urllib.parse import urlencode

        base = cls._waha_base_url()
        qs = f"?{urlencode(query)}" if query else ""
        req = urllib.request.Request(
            f"{base}{path}{qs}",
            headers=cls._waha_headers(),
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                if not (200 <= resp.status < 300):
                    return None
                return json.loads(resp.read().decode())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            logger.warning("waha_get_falha", path=path, erro=str(exc))
            return None

    @classmethod
    def _resolver_chat_id_waha(cls, numero: str, session: str) -> str:
        """WhatsApp pode exigir @lid em vez de @c.us — consulta WAHA antes de enviar."""
        data = cls._waha_get(
            "/api/checkNumberStatus",
            {"session": session, "phone": numero},
        )
        if data and data.get("numberExists") and data.get("chatId"):
            return data["chatId"]
        return f"{numero}@c.us"

    @classmethod
    def _enviar_waha(cls, numero: str, corpo: str) -> bool:
        session = getattr(settings, "WHATSAPP_WAHA_SESSION", "default")
        chat_id = cls._resolver_chat_id_waha(numero, session)
        url = f"{cls._waha_base_url()}/api/sendText"
        token = getattr(settings, "WHATSAPP_API_TOKEN", "")
        headers = {"X-Api-Key": token} if token else {}
        return cls._request_json(
            url,
            {"session": session, "chatId": chat_id, "text": corpo},
            headers=headers,
        )

    @classmethod
    def _enviar_meta(cls, numero: str, corpo: str) -> bool:
        phone_id = settings.WHATSAPP_PHONE_NUMBER_ID
        version = getattr(settings, "WHATSAPP_GRAPH_VERSION", "v21.0")
        url = f"https://graph.facebook.com/{version}/{phone_id}/messages"
        return cls._request_json(
            url,
            {
                "messaging_product": "whatsapp",
                "to": numero,
                "type": "text",
                "text": {"body": corpo},
            },
        )
