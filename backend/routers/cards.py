"""
backend/routers/cards.py
Endpoints API pour les opérations CRUD sur les cartes Kanban
"""

from typing import List as ListType
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, List, Card, Label
from backend.schemas import CardCreate, CardUpdate, CardOut, CardMove, CardLabelAdd
from backend.dependencies.auth import get_current_active_user
from backend.core.permissions import check_board_access, BoardPermission

router = APIRouter()


@router.get("/list/{list_id}/cards", response_model=ListType[CardOut])
def get_list_cards(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère toutes les cartes d'une liste.
    """
    list_obj = db.query(List).filter(List.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Liste non trouvée"
        )

    # Vérifier l'accès au board
    check_board_access(list_obj.board, current_user, BoardPermission.READ)

    cards = db.query(Card).filter(Card.list_id == list_id).order_by(Card.position).all()
    return cards


@router.post("/list/{list_id}/cards", response_model=CardOut, status_code=status.HTTP_201_CREATED)
def create_card(
    list_id: int,
    card_data: CardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Crée une nouvelle carte dans une liste.
    """
    list_obj = db.query(List).filter(List.id == list_id).first()
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Liste non trouvée"
        )

    # Vérifier l'accès au board
    check_board_access(list_obj.board, current_user, BoardPermission.WRITE)

    new_card = Card(
        title=card_data.title,
        description=card_data.description,
        position=card_data.position,
        due_date=card_data.due_date,
        is_archived=card_data.is_archived,
        list_id=list_id,
        author_id=current_user.id
    )

    db.add(new_card)
    db.commit()
    db.refresh(new_card)
    return new_card


@router.get("/{card_id}", response_model=CardOut)
def get_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les détails d'une carte spécifique.
    """
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée"
        )

    # Vérifier l'accès au board via la liste
    check_board_access(card.list.board, current_user, BoardPermission.READ)

    return card


@router.put("/{card_id}", response_model=CardOut)
def update_card(
    card_id: int,
    card_update: CardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Met à jour une carte.
    """
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée"
        )

    # Vérifier l'accès au board via la liste
    check_board_access(card.list.board, current_user, BoardPermission.WRITE)

    update_data = card_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(card, field, value)

    db.commit()
    db.refresh(card)
    return card


@router.post("/{card_id}/move", response_model=CardOut)
def move_card(
    card_id: int,
    move_data: CardMove,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Déplace une carte vers une autre liste.
    """
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée"
        )

    # Vérifier l'accès au board source
    check_board_access(card.list.board, current_user, BoardPermission.WRITE)

    # Vérifier que la liste de destination existe
    new_list = db.query(List).filter(List.id == move_data.list_id).first()
    if not new_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Liste de destination non trouvée"
        )

    # Vérifier l'accès au board de destination
    check_board_access(new_list.board, current_user, BoardPermission.WRITE)

    # Déplacer la carte
    card.list_id = move_data.list_id
    card.position = move_data.position

    db.commit()
    db.refresh(card)
    return card


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Supprime une carte.
    """
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée"
        )

    # Vérifier l'accès au board via la liste
    check_board_access(card.list.board, current_user, BoardPermission.WRITE)

    db.delete(card)
    db.commit()
    return None


@router.post("/{card_id}/labels", response_model=CardOut)
def add_label_to_card(
    card_id: int,
    label_data: CardLabelAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Ajoute un label à une carte.
    """
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée"
        )

    # Vérifier l'accès au board
    check_board_access(card.list.board, current_user, BoardPermission.WRITE)

    # Vérifier que le label existe et appartient au même board
    label = db.query(Label).filter(Label.id == label_data.label_id).first()
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Label non trouvé"
        )

    if label.board_id != card.list.board_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le label n'appartient pas au même board que la carte"
        )

    # Ajouter le label s'il n'est pas déjà présent
    if label not in card.labels:
        card.labels.append(label)
        db.commit()
        db.refresh(card)

    return card


@router.delete("/{card_id}/labels/{label_id}", response_model=CardOut)
def remove_label_from_card(
    card_id: int,
    label_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retire un label d'une carte.
    """
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée"
        )

    # Vérifier l'accès au board
    check_board_access(card.list.board, current_user, BoardPermission.WRITE)

    # Trouver et retirer le label
    label = db.query(Label).filter(Label.id == label_id).first()
    if label and label in card.labels:
        card.labels.remove(label)
        db.commit()
        db.refresh(card)

    return card
