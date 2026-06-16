import re


def normalizar_telefone_whatsapp(telefone: str, pais: str = "55") -> str:
    """E.164 simplificado para WhatsApp (somente dígitos, com DDI)."""
    digitos = re.sub(r"\D", "", telefone or "")
    if not digitos:
        return ""
    if digitos.startswith("00"):
        digitos = digitos[2:]
    if len(digitos) in (10, 11) and not digitos.startswith(pais):
        digitos = f"{pais}{digitos}"
    return digitos
