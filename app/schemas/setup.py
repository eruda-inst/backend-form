from pydantic import BaseModel
from app.schemas import UsuarioResponse, EmpresaResponse

class SetupResponse(BaseModel):
    usuario: UsuarioResponse
    empresa: EmpresaResponse
