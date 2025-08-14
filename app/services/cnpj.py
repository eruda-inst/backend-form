def _only_digits(s: str) -> str:
    return "".join([c for c in s if c.isdigit()])

def validar_cnpj(cnpj: str) -> bool:
    """Valida um CNPJ pelo dígito verificador."""
    c = _only_digits(cnpj)
    if len(c) != 14 or len(set(c)) == 1:
        return False
    pesos1 = [5,4,3,2,9,8,7,6,5,4,3,2]
    soma1 = sum(int(d)*p for d,p in zip(c[:12], pesos1))
    d1 = 11 - (soma1 % 11)
    d1 = 0 if d1 >= 10 else d1
    pesos2 = [6] + pesos1
    soma2 = sum(int(d)*p for d,p in zip(c[:12]+str(d1), pesos2))
    d2 = 11 - (soma2 % 11)
    d2 = 0 if d2 >= 10 else d2
    return c[-2:] == f"{d1}{d2}"
