from __future__ import annotations

from apps.scheduling.models import FuncaoEscala

MAX_ENTRE_OS_DOIS = 2


def validar_chaves_funcoes(funcoes: dict) -> None:
    validas = {c.value for c in FuncaoEscala}
    for chave in funcoes:
        if chave not in validas:
            raise ValueError(f"Função inválida: {chave}")


def expandir_funcoes(funcoes: dict) -> list[tuple[str, int]]:
    """Converte payload da API em pares (funcao, coroinha_id). EntreOsDois aceita lista."""
    validar_chaves_funcoes(funcoes)
    pares: list[tuple[str, int]] = []
    for funcao, valor in funcoes.items():
        if valor is None or valor == "":
            continue
        if isinstance(valor, (list, tuple)) and len(valor) == 0:
            continue
        if funcao == FuncaoEscala.ENTRE_OS_DOIS:
            if isinstance(valor, (list, tuple)):
                ids = [int(x) for x in valor if x is not None]
            else:
                ids = [int(valor)]
            if len(ids) > MAX_ENTRE_OS_DOIS:
                raise ValueError("Entre os dois permite no máximo 2 coroinhas.")
            for cid in ids:
                pares.append((funcao, cid))
        else:
            if isinstance(valor, (list, tuple)):
                raise ValueError(f"Função {funcao} aceita apenas um coroinha.")
            pares.append((funcao, int(valor)))
    return pares