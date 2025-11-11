"""
Point d'entrée principal de l'API FastAPI
Configure CORS, middlewares et monte les routers
"""
import os
from pathlib import Path
from fastapi import FastAPI, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
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
@app.get("/api", tags=["Root"])
async def read_root():
    """Endpoint racine de l'API"""
    return {
        "message": "Bienvenue sur l'API Kanban Board",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/api/health", tags=["Health"])
async def health_check():
    """Endpoint de health check pour monitoring"""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy", "api": "running"}
    )

# Servir le frontend Vue.js (doit être après toutes les routes API)
dist_path = Path(__file__).parent.parent / "dist"
if dist_path.exists():
    # Servir les assets statiques (JS, CSS, images)
    if (dist_path / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(dist_path / "assets")), name="assets")

    # Route pour la page d'accueil
    @app.get("/")
    async def serve_home():
        """Sert la page d'accueil du frontend Vue.js"""
        index_path = dist_path / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return JSONResponse(
            content={
                "message": "Frontend non construit. Accédez à /docs pour l'API.",
                "api": "/api",
                "docs": "/docs"
            }
        )

    # Servir index.html pour toutes les autres routes (supporte Vue Router)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Sert le frontend Vue.js pour toutes les routes non-API"""
        # Ne pas intercepter les routes API
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi.json"):
            raise HTTPException(status_code=404, detail="Not Found")

        # Servir les fichiers statiques s'ils existent
        file_path = dist_path / full_path
        if file_path.is_file():
            return FileResponse(file_path)

        # Sinon servir index.html (pour Vue Router)
        index_path = dist_path / "index.html"
        if index_path.exists():
            return FileResponse(index_path)

        raise HTTPException(status_code=404, detail="Frontend not found")
else:
    # Si le dossier dist n'existe pas, afficher un message
    @app.get("/")
    async def serve_home_no_dist():
        """Message si le frontend n'est pas construit"""
        return JSONResponse(
            content={
                "message": "Frontend non disponible. Accédez à /docs pour l'API.",
                "api": "/api",
                "docs": "/docs",
                "health": "/api/health"
            }
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
