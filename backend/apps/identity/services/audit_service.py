from apps.identity.models import AuditAcao, AuditLog


class AuditService:
    @staticmethod
    def registrar(
        acao: str,
        *,
        usuario=None,
        ip: str | None = None,
        detalhes: dict | None = None,
    ) -> AuditLog:
        return AuditLog.objects.create(
            acao=acao,
            usuario=usuario,
            ip=ip,
            detalhes=detalhes or {},
        )

    @staticmethod
    def login_sucesso(usuario, ip: str | None = None) -> AuditLog:
        return AuditService.registrar(
            AuditAcao.LOGIN_SUCESSO,
            usuario=usuario,
            ip=ip,
            detalhes={"tipo_perfil": usuario.tipo_perfil},
        )

    @staticmethod
    def login_falha(ip: str | None = None, detalhes: dict | None = None) -> AuditLog:
        return AuditService.registrar(AuditAcao.LOGIN_FALHA, ip=ip, detalhes=detalhes or {})

    @staticmethod
    def recuperar_senha_sucesso(usuario, ip: str | None = None) -> AuditLog:
        return AuditService.registrar(
            AuditAcao.RECUPERAR_SENHA,
            usuario=usuario,
            ip=ip,
        )

    @staticmethod
    def recuperar_senha_falha(ip: str | None = None, detalhes: dict | None = None) -> AuditLog:
        return AuditService.registrar(
            AuditAcao.RECUPERAR_SENHA_FALHA,
            ip=ip,
            detalhes=detalhes or {},
        )
