# backend/services/board_service.py
"""
Service de gestion des tableaux avec logique de permissions et collaboration.
Gère l'accès aux tableaux, les rôles des membres et les opérations autorisées.
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.models.board import Board, BoardMember
from backend.models.user import User
from backend.core.exceptions import PermissionDeniedError, ResourceNotFoundError


class BoardRole(str, Enum):
    """Rôles possibles pour les membres d'un tableau."""
    OWNER = "owner"          # Peut tout faire + gérer les membres
    EDITOR = "editor"        # Peut modifier le tableau et son contenu
    VIEWER = "viewer"        # Peut uniquement voir le tableau


class BoardService:
    """Service métier pour les opérations sur les tableaux."""
    
    # Permissions par rôle pour chaque action
    PERMISSIONS_MAP = {
        'create': [BoardRole.OWNER, BoardRole.EDITOR],
        'read': [BoardRole.OWNER, BoardRole.EDITOR, BoardRole.VIEWER],
        'update': [BoardRole.OWNER, BoardRole.EDITOR],
        'delete': [BoardRole.OWNER],
        'manage_members': [BoardRole.OWNER],
    }
    
    @staticmethod
    def _check_permission(
        db: Session, 
        board_id: int, 
        user_id: int, 
        action: str
    ) -> BoardMember:
        """
        Vérifie si un utilisateur a la permission d'effectuer une action sur un tableau.
        
        Args:
            db: Session database
            board_id: ID du tableau
            user_id: ID de l'utilisateur
            action: Type d'action (create, read, update, delete, manage_members)
        
        Returns:
            BoardMember: L'association board-member si permission accordée
            
        Raises:
            PermissionDeniedError: Si l'utilisateur n'a pas la permission
            ResourceNotFoundError: Si le tableau n'existe pas
        """
        board_member = db.query(BoardMember).filter(
            and_(
                BoardMember.board_id == board_id,
                BoardMember.user_id == user_id
            )
        ).first()
        
        if not board_member:
            # Vérifier si le tableau existe
            board = db.query(Board).filter(Board.id == board_id).first()
            if not board:
                raise ResourceNotFoundError(f"Tableau {board_id} non trouvé")
            raise PermissionDeniedError(
                f"Accès refusé au tableau {board_id} pour l'utilisateur {user_id}"
            )
        
        required_roles = BoardService.PERMISSIONS_MAP.get(action, [])
        if board_member.role not in required_roles:
            raise PermissionDeniedError(
                f"Permission insuffisante. Rôle requis: {required_roles}"
            )
        
        return board_member
    
    @staticmethod
    def create_board(
        db: Session,
        user_id: int,
        title: str,
        description: Optional[str] = None,
        is_public: bool = False
    ) -> Board:
        """
        Crée un nouveau tableau avec l'utilisateur comme propriétaire.
        
        Args:
            db: Session database
            user_id: ID du créateur (devient owner)
            title: Titre du tableau
            description: Description optionnelle
            is_public: Si le tableau est public (visible par tous)
        
        Returns:
            Board: Le tableau créé
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ResourceNotFoundError(f"Utilisateur {user_id} non trouvé")
        
        # Créer le tableau
        board = Board(
            title=title,
            description=description,
            is_public=is_public,
            created_at=datetime.utcnow()
        )
        db.add(board)
        db.flush()  # Pour obtenir l'ID du board
        
        # Ajouter le créateur comme owner
        board_member = BoardMember(
            board_id=board.id,
            user_id=user_id,
            role=BoardRole.OWNER
        )
        db.add(board_member)
        db.commit()
        db.refresh(board)
        
        return board
    
    @staticmethod
    def get_board(
        db: Session,
        board_id: int,
        user_id: int
    ) -> Board:
        """
        Récupère un tableau si l'utilisateur y a accès.
        
        Args:
            db: Session database
            board_id: ID du tableau
            user_id: ID de l'utilisateur demandant l'accès
        
        Returns:
            Board: Le tableau demandé
            
        Raises:
            PermissionDeniedError: Si accès refusé
        """
        board = db.query(Board).filter(Board.id == board_id).first()
        if not board:
            raise ResourceNotFoundError(f"Tableau {board_id} non trouvé")
        
        # Si public, pas besoin de vérifier les permissions
        if board.is_public:
            return board
        
        # Vérifier les permissions pour les tableaux privés
        BoardService._check_permission(db, board_id, user_id, 'read')
        return board
    
    @staticmethod
    def get_user_boards(
        db: Session,
        user_id: int,
        include_public: bool = True
    ) -> List[Board]:
        """
        Récupère tous les tableaux accessibles par un utilisateur.
        
        Args:
            db: Session database
            user_id: ID de l'utilisateur
            include_public: Inclure les tableaux publics
        
        Returns:
            List[Board]: Liste des tableaux accessibles
        """
        query = db.query(Board).join(
            BoardMember,
            BoardMember.board_id == Board.id
        ).filter(BoardMember.user_id == user_id)
        
        if include_public:
            query = query.union(
                db.query(Board).filter(Board.is_public == True)
            )
        
        return query.all()
    
    @staticmethod
    def update_board(
        db: Session,
        board_id: int,
        user_id: int,
        updates: Dict[str, Any]
    ) -> Board:
        """
        Met à jour un tableau après vérification des permissions.
        
        Args:
            db: Session database
            board_id: ID du tableau
            user_id: ID de l'utilisateur effectuant la modification
            updates: Dictionnaire des champs à mettre à jour
        
        Returns:
            Board: Le tableau mis à jour
        """
        # Vérifier permissions
        BoardService._check_permission(db, board_id, user_id, 'update')
        
        # Récupérer et mettre à jour
        board = db.query(Board).filter(Board.id == board_id).first()
        if not board:
            raise ResourceNotFoundError(f"Tableau {board_id} non trouvé")
        
        # Mettre à jour les champs autorisés
        allowed_fields = ['title', 'description', 'is_public']
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(board, field, value)
        
        board.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(board)
        
        return board
    
    @staticmethod
    def delete_board(
        db: Session,
        board_id: int,
        user_id: int
    ) -> None:
        """
        Supprime un tableau (réservé au propriétaire).
        
        Args:
            db: Session database
            board_id: ID du tableau
            user_id: ID de l'utilisateur demandant la suppression
        """
        # Vérifier permissions (seul owner peut supprimer)
        BoardService._check_permission(db, board_id, user_id, 'delete')
        
        board = db.query(Board).filter(Board.id == board_id).first()
        if not board:
            raise ResourceNotFoundError(f"Tableau {board_id} non trouvé")
        
        db.delete(board)
        db.commit()
    
    @staticmethod
    def add_collaborator(
        db: Session,
        board_id: int,
        current_user_id: int,
        target_user_id: int,
        role: BoardRole = BoardRole.VIEWER
    ) -> BoardMember:
        """
        Ajoute un collaborateur à un tableau.
        
        Args:
            db: Session database
            board_id: ID du tableau
            current_user_id: ID de l'utilisateur effectuant l'action
            target_user_id: ID du nouvel utilisateur à ajouter
            role: Rôle à attribuer
        
        Returns:
            BoardMember: La nouvelle association créée
        """
        # Vérifier permissions (seul owner peut ajouter des membres)
        BoardService._check_permission(db, board_id, current_user_id, 'manage_members')
        
        # Vérifier que l'utilisateur cible existe
        target_user = db.query(User).filter(User.id == target_user_id).first()
        if not target_user:
            raise ResourceNotFoundError(f"Utilisateur cible {target_user_id} non trouvé")
        
        # Vérifier qu'il n'est pas déjà membre
        existing = db.query(BoardMember).filter(
            and_(
                BoardMember.board_id == board_id,
                BoardMember.user_id == target_user_id
            )
        ).first()
        
        if existing:
            raise ValueError(
                f"L'utilisateur {target_user_id} est déjà membre du tableau {board_id}"
            )
        
        # Ajouter le collaborateur
        board_member = BoardMember(
            board_id=board_id,
            user_id=target_user_id,
            role=role,
            created_at=datetime.utcnow()
        )
        db.add(board_member)
        db.commit()
        db.refresh(board_member)
        
        return board_member
    
    @staticmethod
    def update_collaborator_role(
        db: Session,
        board_id: int,
        current_user_id: int,
        target_user_id: int,
        new_role: BoardRole
    ) -> BoardMember:
        """
        Modifie le rôle d'un collaborateur.
        
        Args:
            db: Session database
            board_id: ID du tableau
            current_user_id: ID de l'utilisateur effectuant l'action
            target_user_id: ID du collaborateur à modifier
            new_role: Nouveau rôle à attribuer
        
        Returns:
            BoardMember: L'association mise à jour
        """
        # Vérifier permissions (seul owner peut modifier les rôles)
        BoardService._check_permission(db, board_id, current_user_id, 'manage_members')
        
        # Récupérer le membre à modifier
        board_member = db.query(BoardMember).filter(
            and_(
                BoardMember.board_id == board_id,
                BoardMember.user_id == target_user_id
            )
        ).first()
        
        if not board_member:
            raise ResourceNotFoundError(
                f"L'utilisateur {target_user_id} n'est pas membre du tableau {board_id}"
            )
        
        # Empêcher de modifier le rôle du owner
        if board_member.role == BoardRole.OWNER:
            raise PermissionDeniedError("Impossible de modifier le rôle du propriétaire")
        
        board_member.role = new_role
        board_member.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(board_member)
        
        return board_member
    
    @staticmethod
    def remove_collaborator(
        db: Session,
        board_id: int,
        current_user_id: int,
        target_user_id: int
    ) -> None:
        """
        Supprime un collaborateur d'un tableau.
        
        Args:
            db: Session database
            board_id: ID du tableau
            current_user_id: ID de l'utilisateur effectuant l'action
            target_user_id: ID du collaborateur à retirer
        """
        # Vérifier permissions (seul owner peut retirer des membres)
        BoardService._check_permission(db, board_id, current_user_id, 'manage_members')
        
        # Récupérer le membre à supprimer
        board_member = db.query(BoardMember).filter(
            and_(
                BoardMember.board_id == board_id,
                BoardMember.user_id == target_user_id
            )
        ).first()
        
        if not board_member:
            raise ResourceNotFoundError(
                f"L'utilisateur {target_user_id} n'est pas membre du tableau {board_id}"
            )
        
        # Empêcher de retirer le owner
        if board_member.role == BoardRole.OWNER:
            raise PermissionDeniedError("Impossible de retirer le propriétaire du tableau")
        
        db.delete(board_member)
        db.commit()
    
    @staticmethod
    def get_board_members(
        db: Session,
        board_id: int,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        Récupère la liste des membres d'un tableau.
        
        Args:
            db: Session database
            board_id: ID du tableau
            user_id: ID de l'utilisateur demandant la liste
        
        Returns:
            List[Dict]: Liste des membres avec leurs infos
        """
        # Vérifier que l'utilisateur a accès au tableau
        BoardService._check_permission(db, board_id, user_id, 'read')
        
        members = db.query(
            BoardMember, User
        ).join(
            User, BoardMember.user_id == User.id
        ).filter(
            BoardMember.board_id == board_id
        ).all()
        
        return [
            {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "role": member.role.value,
                "joined_at": member.created_at
            }
            for member, user in members
        ]