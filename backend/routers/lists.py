from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, crud
from ..database import get_db
from ..auth import get_current_active_user

router = APIRouter(prefix="/lists", tags=["lists"])

def verify_list_access(db: Session, list_id: int, user_id: int) -> models.List:
    """Vérifie que la liste existe et appartient à l'utilisateur"""
    db_list = crud.get_list(db, list_id=list_id)
    if not db_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Liste non trouvée"
        )
    if db_list.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à cette liste"
        )
    return db_list

@router.get("/", response_model=List[schemas.List])
def get_user_lists(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Récupère toutes les listes de l'utilisateur connecté"""
    return crud.get_lists_by_user(db, user_id=current_user.id)

@router.get("/{list_id}", response_model=schemas.List)
def get_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Récupère une liste spécifique"""
    return verify_list_access(db, list_id, current_user.id)

@router.post("/", response_model=schemas.List, status_code=status.HTTP_201_CREATED)
def create_list(
    list_data: schemas.ListCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Crée une nouvelle liste"""
    return crud.create_list(db=db, list=list_data, user_id=current_user.id)

@router.put("/{list_id}", response_model=schemas.List)
def update_list(
    list_id: int,
    list_data: schemas.ListUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Met à jour les informations d'une liste"""
    db_list = verify_list_access(db, list_id, current_user.id)
    return crud.update_list(db=db, list_id=list_id, list_data=list_data)

@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Supprime une liste et toutes ses tâches associées"""
    db_list = verify_list_access(db, list_id, current_user.id)
    crud.delete_list(db=db, list_id=list_id)
    return {"ok": True}

@router.put("/reorder", response_model=List[schemas.List])
def reorder_lists(
    reorder_data: schemas.ListReorder,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Réordonne les listes selon l'ordre fourni"""
    try:
        return crud.reorder_lists(db=db, user_id=current_user.id, ordered_ids=reorder_data.list_ids)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )