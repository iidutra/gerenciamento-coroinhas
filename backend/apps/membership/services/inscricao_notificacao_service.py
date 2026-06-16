from apps.communication.services.envio_service import EnvioService


class InscricaoNotificacaoService:
    @staticmethod
    def _contatos(inscricao) -> dict:
        resp = inscricao.dados.get("responsavel", {})
        coroinha = inscricao.dados.get("coroinha", {})
        return {
            "email": (resp.get("email") or "").strip(),
            "whatsapp": (resp.get("whatsapp") or resp.get("telefone_principal") or "").strip(),
            "telefone_coroinha": (coroinha.get("telefone") or "").strip(),
            "nome_coroinha": coroinha.get("nome") or "coroinha",
        }

    @classmethod
    def _enviar(cls, *, email: str, whatsapp: str, telefone_extra: str, assunto: str, texto: str) -> bool:
        enviado = False
        if email:
            enviado = EnvioService.enviar_email(email, assunto, texto) or enviado
        for tel in (whatsapp, telefone_extra):
            if tel:
                enviado = EnvioService.enviar_whatsapp(tel, texto) or enviado
        return enviado

    @classmethod
    def notificar_aprovacao(cls, inscricao, coroinha, mensagem: str = "") -> bool:
        contatos = cls._contatos(inscricao)
        nome = coroinha.nome
        texto = (
            f"Olá! A inscrição de {nome} na Pastoral dos Coroinhas foi aprovada.\n\n"
            "Acesse o portal com o CPF cadastrado. A senha inicial são os 6 primeiros "
            "dígitos do CPF — troque no primeiro acesso."
        )
        if mensagem.strip():
            texto = f"{texto}\n\n{mensagem.strip()}"
        assunto = f"Inscrição aprovada — {nome}"
        return cls._enviar(
            email=contatos["email"],
            whatsapp=contatos["whatsapp"],
            telefone_extra=contatos["telefone_coroinha"],
            assunto=assunto,
            texto=texto,
        )

    @classmethod
    def notificar_rejeicao(cls, inscricao, mensagem: str = "") -> bool:
        contatos = cls._contatos(inscricao)
        nome = contatos["nome_coroinha"]
        texto = (
            f"Olá! Informamos que a inscrição de {nome} na Pastoral dos Coroinhas "
            "não foi aprovada neste momento."
        )
        if mensagem.strip():
            texto = f"{texto}\n\n{mensagem.strip()}"
        assunto = f"Inscrição — {nome}"
        return cls._enviar(
            email=contatos["email"],
            whatsapp=contatos["whatsapp"],
            telefone_extra=contatos["telefone_coroinha"],
            assunto=assunto,
            texto=texto,
        )
