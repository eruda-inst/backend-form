# core/identidade.py
import re

def normalizar_email(v: str | None) -> str | None:
    """
    Retorna o e-mail em minúsculas e sem espaços.
    """
    if not v: return None
    v = v.strip().lower()
    return v or None

def normalizar_telefone(v: str | None) -> str | None:
    """
    Retorna telefone só com dígitos, preservando +55 quando aplicável.
    """
    if not v: return None
    v = v.strip()
    if v.startswith("+"):
        d = "+" + re.sub(r"\D+", "", v[1:])
    else:
        d = re.sub(r"\D+", "", v)
        if len(d) == 11: d = f"+55{d}"
        elif d: d = f"+{d}"
    return d or None

def normalizar_cpf(v: str | None) -> str | None:
    if not v:
        return None
    d = re.sub(r"\D+", "", v)
    if len(d) != 11:
        return None
    if not _cpf_valido(d):
        return None
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"

def _cpf_valido(digits: str) -> bool:
    if digits == digits[0] * 11:
        return False
    def _calc(cd: str, mult_start: int):
        s = sum(int(cd[i]) * (mult_start - i) for i in range(len(cd)))
        r = (s * 10) % 11
        return 0 if r == 10 else r
    v1 = _calc(digits[:9], 10)
    v2 = _calc(digits[:9] + str(v1), 11)
    return digits[-2:] == f"{v1}{v2}"

    
