from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv

load_dotenv()


SEGREDO_JWT = os.getenv("JWT_SECRET", "padrão-inseguro")
ALGORITMO_JWT = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)

def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    return pwd_context.verify(senha_plana, senha_hash)

def gerar_token(dados: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = dados.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    return jwt.encode(to_encode, SEGREDO_JWT, algorithm=ALGORITMO_JWT)

def decode_jwt(token: str) -> dict | None:
    try:
        return jwt.decode(token, SEGREDO_JWT, algorithms=[ALGORITMO_JWT])
    except JWTError:
        return None

def gerar_refresh_token(dados: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = dados.copy()
    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })
    return jwt.encode(to_encode, SEGREDO_JWT, algorithm=ALGORITMO_JWT)
