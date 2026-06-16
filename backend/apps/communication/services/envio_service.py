import structlog
from django.conf import settings
from django.core.mail import send_mail

logger = structlog.get_logger(__name__)


class EnvioService:
    @staticmethod
    def email_configurado() -> bool:
        return bool(settings.EMAIL_HOST)

    @staticmethod
    def whatsapp_configurado() -> bool:
        return bool(getattr(settings, "WHATSAPP_API_URL", ""))

    @classmethod
    def enviar_email(cls, destino: str, assunto: str, corpo: str) -> bool:
        if not destino:
            return False
        if not cls.email_configurado():
            logger.info("email_simulado", destino=destino[:3] + "***")
            return False
        send_mail(
            subject=assunto,
            message=corpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destino],
            fail_silently=False,
        )
        logger.info("email_enviado", destino=destino[:3] + "***")
        return True

    @classmethod
    def enviar_whatsapp(cls, telefone: str, corpo: str) -> bool:
        if not telefone:
            return False
        if not cls.whatsapp_configurado():
            logger.info("whatsapp_simulado", telefone=telefone[:4] + "***")
            return False

        import urllib.error
        import urllib.request
        import json

        payload = json.dumps({"to": telefone, "message": corpo}).encode()
        req = urllib.request.Request(
            settings.WHATSAPP_API_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                ok = 200 <= resp.status < 300
                if ok:
                    logger.info("whatsapp_enviado", telefone=telefone[:4] + "***")
                return ok
        except (urllib.error.URLError, TimeoutError) as exc:
            logger.warning("whatsapp_falha", erro=str(exc))
            return False
