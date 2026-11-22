from __future__ import annotations

from apps.scheduling.models import FuncaoEscala

MAX_ENTRE_OS_DOIS = 2
MAX_ASSESSORES = 20

FUNCOES_MULTIPLAS: dict[str, int | None] = {
    FuncaoEscala.ENTRE_OS_DOIS: MAX_ENTRE_OS_DOIS,
    FuncaoEscala.ASSESSOR: None,
}


def validar_chaves_funcoes(funcoes: dict) -> None:
    validas = {c.value for c in FuncaoEscala}
    for chave in funcoes:
        if chave not in validas:
            raise ValueError(f"Função inválida: {chave}")


def _ids_da_funcao(funcao: str, valor) -> list[int]:
    if isinstance(valor, (list, tuple)):
        return [int(x) for x in valor if x is not None]
    if valor in (None, ""):
        return []
    return [int(valor)]


def expandir_funcoes(funcoes: dict) -> list[tuple[str, int]]:
    """Converte payload da API em pares (funcao, coroinha_id)."""
    validar_chaves_funcoes(funcoes)
    pares: list[tuple[str, int]] = []
    for funcao, valor in funcoes.items():
        if valor is None or valor == "":
            continue
        if isinstance(valor, (list, tuple)) and len(valor) == 0:
            continue
        if funcao in FUNCOES_MULTIPLAS:
            ids = _ids_da_funcao(funcao, valor)
            limite = FUNCOES_MULTIPLAS[funcao]
            if limite is not None and len(ids) > limite:
                label = dict(FuncaoEscala.choices).get(funcao, funcao)
                raise ValueError(f"{label} permite no máximo {limite} coroinha(s).")
            if funcao == FuncaoEscala.ASSESSOR and len(ids) > MAX_ASSESSORES:
                raise ValueError(f"Assessor permite no máximo {MAX_ASSESSORES} coroinha(s).")
            for cid in ids:
                pares.append((funcao, cid))
        else:
            if isinstance(valor, (list, tuple)):
                raise ValueError(f"Função {funcao} aceita apenas um coroinha.")
            pares.append((funcao, int(valor)))
    return pares