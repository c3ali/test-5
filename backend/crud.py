"""
backend/crud.py
Opérations CRUD de base pour toutes les entités du modèle de données.
Implémente un système générique avec SQLAlchemy async.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from datetime import datetime

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeMeta

from .database import get_async_session
from .models.base import Base

ModelType = TypeVar("ModelType", bound=DeclarativeMeta)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Classe de base pour les opérations CRUD avec des méthodes génériques.
    
    Args:
        model: La classe du modèle SQLAlchemy
    """
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Récupère une entité par son ID.
        
        Args:
            db: Session de base de données
            id: ID de l'entité
            
        Returns:
            L'entité si trouvée, None sinon
        """
        result = await db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """
        Récupère plusieurs entités avec support du filtrage et du tri.
        
        Args:
            db: Session de base de données
            skip: Nombre d'entités à ignorer (offset)
            limit: Nombre maximum d'entités à récupérer
            filters: Dictionnaire de filtres {champ: valeur}
            order_by: Nom du champ pour le tri
            
        Returns:
            Liste des entités
        """
        query = select(self.model)
        
        # Application des filtres
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        # Tri
        if order_by and hasattr(self.model, order_by.lstrip('-')):
            field_name = order_by.lstrip('-')
            field = getattr(self.model, field_name)
            if order_by.startswith('-'):
                field = field.desc()
            query = query.order_by(field)
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_with_pagination(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Récupère des entités avec informations de pagination.
        
        Returns:
            Dictionnaire avec items, total, page, per_page
        """
        skip = (page - 1) * per_page
        
        # Récupère les données
        items = await self.get_multi(
            db, skip=skip, limit=per_page,
            filters=filters, order_by=order_by
        )
        
        # Compte total
        total = await self.count(db, filters=filters)
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
    
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CreateSchemaType,
        created_by: Optional[str] = None,
        commit: bool = True
    ) -> ModelType:
        """
        Crée une nouvelle entité.
        
        Args:
            db: Session de base de données
            obj_in: Données de création (Pydantic schema)
            created_by: Utilisateur qui crée l'entité (pour audit)
            commit: Si True, commit immédiatement
            
        Returns:
            L'entité créée
        """
        # Convertit Pydantic en dict, en excluant les champs None
        obj_data = obj_in.model_dump(exclude_unset=True)
        
        # Ajoute les métadonnées d'audit si présentes
        if hasattr(self.model, 'created_by') and created_by:
            obj_data['created_by'] = created_by
        if hasattr(self.model, 'created_at'):
            obj_data['created_at'] = datetime.utcnow()
        
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        
        if commit:
            await db.commit()
            await db.refresh(db_obj)
        
        return db_obj
    
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        updated_by: Optional[str] = None,
        commit: bool = True
    ) -> ModelType:
        """
        Met à jour une entité existante.
        
        Args:
            db_obj: Entité à mettre à jour
            obj_in: Données de mise à jour (Pydantic schema ou dict)
            updated_by: Utilisateur qui modifie l'entité
            commit: Si True, commit immédiatement
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        # Mise à jour des champs
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        # Mise à jour des métadonnées d'audit
        if hasattr(self.model, 'updated_by') and updated_by:
            db_obj.updated_by = updated_by
        if hasattr(self.model, 'updated_at'):
            db_obj.updated_at = datetime.utcnow()
        
        if commit:
            await db.commit()
            await db.refresh(db_obj)
        
        return db_obj
    
    async def delete(
        self,
        db: AsyncSession,
        *,
        id: Any,
        commit: bool = True
    ) -> Optional[ModelType]:
        """
        Supprime une entité par son ID.
        
        Returns:
            L'entité supprimée si trouvée, None sinon
        """
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            if commit:
                await db.commit()
        return obj
    
    async def count(
        self,
        db: AsyncSession,
        *,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Compte le nombre d'entités correspondant aux filtres.
        """
        query = select(func.count()).select_from(self.model)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def exists(
        self,
        db: AsyncSession,
        id: Any
    ) -> bool:
        """
        Vérifie si une entité existe par son ID.
        """
        result = await self.get(db, id)
        return result is not None
    
    async def get_by_field(
        self,
        db: AsyncSession,
        field: str,
        value: Any
    ) -> Optional[ModelType]:
        """
        Récupère une entité par un champ spécifique (unique).
        """
        if not hasattr(self.model, field):
            raise ValueError(f"Le champ {field} n'existe pas sur le modèle")
        
        query = select(self.model).where(getattr(self.model, field) == value)
        result = await db.execute(query)
        return result.scalar_one_or_none()


# Exemple d'implémentation pour des entités spécifiques
# À adapter selon vos modèles et schémas Pydantic

# from .models.user import User
# from .schemas.user import UserCreate, UserUpdate
# 
# class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
#     def __init__(self):
#         super().__init__(User)
#     
#     # Méthodes spécifiques si nécessaire
#     async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
#         return await self.get_by_field(db, "email", email)
# 
# user = CRUDUser()

# from .models.post import Post
# from .schemas.post import PostCreate, PostUpdate
# 
# post = CRUDBase[Post, PostCreate, PostUpdate](Post)


# Factory pour créer les instances CRUD automatiquement
def get_crud_instance(
    model: Type[ModelType],
    create_schema: Type[CreateSchemaType],
    update_schema: Type[UpdateSchemaType]
) -> CRUDBase[ModelType, CreateSchemaType, UpdateSchemaType]:
    """
    Factory pour créer une instance CRUD pour un modèle donné.
    """
    return CRUDBase[model, create_schema, update_schema](model)


# Dictionnaire centralisé des instances CRUD
# À populiser dans main.py ou au démarrage de l'application
crud_instances: Dict[str, CRUDBase] = {}
```

### Exemple d'utilisation dans `main.py` ou `deps.py`

```python
# Pour créer les instances CRUD automatiquement pour tous vos modèles
from .models.user import User
from .schemas.user import UserCreate, UserUpdate
from .models.post import Post
from .schemas.post import PostCreate, PostUpdate

# Instanciation
user_crud = CRUDUser()
# ou
post_crud = get_crud_instance(Post, PostCreate, PostUpdate)

# Stockage dans le dictionnaire
crud_instances["user"] = user_crud
crud_instances["post"] = post_crud
```

### Utilisation dans les endpoints FastAPI

```python
from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .crud import user_crud
from .database import get_async_session

router = APIRouter()

@router.get("/users/{user_id}")
async def read_user(user_id: int, db: AsyncSession = Depends(get_async_session)):
    user = await user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user

@router.get("/users")
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session)
):
    return await user_crud.get_multi(db, skip=skip, limit=limit)