"""
Router pour la gestion des utilisateurs
"""
from fastapi import APIRouter, HTTPException, status

router = APIRouter()

@router.get("/")
async def get_users():
    """Récupère la liste des utilisateurs"""
    return {"users": []}

@router.get("/{user_id}")
async def get_user(user_id: int):
    """Récupère un utilisateur par son ID"""
    return {"user_id": user_id}
