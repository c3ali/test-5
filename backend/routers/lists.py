"""
backend/routers/lists.py
Endpoints API pour les opérations CRUD sur les listes Kanban
"""

from typing import List as ListType
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Board, List
from backend.schemas import ListCreate, ListUpdate, ListOut
from backend.dependencies.auth import get_current_active_user
from backend.core.permissions import get_board_or_404, check_board_access, BoardPermission

router = APIRouter()


@router.get("/board/{board_id}/lists", response_model=ListType[ListOut])
def get_board_lists(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère toutes les listes d'un tableau.
    """
    board = get_board_or_404(db, board_id, current_user)
    lists = db.query(List).filter(List.board_id == board_id).order_by(List.position).all()
    return lists


@router.post("/board/{board_id}/lists", response_model=ListOut, status_code=status.HTTP_201_CREATED)
def create_list(
    board_id: int,
    list_data: ListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Crée une nouvelle liste dans un tableau.
    """
    board = get_board_or_404(db, board_id, current_user)
    check_board_access(board, current_user, BoardPermission.WRITE)

    new_list = List(
        name=list_data.name,
        position=list_data.position,
        board_id=board_id
    )

    db.add(new_list)
    db.commit()
    db.refresh(new_list)
    return new_list


@router.get("/{list_id}", response_model=ListOut)
def get_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les détails d'une liste spécifique.
    """
    list_obj = db.query(List).filter(List.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Liste non trouvée"
        )

    # Vérifier l'accès au board
    board = list_obj.board
    check_board_access(board, current_user, BoardPermission.READ)

    return list_obj


@router.put("/{list_id}", response_model=ListOut)
def update_list(
    list_id: int,
    list_update: ListUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Met à jour une liste.
    """
    list_obj = db.query(List).filter(List.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Liste non trouvée"
        )

    # Vérifier l'accès au board
    board = list_obj.board
    check_board_access(board, current_user, BoardPermission.WRITE)

    update_data = list_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(list_obj, field, value)

    db.commit()
    db.refresh(list_obj)
    return list_obj


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Supprime une liste et toutes ses cartes.
    """
    list_obj = db.query(List).filter(List.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Liste non trouvée"
        )

    # Vérifier l'accès au board
    board = list_obj.board
    check_board_access(board, current_user, BoardPermission.WRITE)

    db.delete(list_obj)
    db.commit()
    return None
