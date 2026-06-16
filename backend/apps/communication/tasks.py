from celery import shared_task


@shared_task(name="communication.processar_mensagem")
def processar_mensagem(mensagem_id: int) -> None:
    from apps.communication.services.comunicacao_service import ComunicacaoService

    ComunicacaoService.processar_envio(mensagem_id)
