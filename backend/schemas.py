"""
backend/schemas.py
Schémas Pydantic pour la validation des données entrantes/sortantes
"""

from datetime import datetime
from typing import Optional, List, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator
from enum import Enum

# ============================================================================
# ENUMS
# ============================================================================

class RoleEnum(str, Enum):
    """Rôles utilisateur"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class ProductStatusEnum(str, Enum):
    """Statut d'un produit"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"

# ============================================================================
# MIXINS (champs communs)
# ============================================================================

class TimestampMixin(BaseModel):
    """Mixin pour les timestamps de création/mise à jour"""
    created_at: datetime = Field(description="Date de création")
    updated_at: Optional[datetime] = Field(None, description="Date de dernière modification")

# ============================================================================
# AUTHENTIFICATION
# ============================================================================

class Token(BaseModel):
    """Schéma du token JWT"""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = Field(None, description="Durée de validité en secondes")

class TokenPayload(BaseModel):
    """Payload décodé du token"""
    sub: Optional[UUID] = None
    exp: Optional[int] = None

class LoginRequest(BaseModel):
    """Requête d'authentification"""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "email": "user@example.com",
            "password": "secure_password"
        }
    })

# ============================================================================
# UTILISATEURS
# ============================================================================

class UserBase(BaseModel):
    """Champs de base pour un utilisateur"""
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    is_active: bool = True
    role: RoleEnum = RoleEnum.USER

