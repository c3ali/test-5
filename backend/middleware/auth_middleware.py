# backend/middleware/auth_middleware.py
"""
Middleware d'authentification JWT pour protéger les routes de l'API.

Ce middleware vérifie la présence et la validité d'un token JWT
dans l'en-tête Authorization avant d'autoriser l'accès aux routes protégées.
"""

from typing import Optional, Tuple
from jose import JWTError, jwt
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from datetime import datetime

# Configuration JWT - À adapter selon votre setup
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "votre-clé-secrète-super-sécurisée")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


def verify_token(token: str) -> Optional[dict]:
    """
    Vérifie et décode un token JWT.
    
    Args:
        token: Le token JWT à vérifier
        
    Returns:
        dict: Les données du payload si le token est valide
        None: Si le token est invalide ou expiré
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


class AuthMiddleware:
    """
    Middleware qui protège les routes en vérifiant l'authentification JWT.
    
    Exemple d'utilisation dans main.py:
        app.add_middleware(AuthMiddleware)
    """
    
    # Routes publiques qui ne nécessitent pas d'authentification
    PUBLIC_PATHS = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/health",
    ]
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        # Vérifier si le chemin est public
        if any(request.url.path.startswith(path) for path in self.PUBLIC_PATHS):
            return await call_next(request)
        
        # Extraire le token de l'en-tête Authorization
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token d'authentification manquant ou invalide",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = auth_header.replace("Bearer ", "")
        
        # Vérifier le token
        payload = verify_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide ou expiré",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Ajouter les informations de l'utilisateur à la requête
        request.state.user = payload
        request.state.user_id = payload.get("sub")
        
        # Log pour le débogage (optionnel)
        # print(f"Utilisateur authentifié: {request.state.user_id}")
        
        return await call_next(request)


# Alternative: Dépendance FastAPI pour une protection plus granulaire
class JWTBearer(HTTPBearer):
    """
    Dépendance FastAPI pour protéger des routes spécifiques.
    
    Exemple d'utilisation:
        @app.get("/protected-route")
        async def protected_route(user: dict = Depends(JWTBearer())):
            return {"user": user}
    """
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> dict:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Code d'authentification invalide",
            )
        
        if credentials.scheme != "Bearer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Schéma d'authentification invalide",
            )
        
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide ou expiré",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload


# Fonction utilitaire pour récupérer l'utilisateur courant dans les routeurs
def get_current_user(request: Request) -> Optional[dict]:
    """
    Récupère les informations de l'utilisateur authentifié depuis la requête.
    
    Args:
        request: La requête FastAPI
        
    Returns:
        dict: Les informations de l'utilisateur si authentifié
        None: Si aucun utilisateur n'est authentifié
    """
    return getattr(request.state, "user", None)


def get_current_user_id(request: Request) -> Optional[str]:
    """
    Récupère l'ID de l'utilisateur authentifié depuis la requête.
    
    Args:
        request: La requête FastAPI
        
    Returns:
        str: L'ID de l'utilisateur si authentifié
        None: Si aucun utilisateur n'est authentifié
    """
    return getattr(request.state, "user_id", None)
```

### ⚙️ Installation des dépendances requises

```bash
pip install python-jose[cryptography] fastapi
```

### 📝 Utilisation recommandée

**1. Dans `main.py` (middleware global):**

```python
from fastapi import FastAPI
from backend.middleware.auth_middleware import AuthMiddleware

app = FastAPI()
app.add_middleware(AuthMiddleware)
```

**2. Alternative par route (plus flexible):**

```python
from fastapi import Depends
from backend.middleware.auth_middleware import JWTBearer

@app.get("/api/v1/users/me")
async def get_current_user_info(user: dict = Depends(JWTBearer())):
    return {"user_id": user.get("sub"), "email": user.get("email")}
```

**3. Récupération de l'utilisateur dans les routeurs:**

```python
from fastapi import Request
from backend.middleware.auth_middleware import get_current_user_id

@app.post("/api/v1/posts")
async def create_post(request: Request, post_data: dict):
    user_id = get_current_user_id(request)
    # Créer le post avec user_id
    return {"status": "success", "user_id": user_id}
```

### 🔒 Variables d'environnement

Ajoutez à votre `.env`:
```env
JWT_SECRET_KEY=votre-clé-secrète-super-sécurisée-de-minimum-32-caractères
JWT_ALGORITHM=HS256
```

### ✅ Fonctionnalités incluses

- ✅ Vérification automatique du token JWT
- ✅ Gestion des routes publiques exclues
- ✅ Messages d'erreur clairs (401/403)
- ✅ Ajout des infos utilisateur au contexte de la requête
- ✅ Alternative par dépendance pour granularité fine
- ✅ Fonctions utilitaires pour accéder à l'utilisateur
- ✅ Type hints pour sécurité du code
- ✅ Documentation complète

N'oubliez pas d'adapter `PUBLIC_PATHS` selon vos besoins et de remplacer `sub` par la clé appropriée de votre payload