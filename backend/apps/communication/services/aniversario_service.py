from datetime import date

import structlog
from django.conf import settings

from apps.communication.services.whatsapp_service import WhatsAppService
from apps.membership.models import Coroinha, StatusCoroinha

logger = structlog.get_logger(__name__)


class AniversarioService:
    """Lembrete diário de aniversário dos coroinhas, enviado ao coordenador por WhatsApp."""

    STATUS_CONSIDERADOS = (StatusCoroinha.ATIVO, StatusCoroinha.EM_FORMACAO)

    @classmethod
    def aniversariantes(cls, referencia: date | None = None) -> list[Coroinha]:
        hoje = referencia or date.today()
        return list(
            Coroinha.objects.filter(
                data_nascimento__month=hoje.month,
                data_nascimento__day=hoje.day,
                status__in=cls.STATUS_CONSIDERADOS,
            ).order_by("nome")
        )

    @staticmethod
    def _telefone_contato(coroinha: Coroinha) -> str:
        for tel in (coroinha.telefone, coroinha.telefone_mae, coroinha.telefone_pai):
            if tel and tel.strip():
                return tel.strip()
        return ""

    @classmethod
    def montar_mensagem(cls, coroinhas: list[Coroinha], referencia: date | None = None) -> str:
        hoje = referencia or date.today()
        linhas = [f"🎂 Aniversariante(s) de hoje ({hoje.strftime('%d/%m')}):", ""]
        for c in coroinhas:
            linha = f"• {c.nome} — {c.idade} anos"
            tel = cls._telefone_contato(c)
            if tel:
                linha += f"\n  📱 {tel}"
            linhas.append(linha)
        linhas.append("")
        linhas.append("Não esqueça de mandar os parabéns! 🎉")
        return "\n".join(linhas)

    @classmethod
    def destino(cls) -> str:
        return (getattr(settings, "NOTIFICACAO_ANIVERSARIO_DESTINO", "") or "").strip()

    @classmethod
    def ativo(cls) -> bool:
        return getattr(settings, "NOTIFICACAO_ANIVERSARIO_ATIVO", True)

    @classmethod
    def notificar(cls, referencia: date | None = None, *, forcar: bool = False) -> dict:
        """Envia o lembrete se houver aniversariante. Retorna um resumo do resultado."""
        hoje = referencia or date.today()
        if not cls.ativo() and not forcar:
            return {"enviado": False, "motivo": "desativado", "aniversariantes": 0}

        destino = cls.destino()
        if not destino:
            logger.warning("aniversario_sem_destino")
            return {"enviado": False, "motivo": "sem_destino", "aniversariantes": 0}

        coroinhas = cls.aniversariantes(hoje)
        if not coroinhas:
            return {"enviado": False, "motivo": "nenhum_aniversariante", "aniversariantes": 0}

        enviado = WhatsAppService.enviar(destino, cls.montar_mensagem(coroinhas, hoje))
        logger.info("aniversario_notificado", aniversariantes=len(coroinhas), enviado=enviado)
        return {
            "enviado": enviado,
            "motivo": "ok" if enviado else "falha_envio",
            "aniversariantes": len(coroinhas),
            "nomes": [c.nome for c in coroinhas],
        }
