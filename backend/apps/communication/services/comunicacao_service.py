from django.utils import timezone

from apps.communication.models import CanalMensagem
from apps.communication.services.envio_service import EnvioService
from apps.scheduling.models import Escala, EscalaItem


class MensagemTemplate:
    @staticmethod
    def render(
        corpo: str,
        *,
        nome: str = "",
        escala: str = "",
        idade: str = "",
        funcao: str = "",
        data: str = "",
        missa: str = "",
        horario: str = "",
    ) -> str:
        return (
            corpo.replace("{nome}", nome)
            .replace("{escala}", escala)
            .replace("{idade}", idade)
            .replace("{funcao}", funcao)
            .replace("{data}", data)
            .replace("{missa}", missa)
            .replace("{horario}", horario)
        )


class ComunicacaoService:
    @staticmethod
    def _texto_escala(coroinha) -> str:
        proxima = (
            EscalaItem.objects.filter(coroinha=coroinha, escala__data__gte=timezone.now().date())
            .select_related("escala", "escala__missa")
            .order_by("escala__data")
            .first()
        )
        if proxima:
            return f"{proxima.escala.data:%d/%m/%Y} — {proxima.escala.missa.nome}"
        return ""

    @classmethod
    def enviar(
        cls,
        canal: str,
        corpo: str,
        coroinha_ids: list[int],
        usuario,
        *,
        escala: Escala | None = None,
    ) -> "Mensagem":
        from apps.communication.models import Mensagem
        from apps.communication.tasks import processar_mensagem
        from apps.membership.models import Coroinha

        coroinhas = Coroinha.objects.filter(id__in=coroinha_ids)
        if not coroinhas.exists():
            raise ValueError("Nenhum destinatário válido.")

        simulacao_inicial = canal == CanalMensagem.WHATSAPP and not EnvioService.whatsapp_configurado()
        simulacao_inicial = simulacao_inicial or (
            canal == CanalMensagem.EMAIL and not EnvioService.email_configurado()
        )

        mensagem = Mensagem.objects.create(
            canal=canal,
            corpo=corpo,
            enviada_por=usuario,
            simulacao=simulacao_inicial,
            escala=escala,
        )
        mensagem.destinatarios.set(coroinhas)
        processar_mensagem.delay(mensagem.id)
        return mensagem

    @classmethod
    def processar_envio(cls, mensagem_id: int) -> None:
        from apps.communication.models import Mensagem

        mensagem = Mensagem.objects.select_related("escala__missa").prefetch_related(
            "destinatarios__responsaveis",
            "escala__itens",
        ).get(pk=mensagem_id)

        envios_reais = 0
        for coroinha in mensagem.destinatarios.all():
            texto = cls._render_para_coroinha(mensagem.corpo, coroinha, mensagem.escala)
            if mensagem.canal == CanalMensagem.EMAIL:
                if cls._enviar_email_coroinha(coroinha, texto):
                    envios_reais += 1
            elif mensagem.canal == CanalMensagem.WHATSAPP:
                if cls._enviar_whatsapp_coroinha(coroinha, texto):
                    envios_reais += 1

        total = mensagem.destinatarios.count()
        mensagem.simulacao = envios_reais == 0 and total > 0
        mensagem.save(update_fields=["simulacao"])

        from apps.identity.models import AuditAcao
        from apps.identity.services.audit_service import AuditService

        AuditService.registrar(
            AuditAcao.MENSAGEM_ENVIADA,
            usuario=mensagem.enviada_por,
            detalhes={
                "mensagem_id": mensagem.id,
                "canal": mensagem.canal,
                "simulacao": mensagem.simulacao,
                "destinatarios": total,
                "envios_reais": envios_reais,
                "escala_id": mensagem.escala_id,
            },
        )

    @classmethod
    def _render_para_coroinha(cls, corpo: str, coroinha, escala: Escala | None = None) -> str:
        if escala:
            item = escala.itens.filter(coroinha=coroinha).first()
            funcao = item.get_funcao_display() if item and item.funcao else "A definir"
            data_fmt = escala.data.strftime("%d/%m/%Y")
            horario = escala.missa.horario.strftime("%H:%M")
            return MensagemTemplate.render(
                corpo,
                nome=coroinha.nome,
                escala=f"{data_fmt} — {escala.missa.nome}",
                idade=str(coroinha.idade),
                funcao=funcao,
                data=data_fmt,
                missa=escala.missa.nome,
                horario=horario,
            )
        return MensagemTemplate.render(
            corpo,
            nome=coroinha.nome,
            escala=cls._texto_escala(coroinha),
            idade=str(coroinha.idade),
        )

    @staticmethod
    def _enviar_email_coroinha(coroinha, texto: str) -> bool:
        assunto = f"Pastoral dos Coroinhas — {coroinha.nome}"
        enviado = False
        for resp in coroinha.responsaveis.all():
            if resp.email and EnvioService.enviar_email(resp.email, assunto, texto):
                enviado = True
        return enviado

    @staticmethod
    def _enviar_whatsapp_coroinha(coroinha, texto: str) -> bool:
        enviado = False
        enviados_para: set[str] = set()

        def _tenta(tel: str | None) -> None:
            nonlocal enviado
            numero = (tel or "").strip()
            if not numero or numero in enviados_para:
                return
            enviados_para.add(numero)
            if EnvioService.enviar_whatsapp(numero, texto):
                enviado = True

        # 1. Responsaveis vinculados (cadastro com CPF / login da familia)
        for resp in coroinha.responsaveis.all():
            _tenta(resp.whatsapp or resp.telefone)
        # 2. Cadastro simplificado: telefone da mae primeiro, pai como fallback
        _tenta(coroinha.telefone_mae or coroinha.telefone_pai)
        # 3. Telefone direto do coroinha (legado)
        _tenta(coroinha.telefone)
        return enviado

    @staticmethod
    def preview(corpo: str, coroinha_id: int) -> str:
        from apps.membership.models import Coroinha

        coroinha = Coroinha.objects.get(pk=coroinha_id)
        return ComunicacaoService._render_para_coroinha(corpo, coroinha)
