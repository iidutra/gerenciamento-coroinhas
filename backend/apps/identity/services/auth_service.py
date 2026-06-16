import hashlib

import structlog
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q

from apps.identity.models import TipoPerfil, Usuario
from apps.identity.services.audit_service import AuditService
from apps.identity.utils.cpf import normalizar_cpf, validar_cpf

logger = structlog.get_logger(__name__)

RECUPERACAO_ERRO = "CPF ou data de nascimento incorretos."
LOGIN_ERRO = "Credenciais inválidas."


class AuthService:
    @staticmethod
    def _rate_limit_key(prefix: str, cpf: str, ip: str | None) -> str:
        cpf_hash = hashlib.sha256(cpf.encode()).hexdigest()[:16]
        ip_part = ip or "unknown"
        return f"auth:{prefix}:{cpf_hash}:{ip_part}"

    @classmethod
    def _check_rate_limit(cls, prefix: str, cpf: str, ip: str | None) -> None:
        key = cls._rate_limit_key(prefix, cpf, ip)
        attempts = cache.get(key, 0)
        if attempts >= settings.AUTH_RATE_LIMIT_ATTEMPTS:
            logger.warning("auth_rate_limit_exceeded", prefix=prefix)
            raise ValueError("Muitas tentativas. Tente novamente mais tarde.")

    @classmethod
    def _register_failed_attempt(cls, prefix: str, cpf: str, ip: str | None) -> None:
        key = cls._rate_limit_key(prefix, cpf, ip)
        attempts = cache.get(key, 0)
        cache.set(key, attempts + 1, settings.AUTH_RATE_LIMIT_WINDOW)

    @classmethod
    def _clear_rate_limit(cls, prefix: str, cpf: str, ip: str | None) -> None:
        cache.delete(cls._rate_limit_key(prefix, cpf, ip))

    @classmethod
    def login(cls, identificador: str, senha: str, ip: str | None = None) -> Usuario:
        identificador = identificador.strip()
        if "@" in identificador:
            return cls.login_staff(identificador, senha, ip)
        return cls.login_familia(identificador, senha, ip)

    @classmethod
    def login_familia(cls, cpf: str, senha: str, ip: str | None = None) -> Usuario:
        cpf = normalizar_cpf(cpf)
        if not validar_cpf(cpf):
            raise ValueError(LOGIN_ERRO)

        cls._check_rate_limit("login", cpf, ip)

        try:
            usuario = Usuario.objects.get(cpf=cpf, is_active=True)
        except Usuario.DoesNotExist:
            cls._register_failed_attempt("login", cpf, ip)
            raise ValueError(LOGIN_ERRO) from None

        if usuario.tipo_perfil not in (TipoPerfil.PAI, TipoPerfil.COROINHA):
            cls._register_failed_attempt("login", cpf, ip)
            raise ValueError(LOGIN_ERRO)

        if not usuario.check_password(senha):
            cls._register_failed_attempt("login", cpf, ip)
            raise ValueError(LOGIN_ERRO)

        cls._clear_rate_limit("login", cpf, ip)
        logger.info("login_sucesso", usuario_id=usuario.id, tipo_perfil=usuario.tipo_perfil)
        AuditService.login_sucesso(usuario, ip=ip)
        return usuario

    @classmethod
    def login_staff(cls, email: str, senha: str, ip: str | None = None) -> Usuario:
        email = email.strip().lower()
        cls._check_rate_limit("login", email, ip)

        try:
            usuario = Usuario.objects.get(
                Q(email__iexact=email),
                is_active=True,
                tipo_perfil__in=(TipoPerfil.COORDENADOR, TipoPerfil.SECRETARIO, TipoPerfil.PADRE),
            )
        except Usuario.DoesNotExist:
            cls._register_failed_attempt("login", email, ip)
            raise ValueError(LOGIN_ERRO) from None

        if not usuario.check_password(senha):
            cls._register_failed_attempt("login", email, ip)
            raise ValueError(LOGIN_ERRO)

        cls._clear_rate_limit("login", email, ip)
        logger.info("login_sucesso", usuario_id=usuario.id, tipo_perfil=usuario.tipo_perfil)
        AuditService.login_sucesso(usuario, ip=ip)
        return usuario

    @staticmethod
    def _validar_data_nascimento_recuperacao(usuario: Usuario, data_nascimento) -> bool:
        if usuario.tipo_perfil == TipoPerfil.COROINHA:
            return usuario.coroinha and usuario.coroinha.data_nascimento == data_nascimento
        if usuario.tipo_perfil == TipoPerfil.PAI:
            return (
                usuario.responsavel
                and usuario.responsavel.coroinhas.filter(data_nascimento=data_nascimento).exists()
            )
        return False

    @classmethod
    def recuperar_senha(
        cls,
        cpf: str,
        data_nascimento,
        nova_senha: str,
        ip: str | None = None,
    ) -> None:
        cpf = normalizar_cpf(cpf)
        if not validar_cpf(cpf):
            logger.info("recuperar_senha_falha", motivo="cpf_invalido")
            AuditService.recuperar_senha_falha(ip=ip, detalhes={"motivo": "cpf_invalido"})
            raise ValueError(RECUPERACAO_ERRO)

        cls._check_rate_limit("recuperar", cpf, ip)

        try:
            usuario = Usuario.objects.get(
                cpf=cpf,
                is_active=True,
                tipo_perfil__in=(TipoPerfil.PAI, TipoPerfil.COROINHA),
            )
        except Usuario.DoesNotExist:
            cls._register_failed_attempt("recuperar", cpf, ip)
            logger.info("recuperar_senha_falha", motivo="usuario_nao_encontrado")
            AuditService.recuperar_senha_falha(ip=ip, detalhes={"motivo": "usuario_nao_encontrado"})
            raise ValueError(RECUPERACAO_ERRO) from None

        if not cls._validar_data_nascimento_recuperacao(usuario, data_nascimento):
            cls._register_failed_attempt("recuperar", cpf, ip)
            logger.info("recuperar_senha_falha", motivo="data_nascimento", usuario_id=usuario.id)
            AuditService.recuperar_senha_falha(ip=ip, detalhes={"motivo": "data_nascimento"})
            raise ValueError(RECUPERACAO_ERRO)

        cls._clear_rate_limit("recuperar", cpf, ip)

        usuario.set_password(nova_senha)
        usuario.must_change_password = False
        usuario.save(update_fields=["password", "must_change_password"])
        logger.info("recuperar_senha_sucesso", usuario_id=usuario.id)
        AuditService.recuperar_senha_sucesso(usuario, ip=ip)

    @classmethod
    def trocar_senha(cls, usuario: Usuario, senha_atual: str, nova_senha: str) -> None:
        if not usuario.check_password(senha_atual):
            raise ValueError("Senha atual incorreta.")
        usuario.set_password(nova_senha)
        usuario.must_change_password = False
        usuario.save(update_fields=["password", "must_change_password"])
        logger.info("trocar_senha_sucesso", usuario_id=usuario.id)
