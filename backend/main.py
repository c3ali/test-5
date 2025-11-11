"""
Point d'entrée principal de l'API FastAPI
Configure CORS, middlewares et monte les routers
"""
import os
from pathlib import Path
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Import des routers
# TODO: Fix schema and dependency imports in these routers before enabling
# from backend.routers import boards, cards, labels, lists
from backend.routers import users

# Création de l'application FastAPI
app = FastAPI(
    title="API Kanban Board",
    description="API REST avec FastAPI pour gestion de tableaux Kanban",
    version="1.0.0"
)

# Configuration CORS
ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "*",  # En production, limitez aux domaines spécifiques
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montage des routers
app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["Users"]
)

# TODO: Enable these routers after fixing schema and dependency imports
# app.include_router(
#     boards.router,
#     prefix="/api/v1/boards",
#     tags=["Boards"]
# )
#
# app.include_router(
#     lists.router,
#     prefix="/api/v1/lists",
#     tags=["Lists"]
# )
#
# app.include_router(
#     cards.router,
#     prefix="/api/v1/cards",
#     tags=["Cards"]
# )
#
# app.include_router(
#     labels.router,
#     prefix="/api/v1/labels",
#     tags=["Labels"]
# )

# Endpoints de base
@app.get("/", tags=["Root"])
async def root():
    """Endpoint racine - redirige vers la documentation"""
    return {
        "message": "Bienvenue sur l'API Kanban Board",
        "status": "running",
        "documentation": "/docs",
        "api_docs": "/redoc",
        "health": "/api/health"
    }

@app.get("/api", tags=["Root"])
async def read_root():
    """Endpoint racine - vérifie que l'API fonctionne"""
    return {
        "message": "Bienvenue sur l'API Kanban Board",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Servir les fichiers statiques du frontend en production
# NOTE: This is mounted after API routes so API routes take precedence
dist_path = Path(__file__).parent.parent / "dist"
if dist_path.exists():
    app.mount("/assets", StaticFiles(directory=str(dist_path / "assets")), name="assets")
    # Don't mount at "/" as it would override all routes

@app.get("/api/health", tags=["Health"])
async def health_check():
    """Endpoint de health check pour monitoring"""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy", "api": "running"}
    )

# Configuration pour lancer le serveur directement
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        log_level="info"
    )
