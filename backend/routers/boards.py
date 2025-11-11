"""
backend/routers/boards.py
Endpoints API pour les opérations CRUD sur les tableaux et la gestion de la collaboration
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.database import get_db
from backend.models import User, Board
# TODO: Implement these schemas in backend/schemas.py
# from backend.schemas import (
#     BoardCreate,
#     BoardUpdate,
#     BoardOut,
#     CollaboratorAdd,
#     CollaboratorOut,
#     CollaboratorUpdate
# )
from backend.dependencies.auth import get_current_active_user
from backend.core.permissions import (
    check_board_access,
    check_board_ownership,
    BoardPermission
)

router = APIRouter(prefix="/boards", tags=["boards"])


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
    owned_boards = db.query(Board).filter(Board.owner_id == current_user.id).offset(skip).limit(limit).all()
    
    # Tableaux partagés avec l'utilisateur
    shared_boards = (
        db.query(Board)
        .join(BoardMember)
        .filter(BoardMember.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Fusionner et dedupliquer les résultats
    all_boards = {board.id: board for board in owned_boards + shared_boards}
    return list(all_boards.values())


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
        **board_data.dict(),
        owner_id=current_user.id
    )
    
    try:
        db.add(new_board)
        db.commit()
        db.refresh(new_board)
        return new_board
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur lors de la création du tableau"
        )


@router.get("/{board_id}", response_model=BoardOut)
def get_board(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les détails d'un tableau spécifique si l'utilisateur y a accès.
    """
    board = check_board_access(db, board_id, current_user.id, BoardPermission.READ)
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
    board = check_board_ownership(db, board_id, current_user.id)
    
    update_data = board_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(board, field, value)
    
    try:
        db.commit()
        db.refresh(board)
        return board
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur lors de la mise à jour du tableau"
        )


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Supprime un tableau et toutes ses données associées. Seul le propriétaire peut supprimer.
    """
    board = check_board_ownership(db, board_id, current_user.id)
    
    try:
        db.delete(board)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur lors de la suppression du tableau"
        )


# ==================== ENDPOINTS DE COLLABORATION ====================


@router.get("/{board_id}/collaborators", response_model=List[CollaboratorOut])
def get_board_collaborators(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère la liste des collaborateurs d'un tableau. Accessible par le propriétaire et les collaborateurs.
    """
    check_board_access(db, board_id, current_user.id, BoardPermission.READ)
    
    collaborators = (
        db.query(BoardMember, User)
        .join(User, BoardMember.user_id == User.id)
        .filter(BoardMember.board_id == board_id)
        .all()
    )
    
    return [
        CollaboratorOut(
            id=member.id,
            user_id=user.id,
            username=user.username,
            email=user.email,
            role=member.role,
            joined_at=member.joined_at
        )
        for member, user in collaborators
    ]


@router.post("/{board_id}/collaborators", response_model=CollaboratorOut)
def add_collaborator(
    board_id: int,
    collaborator_data: CollaboratorAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Ajoute un collaborateur à un tableau. Seul le propriétaire peut inviter de nouveaux collaborateurs.
    """
    check_board_ownership(db, board_id, current_user.id)
    
    # Vérifier si l'utilisateur à inviter existe
    user_to_add = db.query(User).filter(User.email == collaborator_data.email).first()
    if not user_to_add:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé avec cet email"
        )
    
    # Empêcher l'auto-invitation
    if user_to_add.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas vous ajouter en tant que collaborateur"
        )
    
    # Vérifier si l'utilisateur est déjà collaborateur
    existing_member = db.query(BoardMember).filter(
        BoardMember.board_id == board_id,
        BoardMember.user_id == user_to_add.id
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet utilisateur est déjà collaborateur de ce tableau"
        )
    
    # Créer le nouveau membre
    new_member = BoardMember(
        board_id=board_id,
        user_id=user_to_add.id,
        role=collaborator_data.role
    )
    
    try:
        db.add(new_member)
        db.commit()
        db.refresh(new_member)
        
        return CollaboratorOut(
            id=new_member.id,
            user_id=user_to_add.id,
            username=user_to_add.username,
            email=user_to_add.email,
            role=new_member.role,
            joined_at=new_member.joined_at
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur lors de l'ajout du collaborateur"
        )


@router.put("/{board_id}/collaborators/{user_id}", response_model=CollaboratorOut)
def update_collaborator_role(
    board_id: int,
    user_id: int,
    role_update: CollaboratorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Met à jour le rôle d'un collaborateur. Seul le propriétaire peut modifier les rôles.
    """
    check_board_ownership(db, board_id, current_user.id)
    
    # Vérifier que le collaborateur existe
    collaborator = db.query(BoardMember).filter(
        BoardMember.board_id == board_id,
        BoardMember.user_id == user_id
    ).first()
    
    if not collaborator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collaborateur non trouvé"
        )
    
    # Empêcher la modification du rôle du propriétaire
    board = db.query(Board).filter(Board.id == board_id).first()
    if board.owner_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de modifier le rôle du propriétaire"
        )
    
    collaborator.role = role_update.role
    
    try:
        db.commit()
        db.refresh(collaborator)
        
        user = db.query(User).filter(User.id == user_id).first()
        return CollaboratorOut(
            id=collaborator.id,
            user_id=user.id,
            username=user.username,
            email=user.email,
            role=collaborator.role,
            joined_at=collaborator.joined_at
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur lors de la mise à jour du rôle"
        )


@router.delete("/{board_id}/collaborators/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_collaborator(
    board_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retire un collaborateur d'un tableau. Seul le propriétaire peut retirer des collaborateurs.
    """
    check_board_ownership(db, board_id, current_user.id)
    
    # Vérifier que le collaborateur existe
    collaborator = db.query(BoardMember).filter(
        BoardMember.board_id == board_id,
        BoardMember.user_id == user_id
    ).first()
    
    if not collaborator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collaborateur non trouvé"
        )
    
    # Empêcher le retrait du propriétaire
    board = db.query(Board).filter(Board.id == board_id).first()
    if board.owner_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de retirer le propriétaire du tableau"
        )
    
    try:
        db.delete(collaborator)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur lors de la suppression du collaborateur"
        )