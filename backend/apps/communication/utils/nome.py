import unicodedata

# Conectores que indicam início do sobrenome (não fazem parte do nome composto).
CONECTORES = {"de", "da", "do", "dos", "das", "e", "di", "du", "del", "della", "van", "von"}

# Primeiros nomes que costumam ser compostos no Brasil (Maria Eduarda, Ana
# Cecília, João Pedro, Luiz Felipe...). Quando o nome começa com um destes e a
# palavra seguinte não é um conector, mantemos as duas palavras.
NOMES_COMPOSTOS = {
    "maria", "ana", "jose", "joao", "luiz", "luis", "pedro", "carlos",
    "antonio", "paulo", "marco", "marcos", "vitor", "victor", "joana",
    "jean", "luana", "sara", "sarah", "gabriel", "miguel", "davi",
    "francisco", "fernando", "rita", "rosa", "julia", "juliana", "joaquim",
    "matheus", "mateus", "isabel", "beatriz", "carolina", "eduarda",
}


def _sem_acento(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    ).lower()


def primeiro_nome(nome: str) -> str:
    """Retorna o primeiro nome, preservando nomes compostos comuns.

    Ex.: "Thiago Silva" -> "Thiago"; "Maria Eduarda de Souza" -> "Maria Eduarda";
    "Ana Cecília de Souza Furtado" -> "Ana Cecília"; "Maria de Lourdes" -> "Maria".
    """
    partes = (nome or "").split()
    if not partes:
        return nome or ""
    primeiro = partes[0]
    if len(partes) >= 2:
        segundo = partes[1]
        if _sem_acento(primeiro) in NOMES_COMPOSTOS and _sem_acento(segundo) not in CONECTORES:
            return f"{primeiro} {segundo}"
    return primeiro
