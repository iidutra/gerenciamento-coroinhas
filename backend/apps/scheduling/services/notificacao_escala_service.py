from django.conf import settings

from apps.communication.models import CanalMensagem
from apps.communication.services.comunicacao_service import ComunicacaoService
from apps.scheduling.models import Escala


class NotificacaoEscalaService:
    @staticmethod
    def corpo_padrao() -> str:
        return getattr(
            settings,
            "NOTIFICACAO_ESCALA_CORPO",
            "Olá {nome}, você está escalado para servir em {data} — {missa} ({horario}). Função: {funcao}.",
        )

    @staticmethod
    def canal_padrao() -> str:
        return getattr(settings, "NOTIFICACAO_ESCALA_CANAL", CanalMensagem.WHATSAPP)

    @classmethod
    def notificar(cls, escala: Escala, usuario, *, canal: str | None = None):
        from apps.communication.models import Mensagem

        escala = Escala.objects.prefetch_related("itens__coroinha", "missa").get(pk=escala.pk)
        coroinha_ids = list(escala.itens.values_list("coroinha_id", flat=True))
        if not coroinha_ids:
            return None

        return ComunicacaoService.enviar(
            canal=canal or cls.canal_padrao(),
            corpo=cls.corpo_padrao(),
            coroinha_ids=coroinha_ids,
            usuario=usuario,
            escala=escala,
        )

    @classmethod
    def notificar_se_habilitado(cls, escala: Escala, usuario, *, notificar: bool | None = None):
        if notificar is None:
            notificar = getattr(settings, "NOTIFICACAO_ESCALA_AUTOMATICA", True)
        if not notificar:
            return None
        return cls.notificar(escala, usuario)
