"""Remanejamento estilo Kanban: grupos mensais e celebrações."""

from django.db import transaction

from apps.membership.services.gemeos_service import GemeosService
from apps.scheduling.models import Escala, EscalaMensal, GrupoMensal, GrupoMensalMembro, ModoEscala
from apps.scheduling.services.escala_service import EscalaService
from apps.scheduling.services.grupo_montagem_service import GrupoMontagemService


class RemanejamentoEscalaService:
    @classmethod
    def _candidatos(cls):
        return GrupoMontagemService.candidatos()

    @classmethod
    def _familia_ids(cls, coroinha_id: int) -> set[int]:
        return GemeosService.familia_ids(coroinha_id, cls._candidatos())

    @classmethod
    def _reordenar_grupo(cls, grupo: GrupoMensal) -> None:
        for ordem, membro in enumerate(grupo.membros.order_by("ordem", "coroinha__nome"), start=1):
            if membro.ordem != ordem:
                membro.ordem = ordem
                membro.save(update_fields=["ordem"])

    @classmethod
    def sincronizar_escalas_grupo(cls, escala_mensal: EscalaMensal, grupo_numero: int) -> None:
        grupo = GrupoMensal.objects.filter(escala_mensal=escala_mensal, numero=grupo_numero).first()
        if not grupo:
            return
        ids = list(grupo.membros.order_by("ordem").values_list("coroinha_id", flat=True))
        for escala in Escala.objects.filter(escala_mensal=escala_mensal, grupo_numero=grupo_numero):
            EscalaService.definir_membros(escala, ids)

    @classmethod
    @transaction.atomic
    def mover_grupo(
        cls,
        escala_mensal: EscalaMensal,
        coroinha_id: int,
        grupo_destino_numero: int,
    ) -> None:
        if not (1 <= grupo_destino_numero <= 4):
            raise ValueError("Grupo destino deve ser entre 1 e 4.")

        familia = cls._familia_ids(coroinha_id)
        grupos_origem: set[int] = set()

        membros_familia = GrupoMensalMembro.objects.filter(
            grupo__escala_mensal=escala_mensal,
            coroinha_id__in=familia,
        ).select_related("grupo")
        for membro in membros_familia:
            grupos_origem.add(membro.grupo.numero)

        if grupo_destino_numero in grupos_origem and len(grupos_origem) == 1:
            return

        try:
            grupo_destino = GrupoMensal.objects.get(
                escala_mensal=escala_mensal,
                numero=grupo_destino_numero,
            )
        except GrupoMensal.DoesNotExist as exc:
            raise ValueError(f"Grupo {grupo_destino_numero} não encontrado neste mês.") from exc

        GrupoMensalMembro.objects.filter(
            grupo__escala_mensal=escala_mensal,
            coroinha_id__in=familia,
        ).delete()

        ordem_base = grupo_destino.membros.count()
        for offset, cid in enumerate(sorted(familia), start=1):
            GrupoMensalMembro.objects.create(
                grupo=grupo_destino,
                coroinha_id=cid,
                ordem=ordem_base + offset,
            )

        for numero in grupos_origem:
            grupo = GrupoMensal.objects.get(escala_mensal=escala_mensal, numero=numero)
            cls._reordenar_grupo(grupo)
        cls._reordenar_grupo(grupo_destino)

        for numero in grupos_origem | {grupo_destino_numero}:
            cls.sincronizar_escalas_grupo(escala_mensal, numero)

    @classmethod
    @transaction.atomic
    def mover_celebracao(
        cls,
        *,
        coroinha_id: int,
        escala_origem_id: int,
        escala_destino_id: int | None = None,
    ) -> tuple[Escala, Escala | None]:
        origem = Escala.objects.prefetch_related("itens").get(pk=escala_origem_id)
        familia = cls._familia_ids(coroinha_id)

        ids_origem = list(origem.itens.order_by("ordem").values_list("coroinha_id", flat=True))
        if not familia.intersection(ids_origem):
            raise ValueError("Coroinha não está na celebração de origem.")

        ids_restantes = [cid for cid in ids_origem if cid not in familia]
        EscalaService.definir_membros(origem, ids_restantes)

        destino = None
        if escala_destino_id is not None:
            if escala_destino_id == escala_origem_id:
                raise ValueError("Origem e destino são a mesma celebração.")
            destino = Escala.objects.prefetch_related("itens").get(pk=escala_destino_id)
            ids_destino = list(destino.itens.order_by("ordem").values_list("coroinha_id", flat=True))
            for cid in sorted(familia):
                if cid not in ids_destino:
                    ids_destino.append(cid)
            EscalaService.definir_membros(destino, ids_destino)

        return origem, destino

    @classmethod
    @transaction.atomic
    def atribuir_grupo_celebracao(cls, escala_id: int, grupo_numero: int) -> Escala:
        if not (1 <= grupo_numero <= 4):
            raise ValueError("Grupo deve ser entre 1 e 4.")

        escala = Escala.objects.select_related("escala_mensal").get(pk=escala_id)
        if not escala.escala_mensal:
            raise ValueError("Esta celebração não pertence a uma escala mensal.")

        grupo = GrupoMensal.objects.filter(
            escala_mensal=escala.escala_mensal,
            numero=grupo_numero,
        ).first()
        if not grupo:
            raise ValueError(f"Grupo {grupo_numero} não encontrado neste mês.")

        escala.grupo_numero = grupo_numero
        escala.modo = ModoEscala.GRUPO_MENSAL
        escala.save(update_fields=["grupo_numero", "modo"])

        ids = list(grupo.membros.order_by("ordem").values_list("coroinha_id", flat=True))
        EscalaService.definir_membros(escala, ids)
        return escala
