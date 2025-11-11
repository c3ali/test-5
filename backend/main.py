# backend/main.py
"""
Point d'entrée principal de l'API FastAPI
Configure CORS, middlewares et monte les routers
"""

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import des routers (à créer dans le dossier backend/routers/)
from routers import auth, users, items

# Création de l'application FastAPI
app = FastAPI(
    title="Mon API FastAPI",
    description="API REST avec FastAPI, CORS configuré et routers montés",
    version="1.0.0"
)

# Configuration CORS
# Modifiez ces origines selon vos besoins (URLs de votre frontend)
ORIGINS = [
    "http://localhost:3000",  # React, Vue, Angular (développement)
    "http://127.0.0.1:3000",
    "http://localhost:5173",   # Vite (développement)
    "https://votre-domaine.com",  # Production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,  # Origines autorisées
    allow_credentials=True,  # Autoriser les cookies/credentials
    allow_methods=["*"],     # Autoriser toutes les méthodes (GET, POST, etc.)
    allow_headers=["*"],     # Autoriser tous les headers
)

# Montage des routers
# Chaque router peut avoir un préfixe et des tags pour la documentation
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentification"]
)

app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["Utilisateurs"]
)

app.include_router(
    items.router,
    prefix="/api/v1/items",
    tags=["Items"]
)

# Endpoints de base
@app.get("/", tags=["Root"])
async def read_root():
    """Endpoint racine - vérifie que l'API fonctionne"""
    return {
        "message": "Bienvenue sur l'API FastAPI",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", tags["Health"])
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
        port=8000,
        reload=True,  # Rechargement automatique en développement
        log_level="info"
    )
```

## Instructions complémentaires

### Structure recommandée du projet :
```
backend/
├── main.py
├── routers/
│   ├── __init__.py
│   ├── auth.py
│   ├── users.py
│   └── items.py
└── requirements.txt
```

### Exemple de fichier router (`backend/routers/items.py`) :
```python
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/")
async def get_items():
    return {"items": ["item1", "item2"]}

@router.get("/{item_id}")
async def get_item(item_id: int):
    return {"item_id": item_id}
```

### Pour lancer l'API :

```bash
# Installation des dépendances
pip install fastapi uvicorn

# Lancement en développement
python main.py

# Ou avec uvicorn directement
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera disponible à l'adresse : http://localhost:8000
Documentation interactive : http://localhost:8000/