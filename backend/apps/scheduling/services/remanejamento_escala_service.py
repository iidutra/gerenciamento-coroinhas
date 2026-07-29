"""Remanejamento estilo Kanban: grupos mensais e celebrações."""

from datetime import timedelta

from django.db import transaction

from apps.membership.services.gemeos_service import GemeosService
from apps.scheduling.models import Escala, EscalaMensal, GrupoMensal, GrupoMensalMembro, ModoEscala, TipoSlotMissa
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
    def _coroinha_ids_em_slot(
        cls, escala_mensal: EscalaMensal, data, tipo_slot: str
    ) -> set[int]:
        ids: set[int] = set()
        for escala in Escala.objects.filter(
            escala_mensal=escala_mensal,
            data=data,
            missa__tipo_slot=tipo_slot,
        ).prefetch_related("itens"):
            ids.update(escala.itens.values_list("coroinha_id", flat=True))
        return ids

    @classmethod
    def _coroinha_ids_excluidos_da_escala_grupo(
        cls, escala_mensal: EscalaMensal, escala: Escala
    ) -> set[int]:
        slot = escala.missa.tipo_slot
        if slot == TipoSlotMissa.DOMINGO_MANHA:
            return cls._coroinha_ids_em_slot(
                escala_mensal, escala.data, TipoSlotMissa.COMUNIDADE_DOMINGO
            )
        if slot == TipoSlotMissa.DOMINGO_NOITE:
            sexta = escala.data - timedelta(days=2)
            return cls._coroinha_ids_em_slot(
                escala_mensal, sexta, TipoSlotMissa.SEXTA_ADORACAO
            )
        return set()

    @classmethod
    def _membros_efetivos_escala_grupo(
        cls, escala_mensal: EscalaMensal, grupo_numero: int, escala: Escala
    ) -> list[int]:
        grupo = GrupoMensal.objects.filter(
            escala_mensal=escala_mensal, numero=grupo_numero
        ).first()
        if not grupo:
            return []
        ids_grupo = list(grupo.membros.order_by("ordem").values_list("coroinha_id", flat=True))
        excluir = cls._coroinha_ids_excluidos_da_escala_grupo(escala_mensal, escala)
        return [cid for cid in ids_grupo if cid not in excluir]

    @classmethod
    def sincronizar_escalas_grupo(cls, escala_mensal: EscalaMensal, grupo_numero: int) -> None:
        grupo = GrupoMensal.objects.filter(escala_mensal=escala_mensal, numero=grupo_numero).first()
        if not grupo:
            return
        for escala in Escala.objects.filter(escala_mensal=escala_mensal, grupo_numero=grupo_numero):
            ids = cls._membros_efetivos_escala_grupo(escala_mensal, grupo_numero, escala)
            EscalaService.definir_membros(escala, ids)

    @classmethod
    def _resolver_escala_origem_transferencia(
        cls,
        escala_mensal: EscalaMensal,
        coroinha_id: int,
        destino: Escala,
        grupo_numero: int | None = None,
    ) -> Escala | None:
        slot_dest = destino.missa.tipo_slot

        if slot_dest == TipoSlotMissa.COMUNIDADE_DOMINGO:
            candidatos = Escala.objects.filter(
                escala_mensal=escala_mensal,
                data=destino.data,
                missa__tipo_slot=TipoSlotMissa.DOMINGO_MANHA,
            )
            if grupo_numero is not None:
                candidatos = candidatos.filter(grupo_numero=grupo_numero)
            for escala in candidatos.prefetch_related("itens"):
                if escala.itens.filter(coroinha_id=coroinha_id).exists():
                    return escala
            return candidatos.first()

        if slot_dest == TipoSlotMissa.SEXTA_ADORACAO:
            domingo = destino.data + timedelta(days=2)
            candidatos = Escala.objects.filter(
                escala_mensal=escala_mensal,
                data=domingo,
                missa__tipo_slot=TipoSlotMissa.DOMINGO_NOITE,
            )
            if grupo_numero is not None:
                candidatos = candidatos.filter(grupo_numero=grupo_numero)
            for escala in candidatos.prefetch_related("itens"):
                if escala.itens.filter(coroinha_id=coroinha_id).exists():
                    return escala
            return candidatos.first()

        return None

    @classmethod
    @transaction.atomic
    def transferir_para_celebracao(
        cls,
        escala_mensal: EscalaMensal,
        coroinha_id: int,
        escala_destino_id: int,
        grupo_numero: int | None = None,
    ) -> tuple[Escala, Escala]:
        destino = Escala.objects.prefetch_related("itens").get(pk=escala_destino_id)
        if destino.escala_mensal_id != escala_mensal.id:
            raise ValueError("Celebração de destino não pertence a esta escala mensal.")

        origem = cls._resolver_escala_origem_transferencia(
            escala_mensal, coroinha_id, destino, grupo_numero
        )
        if not origem:
            raise ValueError(
                "Não foi possível identificar a missa de origem (domingo manhã ou domingo noite)."
            )

        ids_origem = set(origem.itens.values_list("coroinha_id", flat=True))
        familia = cls._familia_ids(coroinha_id)
        if familia.intersection(ids_origem):
            origem_atualizada, destino_atualizado = cls.mover_celebracao(
                coroinha_id=coroinha_id,
                escala_origem_id=origem.id,
                escala_destino_id=destino.id,
            )
        else:
            ids_destino = list(destino.itens.order_by("ordem").values_list("coroinha_id", flat=True))
            for cid in sorted(familia):
                if cid not in ids_destino:
                    ids_destino.append(cid)
            EscalaService.definir_membros(destino, ids_destino)
            origem_atualizada = origem
            destino_atualizado = Escala.objects.prefetch_related("itens").get(pk=destino.pk)

        assert destino_atualizado is not None

        if origem.grupo_numero:
            cls.sincronizar_escalas_grupo(escala_mensal, origem.grupo_numero)

        origem_atualizada = Escala.objects.prefetch_related("itens").get(pk=origem.id)
        destino_atualizado = Escala.objects.prefetch_related("itens").get(pk=destino.id)
        return origem_atualizada, destino_atualizado

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

            if origem.escala_mensal and origem.grupo_numero and cls._transferencia_afeta_grupo(
                origem, destino
            ):
                cls.sincronizar_escalas_grupo(origem.escala_mensal, origem.grupo_numero)

        return origem, destino

    @classmethod
    def _transferencia_afeta_grupo(cls, origem: Escala, destino: Escala) -> bool:
        slot_dest = destino.missa.tipo_slot
        if slot_dest == TipoSlotMissa.COMUNIDADE_DOMINGO and destino.data == origem.data:
            return origem.missa.tipo_slot == TipoSlotMissa.DOMINGO_MANHA
        if slot_dest == TipoSlotMissa.SEXTA_ADORACAO and destino.data == origem.data - timedelta(
            days=2
        ):
            return origem.missa.tipo_slot == TipoSlotMissa.DOMINGO_NOITE
        return False

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

        ids = cls._membros_efetivos_escala_grupo(escala.escala_mensal, grupo_numero, escala)
        EscalaService.definir_membros(escala, ids)
        return escala
