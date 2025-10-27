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

def normalizar_cnpj(v: str | None) -> str | None:
    """
    Retorna o CNPJ formatado com pontos, barra e hífen.
    """
    if not v:
        return None
    d = re.sub(r"\D+", "", v)
    if len(d) != 14:
        return None
    if not _cnpj_valido(d):
        return None
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"

def _cnpj_valido(digits: str) -> bool:
    if digits == digits[0] * 14:
        return False
    def _calc(cd: str, mult: list[int]):
        s = sum(int(cd[i]) * mult[i] for i in range(len(cd)))
        r = s % 11
        return 0 if r < 2 else 11 - r
    mult1 = [5,4,3,2,9,8,7,6,5,4,3,2]
    mult2 = [6] + mult1
    v1 = _calc(digits[:12], mult1)
    v2 = _calc(digits[:12] + str(v1), mult2)
    return digits[-2:] == f"{v1}{v2}"
