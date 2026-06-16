import structlog
from django.conf import settings
from django.core.mail import send_mail

from apps.communication.services.whatsapp_service import WhatsAppService

logger = structlog.get_logger(__name__)


class EnvioService:
    @staticmethod
    def email_configurado() -> bool:
        return bool(settings.EMAIL_HOST)

    @staticmethod
    def whatsapp_configurado() -> bool:
        return WhatsAppService.configurado()

    @staticmethod
    def status_comunicacao() -> dict:
        return {
            "email_configurado": EnvioService.email_configurado(),
            **WhatsAppService.status(),
        }

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
        return WhatsAppService.enviar(telefone, corpo)
