"""
FastAPI Application Entry Point - Simulador de Epidemias Web API

Este módulo define la aplicación principal FastAPI que expone
la lógica de simulación epidémica a través de una API REST local.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.utils.logger import get_logger

# Routers
from api.routers import nodes, simulation, mtc

logger = get_logger(__name__)

# Crear instancia FastAPI
app = FastAPI(
    title="Simulador de Epidemias API",
    description="API REST para simulación de epidemias en redes de contacto estudiantil",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS para desarrollo local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(nodes.router, prefix="/api", tags=["Visualización"])
app.include_router(simulation.router, prefix="/api", tags=["Simulación"])
app.include_router(mtc.router, prefix="/api", tags=["MTC"])


@app.get("/")
async def root():
    """Endpoint raíz - información de la API."""
    return {
        "message": "Simulador de Epidemias API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.on_event("startup")
async def startup_event():
    """Evento de inicio - inicializar recursos."""
    logger.info("Iniciando Simulador de Epidemias API v1.0.0")
    logger.info("Documentación disponible en: http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre - limpieza de recursos."""
    logger.info("Cerrando Simulador de Epidemias API")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
