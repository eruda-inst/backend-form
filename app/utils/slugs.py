import secrets

def gerar_slug_publico():
    return secrets.token_urlsafe(16)