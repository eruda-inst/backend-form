from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import criar_tabelas, SessionLocal
from app.routers import user, auth, setup, perfil, grupo, permissao, forms
from fastapi.openapi.models import APIKey, APIKeyIn, SecuritySchemeType
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from app.utils.seed import seed_grupo_admin_e_permissoes
from .websockets import forms as forms_ws



@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    seed_grupo_admin_e_permissoes(db)
    db.close()
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
        version="1.0.0",
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
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(setup.router)
app.include_router(perfil.router)
app.include_router(grupo.router)
app.include_router(permissao.router)
app.include_router(forms.router)
app.include_router(forms_ws.router)



