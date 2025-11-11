"""
backend/routers/cards.py
Endpoints API pour la gestion des cartes Kanban avec glisser-déposer, étiquettes et dates d'échéance
"""

from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..database import get_db
from ..models import Card, CardLabel, Label, List, User
from ..schemas import (
    CardCreate, CardUpdate, CardResponse, 
    CardMove, LabelCreate, LabelResponse,
    CardLabelAdd, CardDueDate
)
from ..auth import get_current_user

router = APIRouter(prefix="/cards", tags=["cards"])


# ==================== CRUD DE BASE ====================

@router.get("/", response_model=List[CardResponse])
def get_cards(
    list_id: Optional[int] = None,
    board_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère toutes les cartes de l'utilisateur connecté,
    filtrées optionnellement par list_id ou board_id
    """
    query = db.query(Card).join(List).filter(List.board.has(user_id=current_user.id))
    
    if list_id:
        query = query.filter(Card.list_id == list_id)
    if board_id:
        query = query.filter(List.board_id == board_id)
    
    return query.order_by(Card.position).all()


@router.post("/", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
def create_card(
    card_data: CardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée une nouvelle carte dans une liste
    """
    # Vérifier que la liste appartient à l'utilisateur
    list_obj = db.query(List).join(List.board).filter(
        List.id == card_data.list_id,
        List.board.has(user_id=current_user.id)
    ).first()
    
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Liste non trouvée ou non autorisée"
        )
    
    # Calculer la position (ajouter à la fin)
    max_position = db.query(Card).filter(
        Card.list_id == card_data.list_id
    ).count()
    
    new_card = Card(
        **card_data.dict(exclude={"labels", "due_date"}),
        position=max_position,
        due_date=card_data.due_date
    )
    
    db.add(new_card)
    db.flush()  # Pour obtenir l'ID de la nouvelle carte
    
    # Gérer les étiquettes si fournies
    if card_data.labels:
        for label_id in card_data.labels:
            label = db.query(Label).join(Label.board).filter(
                Label.id == label_id,
                Label.board.has(user_id=current_user.id)
            ).first()
            if label:
                card_label = CardLabel(card_id=new_card.id, label_id=label_id)
                db.add(card_label)
    
    db.commit()
    db.refresh(new_card)
    return new_card


@router.get("/{card_id}", response_model=CardResponse)
def get_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère une carte spécifique par son ID
    """
    card = db.query(Card).join(Card.list).join(List.board).filter(
        Card.id == card_id,
        List.board.has(user_id=current_user.id)
    ).first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée"
        )
    
    return card


@router.put("/{card_id}", response_model=CardResponse)
def update_card(
    card_id: int,
    card_data: CardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Met à jour les informations d'une carte (titre, description, etc.)
    """
    card = db.query(Card).join(Card.list).join(List.board).filter(
        Card.id == card_id,
        List.board.has(user_id=current_user.id)
    ).first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée ou non autorisée"
        )
    
    # Mettre à jour les champs
    for field, value in card_data.dict(exclude_unset=True, exclude={"labels"}).items():
        setattr(card, field, value)
    
    db.commit()
    db.refresh(card)
    return card


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Supprime une carte et ses dépendances (étiquettes, pièces jointes, etc.)
    """
    card = db.query(Card).join(Card.list).join(List.board).filter(
        Card.id == card_id,
        List.board.has(user_id=current_user.id)
    ).first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée ou non autorisée"
        )
    
    # Supprimer les relations CardLabel
    db.query(CardLabel).filter(CardLabel.card_id == card_id).delete()
    
    # Supprimer la carte
    db.delete(card)
    db.commit()
    
    return {"message": "Carte supprimée avec succès"}


# ==================== GLISSER-DÉPOSER ====================

@router.put("/{card_id}/move", response_model=CardResponse)
def move_card(
    card_id: int,
    move_data: CardMove,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Déplace une carte entre listes et/ou change sa position (glisser-déposer)
    """
    card = db.query(Card).join(Card.list).join(List.board).filter(
        Card.id == card_id,
        List.board.has(user_id=current_user.id)
    ).first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée ou non autorisée"
        )
    
    # Vérifier que la liste de destination existe et appartient à l'utilisateur
    target_list = db.query(List).join(List.board).filter(
        List.id == move_data.target_list_id,
        List.board.has(user_id=current_user.id)
    ).first()
    
    if not target_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Liste de destination non trouvée"
        )
    
    # Si la carte reste dans la même liste
    if card.list_id == move_data.target_list_id:
        # Réorganiser les positions dans la même liste
        _reorder_cards_same_list(db, card, move_data.position)
    else:
        # Déplacer vers une autre liste
        _move_card_to_new_list(db, card, move_data.target_list_id, move_data.position)
    
    db.commit()
    db.refresh(card)
    return card


