"""
backend/routers/boards.py
Endpoints API pour les opérations CRUD sur les tableaux Kanban
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Board
from backend.schemas import BoardCreate, BoardUpdate, BoardOut
from backend.dependencies.auth import get_current_active_user
from backend.core.permissions import (
    check_board_access,
    require_board_ownership,
    get_board_or_404,
    BoardPermission
)

router = APIRouter()


@router.get("/", response_model=List[BoardOut])
def get_user_boards(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère la liste des tableaux auxquels l'utilisateur a accès (créés ou partagés).
    """
    # Tableaux créés par l'utilisateur
    owned_boards = db.query(Board).filter(Board.owner_id == current_user.id).all()

    # Tableaux partagés avec l'utilisateur (via la relation many-to-many)
    shared_boards = current_user.boards

    # Fusionner et dedupliquer les résultats
    all_boards = {board.id: board for board in owned_boards + shared_boards}
    boards_list = list(all_boards.values())

    return boards_list[skip:skip + limit]


@router.post("/", response_model=BoardOut, status_code=status.HTTP_201_CREATED)
def create_board(
    board_data: BoardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Crée un nouveau tableau. L'utilisateur actuel devient le propriétaire.
    """
    new_board = Board(
        name=board_data.name,
        description=board_data.description,
        is_public=board_data.is_public,
        background_color=board_data.background_color,
        owner_id=current_user.id
    )

    db.add(new_board)
    db.commit()
    db.refresh(new_board)
    return new_board


@router.get("/{board_id}", response_model=BoardOut)
def get_board(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les détails d'un tableau spécifique si l'utilisateur y a accès.
    """
    board = get_board_or_404(db, board_id, current_user)
    return board


@router.put("/{board_id}", response_model=BoardOut)
def update_board(
    board_id: int,
    board_update: BoardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Met à jour un tableau. Seul le propriétaire peut modifier les informations du tableau.
    """
    board = get_board_or_404(db, board_id)
    require_board_ownership(board, current_user)

    update_data = board_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(board, field, value)

    db.commit()
    db.refresh(board)
    return board


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Supprime un tableau et toutes ses données associées. Seul le propriétaire peut supprimer.
    """
    board = get_board_or_404(db, board_id)
    require_board_ownership(board, current_user)

    db.delete(board)
    db.commit()
    return None
