import re


def normalizar_telefone_whatsapp(telefone: str, pais: str = "55") -> str:
    """E.164 simplificado para WhatsApp (somente dígitos, com DDI)."""
    digitos = re.sub(r"\D", "", telefone or "")
    if not digitos:
        return ""
    if digitos.startswith("00"):
        digitos = digitos[2:]
    if len(digitos) in (10, 11) and not digitos.startswith(pais):
        # Celular BR antigo (DDD + 8 dígitos começando em 6–9): insere o 9
        if len(digitos) == 10 and digitos[2] in "6789":
            digitos = f"{pais}{digitos[:2]}9{digitos[2:]}"
        else:
            digitos = f"{pais}{digitos}"
    # Já com DDI mas sem o 9 do celular (55 + DDD + 8 dígitos)
    if digitos.startswith(pais) and len(digitos) == 12 and digitos[4] in "6789":
        digitos = f"{digitos[:4]}9{digitos[4:]}"
    return digitos
