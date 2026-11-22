from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from apps.membership.models import Coroinha, StatusCoroinha
from apps.membership.services.gemeos_service import GemeosService
from apps.scheduling.funcoes_payload import expandir_funcoes
from apps.scheduling.models import Escala, EscalaItem, FuncaoEscala, ModoEscala


class EscalaStrategy(ABC):
    @abstractmethod
    def selecionar(self, candidatos: list[Coroinha], quantidade: int, escala: Escala) -> list[Coroinha]:
        ...


class SorteioEquilibradoStrategy(EscalaStrategy):
    """Prioriza quem serviu menos nos últimos 90 dias."""

    def selecionar(self, candidatos: list[Coroinha], quantidade: int, escala: Escala) -> list[Coroinha]:
        if not candidatos:
            return []
        desde = timezone.now().date() - timedelta(days=90)
        ids_dia = set(
            EscalaItem.objects.filter(escala__data=escala.data).values_list("coroinha_id", flat=True)
        )
        candidatos = [c for c in candidatos if c.id not in ids_dia]
        if not candidatos:
            return []

        contagem = (
            EscalaItem.objects.filter(
                coroinha_id__in=[c.id for c in candidatos],
                escala__data__gte=desde,
            )
            .values("coroinha_id")
            .annotate(total=Count("id"))
        )
        scores = {row["coroinha_id"]: row["total"] for row in contagem}
        ordenados = sorted(candidatos, key=lambda c: scores.get(c.id, 0))
        selecionados = ordenados[:quantidade]
        return GemeosService.completar_selecao(selecionados, candidatos)


class SelecaoManualStrategy(EscalaStrategy):
    def __init__(self, coroinha_ids: list[int]):
        self.coroinha_ids = coroinha_ids

    def selecionar(self, candidatos: list[Coroinha], quantidade: int, escala: Escala) -> list[Coroinha]:
        candidatos_map = {c.id: c for c in candidatos}
        selecionados = [candidatos_map[cid] for cid in self.coroinha_ids if cid in candidatos_map][:quantidade]
        GemeosService.validar_conjunto([c.id for c in selecionados])
        return GemeosService.completar_selecao(selecionados, candidatos)


class EscalaService:
    @staticmethod
    def candidatos_elegiveis():
        return list(
            Coroinha.objects.filter(
                status__in=[StatusCoroinha.ATIVO, StatusCoroinha.EM_FORMACAO],
                comunidade_fixa="",
            ).order_by("nome")
        )

    @classmethod
    def montar(
        cls,
        data,
        missa_id: int,
        modo: str,
        quantidade: int,
        usuario,
        coroinha_ids: list[int] | None = None,
        funcoes: dict[str, int] | None = None,
    ) -> Escala:
        from apps.scheduling.models import Missa

        missa = Missa.objects.get(pk=missa_id)
        if Escala.objects.filter(data=data, missa=missa).exists():
            raise ValueError("Já existe escala para esta data e missa.")

        candidatos = cls.candidatos_elegiveis()
        if modo == ModoEscala.SELECAO_MANUAL:
            if not coroinha_ids:
                raise ValueError("Informe os coroinhas para seleção manual.")
            strategy: EscalaStrategy = SelecaoManualStrategy(coroinha_ids)
        else:
            strategy = SorteioEquilibradoStrategy()

        escala = Escala.objects.create(data=data, missa=missa, modo=modo, criado_por=usuario)
        selecionados = strategy.selecionar(candidatos, quantidade, escala)

        if not selecionados:
            escala.delete()
            raise ValueError("Nenhum coroinha disponível para a escala.")

        for i, coroinha in enumerate(selecionados):
            EscalaItem.objects.create(escala=escala, coroinha=coroinha, ordem=i + 1)

        if funcoes:
            cls.atribuir_funcoes(escala, funcoes)

        return escala

    @classmethod
    def montar_com_notificacao(
        cls,
        *,
        notificar: bool | None,
        usuario,
        **kwargs,
    ) -> tuple[Escala, object | None]:
        from apps.scheduling.services.notificacao_escala_service import NotificacaoEscalaService

        escala = cls.montar(usuario=usuario, **kwargs)
        mensagem = NotificacaoEscalaService.notificar_se_habilitado(escala, usuario, notificar=notificar)
        return escala, mensagem

    @classmethod
    def ids_coroinhas_elegiveis(cls) -> list[int]:
        return [c.id for c in cls.candidatos_elegiveis()]

    @classmethod
    def marcar_todos_coroinhas(cls, escala: Escala) -> Escala:
        ids = cls.ids_coroinhas_elegiveis()
        if not ids:
            raise ValueError("Nenhum coroinha elegível para escalar.")
        cls.definir_membros(escala, ids, todos_coroinhas=True)
        return escala

    @staticmethod
    def definir_membros(
        escala: Escala,
        coroinha_ids: list[int],
        *,
        todos_coroinhas: bool | None = None,
    ) -> Escala:
        """Reconcilia os coroinhas da escala: adiciona os novos e remove os
        que saíram, preservando as funções de quem permanece."""
        novos = list(dict.fromkeys(coroinha_ids))  # remove duplicados mantendo ordem

        validos = set(
            Coroinha.objects.filter(id__in=novos).values_list("id", flat=True)
        )
        desconhecidos = [cid for cid in novos if cid not in validos]
        if desconhecidos:
            raise ValueError("Coroinha(s) inexistente(s) na seleção.")

        GemeosService.validar_conjunto(novos)

        atuais = {item.coroinha_id: item for item in escala.itens.all()}

        remover = [cid for cid in atuais if cid not in novos]
        if remover:
            escala.itens.filter(coroinha_id__in=remover).delete()

        ordem = 0
        for cid in novos:
            ordem += 1
            item = atuais.get(cid)
            if item:
                if item.ordem != ordem:
                    item.ordem = ordem
                    item.save(update_fields=["ordem"])
            else:
                EscalaItem.objects.create(escala=escala, coroinha_id=cid, ordem=ordem)

        if todos_coroinhas is True:
            escala.todos_coroinhas = True
        elif todos_coroinhas is False:
            escala.todos_coroinhas = False
        else:
            todos_ids = set(EscalaService.ids_coroinhas_elegiveis())
            escala.todos_coroinhas = todos_ids and set(novos) == todos_ids
        escala.save(update_fields=["todos_coroinhas"])

        return escala

    @staticmethod
    def atribuir_funcoes(escala: Escala, funcoes: dict) -> Escala:
        escala.itens.update(funcao=None, funcoes=[])

        pares = expandir_funcoes(funcoes)
        por_coroinha: dict[int, list[str]] = defaultdict(list)
        for funcao, coroinha_id in pares:
            if funcao not in por_coroinha[coroinha_id]:
                por_coroinha[coroinha_id].append(funcao)

        for coroinha_id, lista in por_coroinha.items():
            item = escala.itens.filter(coroinha_id=coroinha_id).first()
            if not item:
                item = EscalaItem.objects.create(
                    escala=escala,
                    coroinha_id=coroinha_id,
                    ordem=escala.itens.count() + 1,
                )
            item.aplicar_funcoes(lista)
            item.save(update_fields=["funcao", "funcoes"])

        return escala
