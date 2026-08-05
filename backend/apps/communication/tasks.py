from celery import shared_task


@shared_task(name="communication.processar_mensagem")
def processar_mensagem(mensagem_id: int) -> None:
    from apps.communication.services.comunicacao_service import ComunicacaoService

    ComunicacaoService.processar_envio(mensagem_id)


@shared_task(name="communication.notificar_aniversariantes")
def notificar_aniversariantes() -> dict:
    """Lembrete diário dos aniversariantes (agendado pelo Celery beat)."""
    from datetime import date

    from django.core.cache import cache

    from apps.communication.services.aniversario_service import AniversarioService

    chave = f"aniversario_notificado:{date.today().isoformat()}"
    # Idempotência: se o beat disparar duas vezes no mesmo dia (ex.: restart do
    # worker no horário agendado), só a primeira execução envia.
    if not cache.add(chave, 1, timeout=60 * 60 * 20):
        return {"enviado": False, "motivo": "ja_notificado_hoje", "aniversariantes": 0}

    resultado = AniversarioService.notificar()
    # Falha de envio ou destino ausente: libera a trava para permitir nova tentativa.
    if not resultado.get("enviado") and resultado.get("motivo") in {"falha_envio", "sem_destino"}:
        cache.delete(chave)
    return resultado
