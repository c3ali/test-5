"""
backend/core/permissions.py
Permission checking utilities for Kanban boards
"""

from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from enum import Enum

from backend.models import User, Board


class BoardPermission(str, Enum):
    """Board permission levels"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


def check_board_access(
    board: Board,
    user: User,
    required_permission: BoardPermission = BoardPermission.READ
) -> bool:
    """
    Check if a user has access to a board.

    Args:
        board: The board to check access for
        user: The user requesting access
        required_permission: The permission level required

    Returns:
        True if user has access, False otherwise
    """
    # Owner always has full access
    if board.owner_id == user.id:
        return True

    # Admin users have full access
    if user.role == "admin":
        return True

    # Check if user is a collaborator/member
    if user in board.members:
        # For now, all members have read and write access
        # You can extend this to have different permission levels per member
        return required_permission in [BoardPermission.READ, BoardPermission.WRITE]

    return False


def check_board_ownership(board: Board, user: User) -> bool:
    """
    Check if a user is the owner of a board.

    Args:
        board: The board to check
        user: The user to check

    Returns:
        True if user is the owner or admin, False otherwise
    """
    # Owner has ownership rights
    if board.owner_id == user.id:
        return True

    # Admin users can act as owners
    if user.role == "admin":
        return True

    return False


def require_board_access(
    board: Board,
    user: User,
    required_permission: BoardPermission = BoardPermission.READ
) -> None:
    """
    Require that a user has access to a board, raise exception if not.

    Args:
        board: The board to check access for
        user: The user requesting access
        required_permission: The permission level required

    Raises:
        HTTPException: If user doesn't have required access
    """
    if not check_board_access(board, user, required_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à ce board"
        )


def require_board_ownership(board: Board, user: User) -> None:
    """
    Require that a user is the owner of a board, raise exception if not.

    Args:
        board: The board to check
        user: The user to check

    Raises:
        HTTPException: If user is not the owner
    """
    if not check_board_ownership(board, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul le propriétaire du board peut effectuer cette action"
        )


def get_board_or_404(db: Session, board_id: int, user: Optional[User] = None) -> Board:
    """
    Get a board by ID or raise 404.
    Optionally check if user has access.

    Args:
        db: Database session
        board_id: The board ID
        user: Optional user to check access for

    Returns:
        Board object

    Raises:
        HTTPException: If board not found or user doesn't have access
    """
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board non trouvé"
        )

    if user:
        require_board_access(board, user, BoardPermission.READ)

    return board


def check_card_access(card, user: User) -> bool:
    """
    Check if a user has access to a card (via its list's board).

    Args:
        card: The card to check access for
        user: The user requesting access

    Returns:
        True if user has access, False otherwise
    """
    # Access to card is determined by access to its board
    board = card.list.board
    return check_board_access(board, user, BoardPermission.READ)


def require_card_access(card, user: User) -> None:
    """
    Require that a user has access to a card, raise exception if not.

    Args:
        card: The card to check access for
        user: The user requesting access

    Raises:
        HTTPException: If user doesn't have access
    """
    if not check_card_access(card, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à cette carte"
        )


def check_list_access(list_obj, user: User) -> bool:
    """
    Check if a user has access to a list (via its board).

    Args:
        list_obj: The list to check access for
        user: The user requesting access

    Returns:
        True if user has access, False otherwise
    """
    # Access to list is determined by access to its board
    return check_board_access(list_obj.board, user, BoardPermission.READ)


def require_list_access(list_obj, user: User) -> None:
    """
    Require that a user has access to a list, raise exception if not.

    Args:
        list_obj: The list to check access for
        user: The user requesting access

    Raises:
        HTTPException: If user doesn't have access
    """
    if not check_list_access(list_obj, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à cette liste"
        )
