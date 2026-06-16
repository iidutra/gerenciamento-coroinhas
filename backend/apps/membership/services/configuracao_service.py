from django.conf import settings

from apps.membership.models import ConfiguracaoParoquial


class ConfiguracaoService:
    @staticmethod
    def inscricoes_abertas() -> bool:
        if getattr(settings, "INSCRICOES_ABERTAS", False):
            return True
        return ConfiguracaoParoquial.get().inscricoes_abertas

    @staticmethod
    def definir_inscricoes_abertas(aberto: bool, usuario) -> ConfiguracaoParoquial:
        config = ConfiguracaoParoquial.get()
        config.inscricoes_abertas = aberto
        config.inscricoes_atualizado_por = usuario
        config.save(update_fields=["inscricoes_abertas", "inscricoes_atualizado_por", "inscricoes_atualizado_em"])
        return config

    @staticmethod
    def status_inscricoes() -> dict:
        config = ConfiguracaoParoquial.get()
        aberto = ConfiguracaoService.inscricoes_abertas()
        return {
            "inscricoes_abertas": aberto,
            "controlado_por_env": bool(getattr(settings, "INSCRICOES_ABERTAS", False)),
            "atualizado_em": config.inscricoes_atualizado_em,
            "atualizado_por_nome": (
                config.inscricoes_atualizado_por.nome if config.inscricoes_atualizado_por else None
            ),
        }