class UserCreate(UserBase):
    """Schéma pour la création d'un utilisateur"""
    password: str = Field(min_length=8, max_length=128)

    @field_validator('password')
    @classmethod
    def password_must_be_strong(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError('Le mot de passe doit contenir au moins une majuscule')
        if not any(c.isdigit() for c in v):
            raise ValueError('Le mot de passe doit contenir au moins un chiffre')
        return v

class UserUpdate(BaseModel):
    """Schéma pour la mise à jour partielle d'un utilisateur"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    role: Optional[RoleEnum] = None

class UserRead(UserBase, TimestampMixin):
    """Schéma de lecture d'un utilisateur (sortie API)"""
    id: UUID
    model_config = ConfigDict(from_attributes=True)

class UserInDB(UserBase):
    """Schéma utilisateur tel qu'il est stocké en base"""
    id: UUID
    hashed_password: str
    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# PRODUITS (exemple de ressource)
# ============================================================================

class ProductBase(BaseModel):
    """Champs de base pour un produit"""
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: float = Field(gt=0, description="Prix en euros")
    stock: int = Field(ge=0, default=0)
    status: ProductStatusEnum = ProductStatusEnum.DRAFT

class ProductCreate(ProductBase):
    """Schéma pour la création d'un produit"""
    pass

class ProductUpdate(BaseModel):
    """Schéma pour la mise à jour partielle d'un produit"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    status: Optional[ProductStatusEnum] = None

class ProductRead(ProductBase, TimestampMixin):
    """Schéma de lecture d'un produit"""
    id: UUID
    sku: str = Field(description="Référence produit unique")
    owner_id: UUID
    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# PAGINATION
# ============================================================================

T = TypeVar('T')

class PaginationParams(BaseModel):
    """Paramètres de pagination pour les requêtes"""
    page: int = Field(ge=1, default=1, description="Numéro de page")
    size: int = Field(ge=1, le=100, default=20, description="Nombre d'items par page")

class PaginatedResponse(BaseModel, Generic[T]):
    """Réponse paginée standardisée"""
    items: List[T]
    total: int = Field(description="Nombre total d'items")
    page: int
    size: int
    pages: int = Field(description="Nombre total de pages")
    has_next: bool
    has_prev: bool

    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# RÉPONSES STANDARD
# ============================================================================

class SuccessResponse(BaseModel):
    """Réponse de succès générique"""
    success: bool = True
    message: str
    data: Optional[dict] = None

class ErrorResponse(BaseModel):
    """Réponse d'erreur standardisée"""
    success: bool = False
    error_code: str
    message: str
    details: Optional[dict] = None

class ValidationErrorResponse(ErrorResponse):
    """Réponse d'erreur de validation"""
    error_code: str = "VALIDATION_ERROR"
    errors: List[dict] = Field(description="Liste des erreurs de validation")

# ============================================================================
# HEALTH CHECK
# ============================================================================

class HealthCheck(BaseModel):
    """Schéma pour le health check"""
    status: str = Field(description="Statut du service")
    timestamp: datetime
    version: Optional[str] = None
    database: Optional[str] = None
    uptime: Optional[float] = Field(None, description="Temps de fonctionnement en secondes")

# ============================================================================
# MESSAGES (exemple)
# ============================================================================

class Message(BaseModel):
    """Schéma pour un message simple"""
    message: str
    detail: Optional[str] = None

# ============================================================================
# KANBAN - BOARDS
# ============================================================================

class BoardCreate(BaseModel):
    """Schéma pour la création d'un board"""
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    is_public: bool = False
    background_color: str = Field(default="#FFFFFF", max_length=7, pattern=r'^#[0-9A-Fa-f]{6}$')

class BoardUpdate(BaseModel):
    """Schéma pour la mise à jour d'un board"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_public: Optional[bool] = None
    background_color: Optional[str] = Field(None, max_length=7, pattern=r'^#[0-9A-Fa-f]{6}$')

class BoardOut(BaseModel):
    """Schéma de sortie pour un board"""
    id: int
    name: str
    description: Optional[str]
    is_public: bool
    background_color: str
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# KANBAN - LISTS
# ============================================================================

class ListCreate(BaseModel):
    """Schéma pour la création d'une liste"""
    name: str = Field(min_length=1, max_length=100)
    position: int = 0

class ListUpdate(BaseModel):
    """Schéma pour la mise à jour d'une liste"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    position: Optional[int] = None

class ListOut(BaseModel):
    """Schéma de sortie pour une liste"""
    id: int
    name: str
    position: int
    board_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# KANBAN - CARDS
# ============================================================================

class CardCreate(BaseModel):
    """Schéma pour la création d'une carte"""
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    position: int = 0
    due_date: Optional[datetime] = None
    is_archived: bool = False

class CardUpdate(BaseModel):
    """Schéma pour la mise à jour d'une carte"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    position: Optional[int] = None
    due_date: Optional[datetime] = None
    is_archived: Optional[bool] = None

class CardMove(BaseModel):
    """Schéma pour déplacer une carte"""
    list_id: int
    position: int

class CardOut(BaseModel):
    """Schéma de sortie pour une carte"""
    id: int
    title: str
    description: Optional[str]
    position: int
    list_id: int
    author_id: int
    due_date: Optional[datetime]
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CardLabelAdd(BaseModel):
    """Schéma pour ajouter un label à une carte"""
    label_id: int

# ============================================================================
# KANBAN - LABELS
# ============================================================================

class LabelCreate(BaseModel):
    """Schéma pour la création d'un label"""
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(max_length=7, pattern=r'^#[0-9A-Fa-f]{6}$')

class LabelUpdate(BaseModel):
    """Schéma pour la mise à jour d'un label"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, max_length=7, pattern=r'^#[0-9A-Fa-f]{6}$')

class LabelInDB(BaseModel):
    """Schéma pour un label en base de données"""
    id: int
    name: str
    color: str
    board_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LabelResponse(LabelInDB):
    """Schéma de réponse pour un label"""
    pass

# ============================================================================
# CONFIGURATION GLOBALE
# ============================================================================

class Config:
    """Configuration globale des modèles"""
    # Utiliser enum_values pour afficher les valeurs des enums dans les réponses
    use_enum_values = True
    # Valider par défaut à l'assignation
    validate_assignment = True
    # Protection contre les types arbitraires
    arbitrary_types_allowed = False
