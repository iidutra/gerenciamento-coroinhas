"""Gêmeos e irmãos na escala: sempre no mesmo grupo ou mesma missa."""

from __future__ import annotations

from collections import defaultdict

from apps.membership.models import Coroinha


def _norm(texto: str) -> str:
    return (texto or "").strip().lower()


def extrair_sobrenome(nome: str) -> str:
    """Sobrenome completo = tudo após o primeiro nome."""
    partes = _norm(nome).split()
    if len(partes) <= 1:
        return ""
    return " ".join(partes[1:])


class GemeosService:
    MENSAGEM_ESCALA = "Gêmeos e irmãos devem estar na mesma escala."

    @classmethod
    def par_gemeo(cls, coroinha: Coroinha) -> Coroinha | None:
        if coroinha.gemeo_de_id:
            return coroinha.gemeo_de
        return Coroinha.objects.filter(gemeo_de=coroinha).select_related("gemeo_de").first()

    @classmethod
    def chave_familia(cls, coroinha: Coroinha) -> tuple[str, str, str] | None:
        """Mesmo sobrenome completo e mesmos pais."""
        sobrenome = extrair_sobrenome(coroinha.nome)
        mae = _norm(coroinha.nome_mae)
        pai = _norm(coroinha.nome_pai)
        if not sobrenome or not mae or not pai:
            return None
        return (sobrenome, mae, pai)

    @classmethod
    def _unir(cls, parent: dict[int, int], a: int, b: int) -> None:
        ra, rb = cls._find(parent, a), cls._find(parent, b)
        if ra != rb:
            parent[rb] = ra

    @classmethod
    def _find(cls, parent: dict[int, int], x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    @classmethod
    def componentes(cls, candidatos: list[Coroinha]) -> dict[int, set[int]]:
        """Agrupa gêmeos (vínculo explícito) e irmãos (sobrenome + pais)."""
        id_map = {c.id: c for c in candidatos}
        parent = {c.id: c.id for c in candidatos}

        for coroinha in candidatos:
            par = cls.par_gemeo(coroinha)
            if par and par.id in id_map:
                cls._unir(parent, coroinha.id, par.id)

        familias: dict[tuple[str, str, str], list[int]] = defaultdict(list)
        for coroinha in candidatos:
            chave = cls.chave_familia(coroinha)
            if chave:
                familias[chave].append(coroinha.id)

        for ids in familias.values():
            base = ids[0]
            for outro in ids[1:]:
                cls._unir(parent, base, outro)

        componentes: dict[int, set[int]] = {}
        grupos: dict[int, set[int]] = defaultdict(set)
        for cid in id_map:
            grupos[cls._find(parent, cid)].add(cid)
        for cid in id_map:
            componentes[cid] = grupos[cls._find(parent, cid)]
        return componentes

    @classmethod
    def familia_ids(cls, coroinha_id: int, candidatos: list[Coroinha] | None = None) -> set[int]:
        if candidatos:
            componentes = cls.componentes(candidatos)
            return componentes.get(coroinha_id, {coroinha_id})

        coroinha = Coroinha.objects.filter(pk=coroinha_id).select_related("gemeo_de").first()
        if not coroinha:
            return set()

        ids = {coroinha_id}
        par = cls.par_gemeo(coroinha)
        if par:
            ids.add(par.id)

        chave = cls.chave_familia(coroinha)
        if not chave:
            return ids

        sobrenome, mae, pai = chave
        possiveis = Coroinha.objects.exclude(nome_mae="").exclude(nome_pai="").filter(
            nome_mae__iexact=coroinha.nome_mae.strip(),
            nome_pai__iexact=coroinha.nome_pai.strip(),
        )
        for outro in possiveis:
            if outro.id in ids:
                continue
            if cls.chave_familia(outro) == chave:
                ids.add(outro.id)
        return ids

    @classmethod
    def par_id(cls, coroinha_id: int) -> int | None:
        familia = cls.familia_ids(coroinha_id)
        familia.discard(coroinha_id)
        return next(iter(familia), None)

    @classmethod
    def par_efetivo(cls, coroinha: Coroinha, candidatos: list[Coroinha] | None = None) -> Coroinha | None:
        familia = cls.familia_ids(coroinha.id, candidatos)
        familia.discard(coroinha.id)
        if not familia:
            return None
        if candidatos:
            id_map = {c.id: c for c in candidatos}
            for fid in sorted(familia):
                if fid in id_map:
                    return id_map[fid]
            return None
        return Coroinha.objects.filter(pk__in=familia).order_by("nome").first()

    @classmethod
    def unidades(cls, candidatos: list[Coroinha]) -> list[list[Coroinha]]:
        """Agrupa coroinhas em unidades familiares (1 ou mais irmãos/gêmeos)."""
        componentes = cls.componentes(candidatos)
        vistos: set[int] = set()
        unidades: list[list[Coroinha]] = []

        for coroinha in candidatos:
            if coroinha.id in vistos:
                continue
            grupo_ids = componentes.get(coroinha.id, {coroinha.id})
            unidade = [c for c in candidatos if c.id in grupo_ids]
            if not unidade:
                unidade = [coroinha]
            unidades.append(unidade)
            vistos.update(c.id for c in unidade)
        return unidades

    @classmethod
    def validar_conjunto(cls, coroinha_ids: list[int]) -> None:
        """Irmãos/gêmeos devem estar todos incluídos ou todos ausentes."""
        ids = set(coroinha_ids)
        for cid in coroinha_ids:
            familia = cls.familia_ids(cid)
            if len(familia) <= 1:
                continue
            presentes = familia & ids
            if presentes and presentes != familia:
                raise ValueError(cls.MENSAGEM_ESCALA)

    @classmethod
    def expandir_ids(cls, ids: set[int]) -> set[int]:
        expandido = set(ids)
        for cid in list(ids):
            expandido |= cls.familia_ids(cid)
        return expandido

    @classmethod
    def completar_selecao(cls, selecionados: list[Coroinha], elegiveis: list[Coroinha]) -> list[Coroinha]:
        """Inclui irmãos/gêmeos elegíveis quando um deles foi escolhido."""
        elegiveis_map = {c.id: c for c in elegiveis}
        componentes = cls.componentes(elegiveis)
        resultado = list(selecionados)
        ids = {c.id for c in resultado}

        for coroinha in list(resultado):
            for fid in componentes.get(coroinha.id, {coroinha.id}):
                if fid not in ids and fid in elegiveis_map:
                    resultado.append(elegiveis_map[fid])
                    ids.add(fid)
        return resultado

    @classmethod
    def selecionar_da_familia(
        cls,
        pool: list[Coroinha],
        quantidade: int,
        *,
        candidatos: list[Coroinha] | None = None,
    ) -> list[Coroinha] | None:
        """Prefere escalar membros da mesma família juntos."""
        if quantidade < 1 or len(pool) < 2:
            return None

        base = candidatos or pool
        componentes = cls.componentes(base)
        vistos: set[int] = set()

        for coroinha in pool:
            if coroinha.id in vistos:
                continue
            familia = [c for c in pool if c.id in componentes.get(coroinha.id, {coroinha.id})]
            vistos.update(c.id for c in familia)
            if len(familia) < 2:
                continue
            if len(familia) >= quantidade:
                return familia[:quantidade]
            if quantidade == 2:
                return familia[:2]
        return None
