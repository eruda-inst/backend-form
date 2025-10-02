from fastapi import FastAPI
from fastapi.openapi.models import APIKey, APIKeyIn, SecuritySchemeType
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
import asyncio
from app.db.database import engine, criar_tabelas, SessionLocal
from app.core.config import settings
from contextlib import asynccontextmanager
from app.routers import integracoes, user, auth, setup, perfil, grupo, permissao, forms, respostas, empresa
from app.utils.seed import seed_grupo_admin_e_permissoes
from .websockets import forms as forms_ws
from .websockets import respostas as respostas_ws



async def wait_for_db():
    """Bloqueia até o banco aceitar conexões executando SELECT 1 com backoff exponencial."""
    attempts, delay, max_delay = 20, 1, 5
    for i in range(attempts):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception:
            if i == attempts - 1:
                raise
            await asyncio.sleep(delay)
            delay = min(delay * 2, max_delay)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await wait_for_db()
    with SessionLocal() as db:
        seed_grupo_admin_e_permissoes(db)
    yield


app = FastAPI(lifespan=lifespan,title="Sistema de Pesquisa e Formulários")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

criar_tabelas()



def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Sistema de Pesquisa e Formulários",
        version="1.3.0",
        description="API protegida por JWT",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
app.mount(settings.MEDIA_URL, StaticFiles(directory=settings.MEDIA_ROOT), name="media")
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(setup.router)
app.include_router(perfil.router)
app.include_router(grupo.router)
app.include_router(permissao.router)
app.include_router(forms.router)
app.include_router(respostas.router)
app.include_router(forms_ws.router)
app.include_router(respostas_ws.router)
app.include_router(empresa.router)
app.include_router(integracoes.router)