def _reorder_cards_same_list(db: Session, card: Card, new_position: int):
    """Réorganise les positions des cartes dans la même liste"""
    old_position = card.position
    
    if new_position == old_position:
        return
    
    if new_position < old_position:
        # Déplacer vers le haut
        db.query(Card).filter(
            Card.list_id == card.list_id,
            Card.position >= new_position,
            Card.position < old_position
        ).update({"position": Card.position + 1})
    else:
        # Déplacer vers le bas
        db.query(Card).filter(
            Card.list_id == card.list_id,
            Card.position > old_position,
            Card.position <= new_position
        ).update({"position": Card.position - 1})
    
    card.position = new_position


def _move_card_to_new_list(db: Session, card: Card, target_list_id: int, new_position: int):
    """Déplace une carte vers une nouvelle liste et réorganise les positions"""
    old_list_id = card.list_id
    old_position = card.position
    
    # Retirer la carte de l'ancienne liste (décaler les positions)
    db.query(Card).filter(
        Card.list_id == old_list_id,
        Card.position > old_position
    ).update({"position": Card.position - 1})
    
    # Ajuster la position dans la nouvelle liste
    max_position = db.query(Card).filter(
        Card.list_id == target_list_id
    ).count()
    
    if new_position is None or new_position > max_position:
        new_position = max_position
    
    # Faire de la place dans la nouvelle liste
    db.query(Card).filter(
        Card.list_id == target_list_id,
        Card.position >= new_position
    ).update({"position": Card.position + 1})
    
    # Mettre à jour la carte
    card.list_id = target_list_id
    card.position = new_position


# ==================== ÉTIQUETTES ====================

@router.get("/{card_id}/labels", response_model=List[LabelResponse])
def get_card_labels(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère toutes les étiquettes associées à une carte
    """
    card = db.query(Card).join(Card.list).join(List.board).filter(
        Card.id == card_id,
        List.board.has(user_id=current_user.id)
    ).first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée ou non autorisée"
        )
    
    return card.labels


@router.post("/{card_id}/labels", response_model=LabelResponse)
def add_label_to_card(
    card_id: int,
    label_data: CardLabelAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ajoute une étiquette existante à une carte,
    ou crée une nouvelle étiquette si label_id est None
    """
    card = db.query(Card).join(Card.list).join(List.board).filter(
        Card.id == card_id,
        List.board.has(user_id=current_user.id)
    ).first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée ou non autorisée"
        )
    
    # Si on crée une nouvelle étiquette
    if label_data.label_id is None:
        # Vérifier que le board existe et appartient à l'utilisateur
        board = card.list.board
        if board.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Non autorisé à créer des étiquettes pour ce board"
            )
        
        new_label = Label(
            name=label_data.name,
            color=label_data.color,
            board_id=board.id
        )
        db.add(new_label)
        db.flush()
        label_id = new_label.id
    else:
        # Utiliser une étiquette existante
        label_id = label_data.label_id
        label = db.query(Label).join(Label.board).filter(
            Label.id == label_id,
            Label.board.has(user_id=current_user.id)
        ).first()
        
        if not label:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Étiquette non trouvée ou non autorisée"
            )
    
    # Vérifier que l'étiquette n'est pas déjà associée
    existing = db.query(CardLabel).filter(
        CardLabel.card_id == card_id,
        CardLabel.label_id == label_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette étiquette est déjà associée à la carte"
        )
    
    # Ajouter l'étiquette à la carte
    card_label = CardLabel(card_id=card_id, label_id=label_id)
    db.add(card_label)
    db.commit()
    
    return db.query(Label).get(label_id)


