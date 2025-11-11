"""
Endpoints API pour la gestion des étiquettes (labels)
Permet les opérations CRUD sur les étiquettes utilisables pour catégoriser les images
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.database import get_db
from backend.models.label import Label
from backend.schemas.label import LabelCreate, LabelUpdate, LabelInDB
from backend.dependencies.auth import get_current_active_user
from backend.models.user import User

router = APIRouter(
    prefix="/labels",
    tags=["étiquettes"],
    dependencies=[Depends(get_current_active_user)]
)


@router.get(
    "/",
    response_model=List[LabelInDB],
    summary="Récupérer toutes les étiquettes",
    description="Retourne la liste de toutes les étiquettes disponibles"
)
async def get_labels(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les étiquettes avec pagination
    """
    labels = db.query(Label).offset(skip).limit(limit).all()
    return labels


@router.get(
    "/{label_id}",
    response_model=LabelInDB,
    summary="Récupérer une étiquette par ID",
    description="Retourne les détails d'une étiquette spécifique"
)
async def get_label(
    label_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère une étiquette par son identifiant
    """
    label = db.query(Label).filter(Label.id == label_id).first()
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Étiquette avec l'ID {label_id} non trouvée"
        )
    return label


@router.post(
    "/",
    response_model=LabelInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle étiquette",
    description="Crée une nouvelle étiquette avec les données fournies"
)
async def create_label(
    label_data: LabelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Crée une nouvelle étiquette
    """
    # Vérifier si l'étiquette existe déjà
    existing_label = db.query(Label).filter(Label.name == label_data.name).first()
    if existing_label:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Une étiquette avec le nom '{label_data.name}' existe déjà"
        )
    
    try:
        db_label = Label(**label_data.dict())
        db.add(db_label)
        db.commit()
        db.refresh(db_label)
        return db_label
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création de l'étiquette"
        )


@router.put(
    "/{label_id}",
    response_model=LabelInDB,
    summary="Mettre à jour une étiquette",
    description="Met à jour les informations d'une étiquette existante"
)
async def update_label(
    label_id: int,
    label_data: LabelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Met à jour une étiquette existante
    """
    db_label = db.query(Label).filter(Label.id == label_id).first()
    if not db_label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Étiquette avec l'ID {label_id} non trouvée"
        )
    
    # Vérifier les conflits de nom
    if label_data.name:
        existing_label = db.query(Label).filter(
            Label.name == label_data.name,
            Label.id != label_id
        ).first()
        if existing_label:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Une étiquette avec le nom '{label_data.name}' existe déjà"
            )
    
    try:
        update_data = label_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_label, field, value)
        
        db.commit()
        db.refresh(db_label)
        return db_label
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour de l'étiquette"
        )


@router.delete(
    "/{label_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une étiquette",
    description="Supprime définitivement une étiquette de la base de données"
)
async def delete_label(
    label_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Supprime une étiquette
    """
    db_label = db.query(Label).filter(Label.id == label_id).first()
    if not db_label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Étiquette avec l'ID {label_id} non trouvée"
        )
    
    try:
        db.delete(db_label)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer l'étiquette car elle est utilisée par une ou plusieurs images"
        )


@router.get(
    "/search/",
    response_model=List[LabelInDB],
    summary="Rechercher des étiquettes",
    description="Recherche des étiquettes par nom avec filtrage"
)
async def search_labels(
    name: Optional[str] = None,
    color: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Recherche des étiquettes par nom ou couleur
    """
    query = db.query(Label)
    
    if name:
        query = query.filter(Label.name.ilike(f"%{name}%"))
    
    if color:
        query = query.filter(Label.color == color)
    
    return query.all()