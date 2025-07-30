from fastapi import FastAPI
from app.database import criar_tabelas
from app.routers import user, auth, setup, perfil
from fastapi.openapi.models import APIKey, APIKeyIn, SecuritySchemeType
from fastapi.openapi.utils import get_openapi

app = FastAPI(title="Sistema de Pesquisa e Formulários")

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
