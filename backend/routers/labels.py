"""
backend/routers/labels.py
Endpoints API pour les opérations CRUD sur les labels Kanban
"""

from typing import List as ListType
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Board, Label
from backend.schemas import LabelCreate, LabelUpdate, LabelResponse
from backend.dependencies.auth import get_current_active_user
from backend.core.permissions import get_board_or_404, check_board_access, BoardPermission

router = APIRouter()


@router.get("/board/{board_id}/labels", response_model=ListType[LabelResponse])
def get_board_labels(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère tous les labels d'un tableau.
    """
    board = get_board_or_404(db, board_id, current_user)
    labels = db.query(Label).filter(Label.board_id == board_id).all()
    return labels


@router.post("/board/{board_id}/labels", response_model=LabelResponse, status_code=status.HTTP_201_CREATED)
def create_label(
    board_id: int,
    label_data: LabelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Crée un nouveau label dans un tableau.
    """
    board = get_board_or_404(db, board_id, current_user)
    check_board_access(board, current_user, BoardPermission.WRITE)

    new_label = Label(
        name=label_data.name,
        color=label_data.color,
        board_id=board_id
    )

    db.add(new_label)
    db.commit()
    db.refresh(new_label)
    return new_label


@router.get("/{label_id}", response_model=LabelResponse)
def get_label(
    label_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les détails d'un label spécifique.
    """
    label = db.query(Label).filter(Label.id == label_id).first()
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Label non trouvé"
        )

    # Vérifier l'accès au board
    board = label.board
    check_board_access(board, current_user, BoardPermission.READ)

    return label


@router.put("/{label_id}", response_model=LabelResponse)
def update_label(
    label_id: int,
    label_update: LabelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Met à jour un label.
    """
    label = db.query(Label).filter(Label.id == label_id).first()
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Label non trouvé"
        )

    # Vérifier l'accès au board
    board = label.board
    check_board_access(board, current_user, BoardPermission.WRITE)

    update_data = label_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(label, field, value)

    db.commit()
    db.refresh(label)
    return label


@router.delete("/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_label(
    label_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Supprime un label.
    """
    label = db.query(Label).filter(Label.id == label_id).first()
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Label non trouvé"
        )

    # Vérifier l'accès au board
    board = label.board
    check_board_access(board, current_user, BoardPermission.WRITE)

    db.delete(label)
    db.commit()
    return None
