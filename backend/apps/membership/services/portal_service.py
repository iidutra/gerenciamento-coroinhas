import unicodedata

from django.utils import timezone

from apps.attendance.models import Presenca, StatusPresenca
from apps.communication.utils.telefone import normalizar_telefone_whatsapp
from apps.identity.models import AuditAcao, TipoPerfil, Usuario
from apps.identity.services.audit_service import AuditService
from apps.scheduling.models import Escala, EscalaItem
from apps.training.models import Formacao, FormacaoConclusao


from apps.membership.utils.media import build_foto_url


def _chave_nome(nome: str | None) -> str:
    """Normaliza um nome para comparação (sem acento, minúsculo, sem espaços extras)."""
    if not nome:
        return ""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", nome) if unicodedata.category(c) != "Mn"
    )
    return " ".join(sem_acento.lower().split())


def _chave_telefone(telefone: str | None) -> str:
    return normalizar_telefone_whatsapp(telefone or "")


def _ids_irmaos_por_nome_e_telefone(responsavel, ids_conhecidos: set[int]) -> set[int]:
    """Fallback para coroinhas cadastrados direto pela equipe pastoral (sem passar
    pela inscrição on-line), que por isso nunca ficam vinculados a um Responsavel
    via CPF. Nome sozinho não é identificador forte o suficiente para autorizar
    acesso aos dados de uma criança (dois "José Silva" podem ser pessoas
    diferentes), então só consideramos irmão quando NOME e TELEFONE do pai/mãe
    batem com o cadastro do responsável logado.
    """
    from apps.membership.models import Coroinha

    nomes = {
        _chave_nome(n) for n in (responsavel.nome_pai, responsavel.nome_mae, responsavel.nome)
    }
    nomes.discard("")
    telefones = {_chave_telefone(t) for t in (responsavel.telefone, responsavel.whatsapp)}
    telefones.discard("")
    if not nomes or not telefones:
        return set()

    encontrados = set()
    candidatos = Coroinha.objects.exclude(id__in=ids_conhecidos).only(
        "id", "nome_pai", "nome_mae", "telefone_pai", "telefone_mae"
    )
    for c in candidatos:
        nome_bate = _chave_nome(c.nome_pai) in nomes or _chave_nome(c.nome_mae) in nomes
        telefone_bate = (
            _chave_telefone(c.telefone_pai) in telefones
            or _chave_telefone(c.telefone_mae) in telefones
        )
        if nome_bate and telefone_bate:
            encontrados.add(c.id)
    return encontrados


class PortalService:
    @staticmethod
    def pode_ver_coroinha(usuario: Usuario, coroinha_id: int) -> bool:
        if usuario.is_staff_pastoral:
            from apps.membership.models import Coroinha

            return Coroinha.objects.filter(id=coroinha_id).exists()
        return PortalService.coroinhas_acessiveis(usuario).filter(id=coroinha_id).exists()

    @staticmethod
    def coroinhas_acessiveis(usuario: Usuario):
        from apps.membership.models import Coroinha

        if usuario.is_staff_pastoral:
            return Coroinha.objects.all().order_by("nome")
        if usuario.tipo_perfil == TipoPerfil.COROINHA and usuario.coroinha_id:
            return Coroinha.objects.filter(id=usuario.coroinha_id)
        if usuario.tipo_perfil == TipoPerfil.PAI and usuario.responsavel_id:
            responsavel = usuario.responsavel
            ids_verificados = set(responsavel.coroinhas.values_list("id", flat=True))
            ids_heuristica = _ids_irmaos_por_nome_e_telefone(responsavel, ids_verificados)
            if ids_heuristica:
                AuditService.registrar(
                    AuditAcao.PORTAL_VINCULO_HEURISTICO,
                    usuario=usuario,
                    detalhes={
                        "responsavel_id": responsavel.id,
                        "coroinha_ids": sorted(ids_heuristica),
                    },
                )
            return Coroinha.objects.filter(id__in=ids_verificados | ids_heuristica).order_by("nome")
        return Coroinha.objects.none()

    @classmethod
    def get_resumo(cls, usuario: Usuario, coroinha_id: int, request=None) -> dict:
        if not cls.pode_ver_coroinha(usuario, coroinha_id):
            raise PermissionError("Sem permissão para ver este coroinha.")

        from apps.membership.models import Coroinha

        coroinha = Coroinha.objects.get(id=coroinha_id)
        hoje = timezone.now().date()

        itens = EscalaItem.objects.filter(coroinha=coroinha).select_related(
            "escala", "escala__missa"
        )
        escalas_total = itens.count()
        presencas_total = Presenca.objects.filter(
            escala_item__in=itens, status=StatusPresenca.PRESENTE
        ).count()
        faltas_total = Presenca.objects.filter(
            escala_item__in=itens, status=StatusPresenca.AUSENTE
        ).count()

        conclusoes = FormacaoConclusao.objects.filter(coroinha=coroinha).select_related("formacao")
        formacoes_concluidas = conclusoes.count()

        proxima_item = (
            itens.filter(escala__data__gte=hoje).order_by("escala__data", "escala__missa__horario").first()
        )
        proxima_escala = None
        if proxima_item:
            proxima_escala = {
                "data": proxima_item.escala.data.isoformat(),
                "missa": proxima_item.escala.missa.nome,
            }

        itens_mes_atual = itens.filter(
            escala__data__year=hoje.year, escala__data__month=hoje.month
        )

        escalas_list = []
        for item in itens_mes_atual.order_by("-escala__data"):
            pres = getattr(item, "presenca", None)
            try:
                pres = item.presenca
            except Presenca.DoesNotExist:
                pres = None
            escalas_list.append(
                {
                    "data": item.escala.data.isoformat(),
                    "missa": item.escala.missa.nome,
                    "presenca": pres.status if pres else None,
                }
            )

        formacoes_list = [
            {
                "titulo": c.formacao.titulo,
                "data": c.formacao.data.isoformat(),
                "descricao": c.formacao.descricao,
            }
            for c in conclusoes.order_by("-formacao__data")
        ]

        formacoes_total = Formacao.objects.count()

        return {
            "id": coroinha.id,
            "nome": coroinha.nome,
            "idade": coroinha.idade,
            "escola": coroinha.escola,
            "serie": coroinha.serie,
            "turma": coroinha.turma,
            "status": coroinha.status,
            "foto_url": build_foto_url(coroinha.foto, request),
            "escalas_total": escalas_total,
            "presencas_total": presencas_total,
            "faltas_total": faltas_total,
            "formacoes_concluidas": formacoes_concluidas,
            "formacoes_total": formacoes_total,
            "proxima_escala": proxima_escala,
            "escalas": escalas_list,
            "formacoes": formacoes_list,
        }

    @staticmethod
    def proximas_escalas_dashboard(limit: int = 5):
        hoje = timezone.now().date()
        escalas = (
            Escala.objects.filter(data__gte=hoje)
            .select_related("missa")
            .prefetch_related("itens")
            .order_by("data", "missa__horario")[:limit]
        )
        return [
            {
                "id": e.id,
                "data": e.data.isoformat(),
                "missa": e.missa.nome,
                "coroinhas_count": e.itens.count(),
            }
            for e in escalas
        ]
