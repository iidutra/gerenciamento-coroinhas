"""Gêmeos na escala: sempre no mesmo grupo ou mesma missa."""

from __future__ import annotations

from apps.membership.models import Coroinha


def _norm(texto: str) -> str:
    return (texto or "").strip().lower()


class GemeosService:
    @classmethod
    def par_gemeo(cls, coroinha: Coroinha) -> Coroinha | None:
        if coroinha.gemeo_de_id:
            return coroinha.gemeo_de
        return Coroinha.objects.filter(gemeo_de=coroinha).select_related("gemeo_de").first()

    @classmethod
    def par_id(cls, coroinha_id: int) -> int | None:
        row = (
            Coroinha.objects.filter(pk=coroinha_id)
            .values("id", "gemeo_de_id")
            .first()
        )
        if not row:
            return None
        if row["gemeo_de_id"]:
            return row["gemeo_de_id"]
        rev = Coroinha.objects.filter(gemeo_de_id=coroinha_id).values_list("id", flat=True).first()
        return rev

    @classmethod
    def detectar_par_auto(cls, coroinha: Coroinha, candidatos: list[Coroinha]) -> Coroinha | None:
        """Mesma data de nascimento e mesmos pais (quando informados)."""
        mae = _norm(coroinha.nome_mae)
        pai = _norm(coroinha.nome_pai)
        if not mae and not pai:
            return None
        for outro in candidatos:
            if outro.id == coroinha.id:
                continue
            if outro.data_nascimento != coroinha.data_nascimento:
                continue
            if mae and _norm(outro.nome_mae) == mae:
                return outro
            if pai and _norm(outro.nome_pai) == pai:
                return outro
        return None

    @classmethod
    def par_efetivo(cls, coroinha: Coroinha, candidatos: list[Coroinha] | None = None) -> Coroinha | None:
        par = cls.par_gemeo(coroinha)
        if par:
            return par
        if candidatos:
            return cls.detectar_par_auto(coroinha, candidatos)
        return None

    @classmethod
    def unidades(cls, candidatos: list[Coroinha]) -> list[list[Coroinha]]:
        """Agrupa coroinhas em unidades de 1 ou 2 (par de gêmeos)."""
        ids_pool = {c.id for c in candidatos}
        usados: set[int] = set()
        unidades: list[list[Coroinha]] = []

        for coroinha in candidatos:
            if coroinha.id in usados:
                continue
            par = cls.par_efetivo(coroinha, candidatos)
            if par and par.id in ids_pool and par.id not in usados:
                unidades.append([coroinha, par])
                usados.add(coroinha.id)
                usados.add(par.id)
            else:
                unidades.append([coroinha])
                usados.add(coroinha.id)
        return unidades

    @classmethod
    def validar_conjunto(cls, coroinha_ids: list[int]) -> None:
        """Gêmeos devem estar todos incluídos ou todos ausentes."""
        ids = set(coroinha_ids)
        for cid in coroinha_ids:
            par_id = cls.par_id(cid)
            if par_id and (cid in ids) != (par_id in ids):
                raise ValueError("Gêmeos devem estar na mesma escala.")

    @classmethod
    def expandir_ids(cls, ids: set[int]) -> set[int]:
        expandido = set(ids)
        for cid in list(ids):
            par_id = cls.par_id(cid)
            if par_id:
                expandido.add(par_id)
        return expandido

    @classmethod
    def completar_selecao(cls, selecionados: list[Coroinha], elegiveis: list[Coroinha]) -> list[Coroinha]:
        """Inclui o gêmeo quando um deles foi escolhido e o par está elegível."""
        elegiveis_map = {c.id: c for c in elegiveis}
        resultado = list(selecionados)
        ids = {c.id for c in resultado}
        for coroinha in list(resultado):
            par = cls.par_efetivo(coroinha, elegiveis)
            if par and par.id not in ids and par.id in elegiveis_map:
                resultado.append(par)
                ids.add(par.id)
        return resultado
