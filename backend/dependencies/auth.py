"""
backend/dependencies/auth.py
FastAPI authentication dependencies
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID

from backend.database import get_db
from backend.models import User
from backend.core.security import verify_token

# Security scheme for JWT token
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Supports demo mode with token 'demo-token-no-auth-required'.

    Args:
        credentials: JWT token from Authorization header
        db: Database session

    Returns:
        User object if authenticated

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    # Check for demo mode token
    if token == "demo-token-no-auth-required":
        # Return a fake demo user without database access
        demo_user = User()
        demo_user.id = UUID("00000000-0000-0000-0000-000000000001")
        demo_user.email = "demo@kanban.com"
        demo_user.first_name = "Démo"
        demo_user.last_name = "Utilisateur"
        demo_user.role = "user"
        demo_user.is_active = True
        demo_user.hashed_password = ""
        return demo_user

    # Verify and decode the token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID from token payload
    user_id_str: Optional[str] = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide: identifiant utilisateur manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide: identifiant utilisateur incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur non trouvé",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get the current active user.

    Args:
        current_user: Current authenticated user

    Returns:
        User object if active

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utilisateur inactif"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency to get the current admin user.

    Args:
        current_user: Current active user

    Returns:
        User object if admin

    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Privilèges administrateur requis"
        )
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to optionally get the current user.
    Returns None if no token is provided or token is invalid.

    Supports demo mode with token 'demo-token-no-auth-required'.

    Args:
        credentials: Optional JWT token from Authorization header
        db: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    if not credentials:
        return None

    token = credentials.credentials

    # Check for demo mode token
    if token == "demo-token-no-auth-required":
        demo_user = User()
        demo_user.id = UUID("00000000-0000-0000-0000-000000000001")
        demo_user.email = "demo@kanban.com"
        demo_user.first_name = "Démo"
        demo_user.last_name = "Utilisateur"
        demo_user.role = "user"
        demo_user.is_active = True
        demo_user.hashed_password = ""
        return demo_user

    payload = verify_token(token)
    if not payload:
        return None

    user_id_str: Optional[str] = payload.get("sub")
    if not user_id_str:
        return None

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        return None

    user = db.query(User).filter(User.id == user_id).first()
    return user