@router.delete("/{card_id}/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_label_from_card(
    card_id: int,
    label_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Supprime une étiquette d'une carte
    """
    card = db.query(Card).join(Card.list).join(List.board).filter(
        Card.id == card_id,
        List.board.has(user_id=current_user.id)
    ).first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée ou non autorisée"
        )
    
    card_label = db.query(CardLabel).filter(
        CardLabel.card_id == card_id,
        CardLabel.label_id == label_id
    ).first()
    
    if not card_label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Étiquette non associée à cette carte"
        )
    
    db.delete(card_label)
    db.commit()
    
    return {"message": "Étiquette retirée avec succès"}


# ==================== DATES D'ÉCHÉANCE ====================

@router.put("/{card_id}/due-date", response_model=CardResponse)
def set_due_date(
    card_id: int,
    due_date_data: CardDueDate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Définit ou met à jour la date d'échéance d'une carte
    """
    card = db.query(Card).join(Card.list).join(List.board).filter(
        Card.id == card_id,
        List.board.has(user_id=current_user.id)
    ).first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée ou non autorisée"
        )
    
    # Valider que la date n'est pas dans le passé (optionnel, peut être désactivé)
    if due_date_data.due_date and due_date_data.due_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La date d'échéance ne peut pas être dans le passé"
        )
    
    card.due_date = due_date_data.due_date
    db.commit()
    db.refresh(card)
    return card


@router.delete("/{card_id}/due-date", status_code=status.HTTP_204_NO_CONTENT)
def remove_due_date(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Supprime la date d'échéance d'une carte
    """
    card = db.query(Card).join(Card.list).join(List.board).filter(
        Card.id == card_id,
        List.board.has(user_id=current_user.id)
    ).first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carte non trouvée ou non autorisée"
        )
    
    card.due_date = None
    db.commit()
    
    return {"message": "Date d'échéance supprimée avec succès"}


# ==================== RECHERCHE & FILTRES ====================

@router.get("/filter/by-label/{label_id}", response_model=List[CardResponse])
def get_cards_by_label(
    label_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère toutes les cartes ayant une étiquette spécifique
    """
    # Vérifier que l'étiquette existe et appartient à l'utilisateur
    label = db.query(Label).join(Label.board).filter(
        Label.id == label_id,
        Label.board.has(user_id=current_user.id)
    ).first()
    
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Étiquette non trouvée ou non autorisée"
        )
    
    return db.query(Card).join(Card.labels).filter(
        Label.id == label_id
    ).order_by(Card.due_date, Card.position).all()


@router.get("/filter/overdue", response_model=List[CardResponse])
def get_overdue_cards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère toutes les cartes en retard (due_date < aujourd'hui)
    """
    today = date.today()
    
    return db.query(Card).join(Card.list).join(List.board).filter(
        List.board.has(user_id=current_user.id),
        Card.due_date.isnot(None),
        Card.due_date < today
    ).order_by(Card.due_date).all()


@router.get("/filter/due-this-week", response_model=List[CardResponse])
def get_cards_due_this_week(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère toutes les cartes dont la date d'échéance est cette semaine
    """
    today = date.today()
    week_end = date.fromordinal(today.toordinal() + 7)
    
    return db.query(Card).join(Card.list).join(List.board).filter(
        List.board.has(user_id=current_user.id),
        Card.due_date.isnot(None),
        Card.due_date >= today,
        Card.due_date <= week_end
    ).order_by(Card.due_date).all()