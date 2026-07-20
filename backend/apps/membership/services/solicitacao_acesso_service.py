import hashlib
import unicodedata

import structlog
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from apps.identity.models import AuditAcao, TipoPerfil, Usuario
from apps.identity.services.audit_service import AuditService
from apps.identity.utils.cpf import normalizar_cpf, validar_cpf
from apps.membership.models import (
    Coroinha,
    Responsavel,
    SolicitacaoAcesso,
    StatusSolicitacao,
)

logger = structlog.get_logger(__name__)

COROINHA_NAO_ENCONTRADO = (
    "Nenhum coroinha encontrado com esse nome e data de nascimento. "
    "Confira os dados ou fale com a coordenação."
)


def normalizar_nome(nome: str) -> str:
    """Minúsculas, sem acentos e sem espaços duplicados, para comparação tolerante."""
    texto = unicodedata.normalize("NFKD", nome or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.strip().lower().split())


class SolicitacaoAcessoService:
    RATE_LIMIT_ATTEMPTS = 15

    @staticmethod
    def _rate_limit_key(prefix: str, ip: str | None) -> str:
        ip_part = ip or "unknown"
        return f"acesso:{prefix}:{hashlib.sha256(ip_part.encode()).hexdigest()[:16]}"

    @classmethod
    def _check_rate_limit(cls, prefix: str, ip: str | None) -> None:
        key = cls._rate_limit_key(prefix, ip)
        attempts = cache.get(key, 0)
        if attempts >= cls.RATE_LIMIT_ATTEMPTS:
            logger.warning("acesso_rate_limit_exceeded", prefix=prefix)
            raise ValueError("Muitas tentativas. Tente novamente mais tarde.")
        cache.set(key, attempts + 1, settings.AUTH_RATE_LIMIT_WINDOW)

    @staticmethod
    def buscar_coroinhas(nome: str, data_nascimento) -> list[Coroinha]:
        alvo = normalizar_nome(nome)
        if not alvo:
            return []
        candidatos = Coroinha.objects.filter(data_nascimento=data_nascimento)
        return [c for c in candidatos if normalizar_nome(c.nome) == alvo]

    @classmethod
    def verificar(cls, nome: str, data_nascimento, ip: str | None = None) -> list[Coroinha]:
        cls._check_rate_limit("verificar", ip)
        coroinhas = cls.buscar_coroinhas(nome, data_nascimento)
        if not coroinhas:
            raise ValueError(COROINHA_NAO_ENCONTRADO)
        return coroinhas

    @classmethod
    @transaction.atomic
    def solicitar(
        cls,
        *,
        coroinha_id: int,
        nome_coroinha: str,
        data_nascimento,
        nome_responsavel: str,
        cpf: str,
        senha: str,
        whatsapp: str = "",
        ip: str | None = None,
    ) -> SolicitacaoAcesso:
        cls._check_rate_limit("solicitar", ip)

        cpf = normalizar_cpf(cpf)
        if not validar_cpf(cpf):
            raise ValueError("CPF inválido.")

        try:
            coroinha = Coroinha.objects.get(id=coroinha_id, data_nascimento=data_nascimento)
        except Coroinha.DoesNotExist:
            raise ValueError(COROINHA_NAO_ENCONTRADO) from None

        # Reconfirma o nome para impedir que só o id seja adulterado no passo 2.
        if normalizar_nome(nome_coroinha) != normalizar_nome(coroinha.nome):
            raise ValueError(COROINHA_NAO_ENCONTRADO)

        responsavel_existente = Responsavel.objects.filter(cpf=cpf).first()
        if responsavel_existente and responsavel_existente.coroinhas.filter(id=coroinha.id).exists():
            raise ValueError(
                "Você já tem acesso a este coroinha. Basta entrar com seu CPF e senha."
            )

        if SolicitacaoAcesso.objects.filter(
            cpf=cpf, coroinha=coroinha, status=StatusSolicitacao.PENDENTE
        ).exists():
            raise ValueError(
                "Já existe um pedido pendente para este coroinha. "
                "Aguarde a aprovação da coordenação."
            )

        solicitacao = SolicitacaoAcesso.objects.create(
            coroinha=coroinha,
            nome_responsavel=nome_responsavel.strip(),
            cpf=cpf,
            whatsapp=(whatsapp or "").strip(),
            senha_hash=make_password(senha),
        )
        AuditService.registrar(
            AuditAcao.SOLICITACAO_ACESSO_CRIADA,
            ip=ip,
            detalhes={"solicitacao_id": solicitacao.id, "coroinha_id": coroinha.id},
        )
        logger.info("solicitacao_acesso_criada", solicitacao_id=solicitacao.id)
        return solicitacao

    @staticmethod
    def listar(status: str | None = None):
        qs = SolicitacaoAcesso.objects.select_related("coroinha").all()
        if status:
            qs = qs.filter(status=status)
        return qs

    @staticmethod
    @transaction.atomic
    def aprovar(solicitacao: SolicitacaoAcesso, aprovador: Usuario) -> Usuario:
        if solicitacao.status != StatusSolicitacao.PENDENTE:
            raise ValueError("Solicitação já foi processada.")

        responsavel, _ = Responsavel.objects.get_or_create(
            cpf=solicitacao.cpf,
            defaults={
                "nome": solicitacao.nome_responsavel,
                "whatsapp": solicitacao.whatsapp,
            },
        )
        campos = []
        if not responsavel.nome:
            responsavel.nome = solicitacao.nome_responsavel
            campos.append("nome")
        if solicitacao.whatsapp and not responsavel.whatsapp:
            responsavel.whatsapp = solicitacao.whatsapp
            campos.append("whatsapp")
        if campos:
            responsavel.save(update_fields=campos)

        responsavel.coroinhas.add(solicitacao.coroinha)

        usuario = Usuario.objects.filter(cpf=solicitacao.cpf).first()
        if usuario is None:
            # Conta nova: a senha já veio hasheada do pedido.
            usuario = Usuario(
                cpf=solicitacao.cpf,
                nome=solicitacao.nome_responsavel,
                tipo_perfil=TipoPerfil.PAI,
                responsavel=responsavel,
            )
            usuario.password = solicitacao.senha_hash
            usuario.save()
        else:
            # Pai já cadastrado adicionando outro filho: apenas garante vínculo/ativação.
            atualizou = False
            if usuario.responsavel_id != responsavel.id:
                usuario.responsavel = responsavel
                atualizou = True
            if not usuario.is_active:
                usuario.is_active = True
                atualizou = True
            if atualizou:
                usuario.save()

        solicitacao.status = StatusSolicitacao.APROVADA
        solicitacao.processado_em = timezone.now()
        solicitacao.processado_por = aprovador
        solicitacao.save(update_fields=["status", "processado_em", "processado_por"])

        AuditService.registrar(
            AuditAcao.SOLICITACAO_ACESSO_APROVADA,
            usuario=aprovador,
            detalhes={
                "solicitacao_id": solicitacao.id,
                "coroinha_id": solicitacao.coroinha_id,
                "usuario_id": usuario.id,
            },
        )
        logger.info("solicitacao_acesso_aprovada", solicitacao_id=solicitacao.id)
        return usuario

    @staticmethod
    @transaction.atomic
    def rejeitar(solicitacao: SolicitacaoAcesso, aprovador: Usuario) -> None:
        if solicitacao.status != StatusSolicitacao.PENDENTE:
            raise ValueError("Solicitação já foi processada.")
        solicitacao.status = StatusSolicitacao.REJEITADA
        solicitacao.processado_em = timezone.now()
        solicitacao.processado_por = aprovador
        solicitacao.save(update_fields=["status", "processado_em", "processado_por"])
        AuditService.registrar(
            AuditAcao.SOLICITACAO_ACESSO_REJEITADA,
            usuario=aprovador,
            detalhes={"solicitacao_id": solicitacao.id},
        )
        logger.info("solicitacao_acesso_rejeitada", solicitacao_id=solicitacao.id)
