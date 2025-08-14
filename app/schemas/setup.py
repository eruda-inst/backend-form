from pydantic import BaseModel
from app.schemas import EmpresaCreate, UsuarioCreate

class SetupPayload(BaseModel):
    usuario: UsuarioCreate
    empresa: EmpresaCreate