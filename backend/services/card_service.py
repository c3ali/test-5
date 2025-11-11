"""
Service de logique métier pour la gestion des cartes (tickets)
Inclut la gestion des notifications et de l'historique des modifications
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from models.card import Card, CardHistory, CardComment
from models.board import Board, BoardColumn
from models.user import User
from schemas.card_schema import CardCreate, CardUpdate, CardResponse, CardHistoryResponse
from services.notification_service import NotificationService
from core.exceptions import (
    CardNotFoundException, 
    BoardNotFoundException, 
    PermissionDeniedException,
    ColumnNotFoundException
)
from core.enums import CardActionType, NotificationType, CardStatus
from core.logger import get_logger

logger = get_logger(__name__)


class CardService:
    """Service pour la gestion complète des cartes avec historique et notifications"""
    
    def __init__(self, db: Session, notification_service: NotificationService):
        self.db = db
        self.notification_service = notification_service
    
    def _log_history(
        self, 
        card_id: int, 
        user_id: int, 
        action: CardActionType, 
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        field_name: Optional[str] = None,
        comment: Optional[str] = None
    ) -> CardHistory:
        """Crée un enregistrement d'historique pour une action sur une carte"""
        history_entry = CardHistory(
            card_id=card_id,
            user_id=user_id,
            action=action,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            comment=comment,
            created_at=datetime.utcnow()
        )
        self.db.add(history_entry)
        self.db.flush()
        logger.info(f"Historique enregistré: {action} sur la carte {card_id} par l'utilisateur {user_id}")
        return history_entry
    
    async def _send_card_notification(
        self,
        card: Card,
        action: CardActionType,
        user_id: int,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Envoie des notifications liées aux actions sur les cartes"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return
            
            # Déterminer les destinataires (assignés, créateur, membres du board)
            recipients = self._get_notification_recipients(card)
            
            # Construire le message de notification
            notification_data = {
                "card_id": card.id,
                "card_title": card.title,
                "board_id": card.board_id,
                "column_id": card.column_id,
                "user_id": user_id,
                "username": user.username,
                "action": action.value,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if additional_data:
                notification_data.update(additional_data)
            
            # Envoyer la notification
            await self.notification_service.send_notification(
                notification_type=NotificationType.CARD_UPDATE,
                recipients=recipients,
                data=notification_data,
                title=f"Carte '{card.title}' - {self._get_action_french_label(action)}",
                content=self._build_notification_message(card, action, user)
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification: {str(e)}", exc_info=True)
    
    def _get_notification_recipients(self, card: Card) -> List[int]:
        """Récupère la liste des IDs utilisateurs à notifier pour une carte"""
        recipients = set()
        
        # Ajouter le créateur
        if card.created_by:
            recipients.add(card.created_by)
        
        # Ajouter les assignés
        for assignee in card.assignees:
            recipients.add(assignee.id)
        
        # Ajouter les administrateurs du board
        board = self.db.query(Board).filter(Board.id == card.board_id).first()
        if board:
            for member in board.members:
                if member.role in ["admin", "owner"]:
                    recipients.add(member.user_id)
        
        return list(recipients)
    
    def _build_notification_message(self, card: Card, action: CardActionType, user: User) -> str:
        """Construit un message de notification en français"""
        action_labels = {
            CardActionType.CREATED: f"a créé la carte '{card.title}'",
            CardActionType.UPDATED: f"a modifié la carte '{card.title}'",
            CardActionType.DELETED: f"a supprimé la carte '{card.title}'",
            CardActionType.MOVED: f"a déplacé la carte '{card.title}'",
            CardActionType.ASSIGNED: f"s'est assigné la carte '{card.title}'",
            CardActionType.COMMENTED: f"a commenté sur la carte '{card.title}'",
            CardActionType.STATUS_CHANGED: f"a changé le statut de la carte '{card.title}'",
            CardActionType.DUE_DATE_CHANGED: f"a modifié la date d'échéance de '{card.title}'",
        }
        
        return f"{user.username} {action_labels.get(action, 'a effectué une action')}"
    
    def _get_action_french_label(self, action: CardActionType) -> str:
        """Retourne le libellé français d'une action"""
        labels = {
            CardActionType.CREATED: "Création",
            CardActionType.UPDATED: "Modification",
            CardActionType.DELETED: "Suppression",
            CardActionType.MOVED: "Déplacement",
            CardActionType.ASSIGNED: "Assignation",
            CardActionType.COMMENTED: "Commentaire",
            CardActionType.STATUS_CHANGED: "Changement de statut",
            CardActionType.DUE_DATE_CHANGED: "Date d'échéance modifiée",
        }
        return labels.get(action, "Action")
    
    def _serialize_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any]) -> tuple:
        """Sérialise les anciennes et nouvelles valeurs pour l'historique"""
        try:
            old_value = json.dumps(old_data, ensure_ascii=False) if old_data else None
            new_value = json.dumps(new_data, ensure_ascii=False) if new_data else None
            return old_value, new_value
        except Exception as e:
            logger.error(f"Erreur de sérialisation: {str(e)}")
            return str(old_data), str(new_data)
    
    def get_card_by_id(self, card_id: int, user_id: int) -> Card:
        """Récupère une carte par son ID avec vérification des permissions"""
        card = self.db.query(Card).filter(
            Card.id == card_id,
            Card.is_active == True
        ).first()
        
        if not card:
            raise CardNotFoundException(f"Carte avec l'ID {card_id} non trouvée")
        
        # Vérification des permissions
        self._check_card_access(card, user_id)
        
        return card
    
    def get_cards_by_board(
        self, 
        board_id: int, 
        user_id: int, 
        column_id: Optional[int] = None,
        status: Optional[CardStatus] = None
    ) -> List[Card]:
        """Récupère toutes les cartes d'un board avec filtres optionnels"""
        # Vérification d'accès au board
        board = self.db.query(Board).filter(Board.id == board_id).first()
        if not board:
            raise BoardNotFoundException(f"Board avec l'ID {board_id} non trouvé")
        
        self._check_board_access(board, user_id)
        
        # Construction de la requête
        query = self.db.query(Card).filter(
            Card.board_id == board_id,
            Card.is_active == True
        )
        
        if column_id:
            query = query.filter(Card.column_id == column_id)
        
        if status:
            query = query.filter(Card.status == status)
        
        return query.order_by(Card.position.asc(), Card.created_at.desc()).all()
    
    def create_card(self, card_data: CardCreate, user_id: int) -> Card:
        """Crée une nouvelle carte avec historique et notification"""
        # Vérification du board et de la colonne
        board = self.db.query(Board).filter(Board.id == card_data.board_id).first()
        if not board:
            raise BoardNotFoundException("Board non trouvé")
        
        column = self.db.query(BoardColumn).filter(
            BoardColumn.id == card_data.column_id,
            BoardColumn.board_id == card_data.board_id
        ).first()
        
        if not column:
            raise ColumnNotFoundException("Colonne non trouvée")
        
        self._check_board_access(board, user_id)
        
        # Création de la carte
        db_card = Card(
            **card_data.dict(exclude={"assignee_ids", "label_ids"}),
            created_by=user_id,
            position=self._get_next_position(card_data.column_id)
        )
        
        # Gestion des assignations
        if card_data.assignee_ids:
            assignees = self.db.query(User).filter(User.id.in_(card_data.assignee_ids)).all()
            db_card.assignees.extend(assignees)
        
        # Gestion des labels
        if hasattr(db_card, 'labels') and card_data.label_ids:
            labels = self.db.query(Label).filter(Label.id.in_(card_data.label_ids)).all()
            db_card.labels.extend(labels)
        
        self.db.add(db_card)
        self.db.flush()
        
        # Log de l'historique
        self._log_history(
            card_id=db_card.id,
            user_id=user_id,
            action=CardActionType.CREATED,
            comment=f"Carte créée dans la colonne '{column.name}'"
        )
        
        # Commit avant l'envoi de notification
        self.db.commit()
        self.db.refresh(db_card)
        
        # Envoi de la notification (asynchrone)
        try:
            import asyncio
            asyncio.create_task(
                self._send_card_notification(card=db_card, action=CardActionType.CREATED, user_id=user_id)
            )
        except Exception as e:
            logger.error(f"Erreur lors de la création de la tâche de notification: {str(e)}")
        
        return db_card
    
    def update_card(
        self, 
        card_id: int, 
        card_update: CardUpdate, 
        user_id: int
    ) -> Card:
        """Met à jour une carte avec suivi des modifications, historique et notifications"""
        card = self.get_card_by_id(card_id, user_id)
        
        # Récupération des anciennes valeurs
        old_data = {}
        changes = []
        
        # Vérification des champs modifiés
        update_data = card_update.dict(exclude_unset=True, exclude={"assignee_ids", "label_ids"})
        
        for field, new_value in update_data.items():
            old_value = getattr(card, field, None)
            if old_value != new_value:
                old_data[field] = str(old_value)
                changes.append({
                    "field": field,
                    "old": old_value,
                    "new": new_value
                })
                setattr(card, field, new_value)
        
        # Gestion spécifique du changement de colonne (déplacement)
        if "column_id" in update_data and card.column_id != update_data["column_id"]:
            old_column = self.db.query(BoardColumn).filter(BoardColumn.id == card.column_id).first()
            new_column = self.db.query(BoardColumn).filter(
                BoardColumn.id == update_data["column_id"]
            ).first()
            
            if old_column and new_column:
                self._log_history(
                    card_id=card.id,
                    user_id=user_id,
                    action=CardActionType.MOVED,
                    old_value=old_column.name,
                    new_value=new_column.name,
                    comment=f"Carte déplacée de '{old_column.name}' à '{new_column.name}'"
                )
                
                # Notification de déplacement
                try:
                    import asyncio
                    asyncio.create_task(
                        self._send_card_notification(
                            card=card,
                            action=CardActionType.MOVED,
                            user_id=user_id,
                            additional_data={
                                "old_column": old_column.name,
                                "new_column": new_column.name
                            }
                        )
                    )
                except Exception as e:
                    logger.error(f"Erreur notification déplacement: {str(e)}")
        
        # Gestion des assignations
        if "assignee_ids" in update_data:
            self._update_card_assignees(card, card_update.assignee_ids, user_id)
        
        # Gestion des labels
        if "label_ids" in update_data and hasattr(card, 'labels'):
            self._update_card_labels(card, card_update.label_ids)
        
        # Log des autres modifications
        if changes:
            old_serialized, new_serialized = self._serialize_changes(old_data, update_data)
            
            self._log_history(
                card_id=card.id,
                user_id=user_id,
                action=CardActionType.UPDATED,
                old_value=old_serialized,
                new_value=new_serialized,
                comment=f"Modification des champs: {', '.join([c['field'] for c in changes])}"
            )
            
            # Notification de mise à jour
            try:
                import asyncio
                asyncio.create_task(
                    self._send_card_notification(
                        card=card,
                        action=CardActionType.UPDATED,
                        user_id=user_id,
                        additional_data={"changes": [c["field"] for c in changes]}
                    )
                )
            except Exception as e:
                logger.error(f"Erreur notification mise à jour: {str(e)}")
        
        card.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(card)
        
        return card
    
    def delete_card(self, card_id: int, user_id: int) -> None:
        """Supprime une carte (soft delete) avec historique et notification"""
        card = self.get_card_by_id(card_id, user_id)
        
        # Vérification des permissions
        if card.created_by != user_id and not self._is_board_admin(card.board_id, user_id):
            raise PermissionDeniedException("Vous n'avez pas la permission de supprimer cette carte")
        
        # Soft delete
        card.is_active = False
        card.deleted_at = datetime.utcnow()
        card.deleted_by = user_id
        
        # Log historique
        self._log_history(
            card_id=card.id,
            user_id=user_id,
            action=CardActionType.DELETED,
            comment=f"Carte supprimée par l'utilisateur {user_id}"
        )
        
        self.db.commit()
        
        # Notification
        try:
            import asyncio
            asyncio.create_task(
                self._send_card_notification(card=card, action=CardActionType.DELETED, user_id=user_id)
            )
        except Exception as e:
            logger.error(f"Erreur notification suppression: {str(e)}")
    
    def get_card_history(
        self, 
        card_id: int, 
        user_id: int, 
        limit: int = 50
    ) -> List[CardHistoryResponse]:
        """Récupère l'historique d'une carte"""
        card = self.get_card_by_id(card_id, user_id)
        
        history_entries = self.db.query(CardHistory).filter(
            CardHistory.card_id == card_id
        ).order_by(CardHistory.created_at.desc()).limit(limit).all()
        
        return [CardHistoryResponse.from_orm(entry) for entry in history_entries]
    
    def add_comment(
        self, 
        card_id: int, 
        user_id: int, 
        content: str
    ) -> CardComment:
        """Ajoute un commentaire à une carte avec notification"""
        card = self.get_card_by_id(card_id, user_id)
        
        comment = CardComment(
            card_id=card_id,
            user_id=user_id,
            content=content,
            created_at=datetime.utcnow()
        )
        
        self.db.add(comment)
        
        # Log historique
        self._log_history(
            card_id=card_id,
            user_id=user_id,
            action=CardActionType.COMMENTED,
            comment=f"Ajout d'un commentaire: {content[:100]}..."
        )
        
        self.db.commit()
        self.db.refresh(comment)
        
        # Notification
        try:
            import asyncio
            asyncio.create_task(
                self._send_card_notification(
                    card=card,
                    action=CardActionType.COMMENTED,
                    user_id=user_id,
                    additional_data={"comment": content[:100]}
                )
            )
        except Exception as e:
            logger.error(f"Erreur notification commentaire: {str(e)}")
        
        return comment
    
    def assign_user_to_card(
        self, 
        card_id: int, 
        assignee_id: int, 
        assigned_by_user_id: int
    ) -> Card:
        """Assigne un utilisateur à une carte"""
        card = self.get_card_by_id(card_id, assigned_by_user_id)
        
        assignee = self.db.query(User).filter(User.id == assignee_id).first()
        if not assignee:
            raise ValueError(f"Utilisateur {assignee_id} non trouvé")
        
        # Vérifier si l'utilisateur a accès au board
        if not self._is_board_member(card.board_id, assignee_id):
            raise PermissionDeniedException(
                f"L'utilisateur {assignee_id} n'est pas membre de ce board"
            )
        
        # Ajouter l'assignation
        if assignee not in card.assignees:
            card.assignees.append(assignee)
            
            # Log historique
            self._log_history(
                card_id=card_id,
                user_id=assigned_by_user_id,
                action=CardActionType.ASSIGNED,
                comment=f"Utilisateur {assignee.username} assigné à la carte"
            )
            
            self.db.commit()
            self.db.refresh(card)
            
            # Notification à l'utilisateur assigné
            try:
                import asyncio
                asyncio.create_task(
                    self.notification_service.send_notification(
                        notification_type=NotificationType.CARD_ASSIGNED,
                        recipients=[assignee_id],
                        data={
                            "card_id": card.id,
                            "card_title": card.title,
                            "board_id": card.board_id,
                            "assigned_by": assigned_by_user_id
                        },
                        title=f"Vous avez ete assigne a '{card.title}'",
                        content=f"{card.assignees[0].username if card.assignees else 'Quelquun'} vous a assigne a la carte"
                    )
                )
            except Exception as e:
                logger.error(f"Erreur notification assignation: {str(e)}")
        
        return card
    
    def _update_card_assignees(self, card: Card, new_assignee_ids: List[int], user_id: int):
        """Met à jour la liste des assignés d'une carte"""
        current_assignee_ids = [u.id for u in card.assignees]
        
        # Ajouter nouveaux assignés
        for assignee_id in new_assignee_ids:
            if assignee_id not in current_assignee_ids:
                self.assign_user_to_card(card.id, assignee_id, user_id)
        
        # Retirer les assignés supprimés
        for current_id in current_assignee_ids:
            if current_id not in new_assignee_ids:
                user_to_remove = self.db.query(User).filter(User.id == current_id).first()
                if user_to_remove:
                    card.assignees.remove(user_to_remove)
                    
                    self._log_history(
                        card_id=card.id,
                        user_id=user_id,
                        action=CardActionType.UPDATED,
                        comment=f"Utilisateur {user_to_remove.username} retiré des assignés"
                    )
    
    def _update_card_labels(self, card: Card, new_label_ids: List[int]):
        """Met à jour les labels d'une carte"""
        if not hasattr(card, 'labels'):
            return
        
        current_label_ids = [l.id for l in card.labels]
        
        # Labels à ajouter
        labels_to_add = list(set(new_label_ids) - set(current_label_ids))
        if labels_to_add:
            new_labels = self.db.query(Label).filter(Label.id.in_(labels_to_add)).all()
            card.labels.extend(new_labels)
        
        # Labels à retirer
        labels_to_remove = list(set(current_label_ids) - set(new_label_ids))
        if labels_to_remove:
            for label_id in labels_to_remove:
                label_to_remove = next((l for l in card.labels if l.id == label_id), None)
                if label_to_remove:
                    card.labels.remove(label_to_remove)
    
    def _get_next_position(self, column_id: int) -> int:
        """Récupère la prochaine position disponible dans une colonne"""
        max_position = self.db.query(func.max(Card.position)).filter(
            Card.column_id == column_id,
            Card.is_active == True
        ).scalar()
        
        return (max_position or 0) + 1
    
    def _check_card_access(self, card: Card, user_id: int):
        """Vérifie si un utilisateur a accès à une carte"""
        board = self.db.query(Board).filter(Board.id == card.board_id).first()
        if not board:
            raise BoardNotFoundException("Board non trouvé")
        
        self._check_board_access(board, user_id)
    
    def _check_board_access(self, board: Board, user_id: int):
        """Vérifie si un utilisateur a accès à un board"""
        is_member = self.db.query(board.members).filter(
            board.members.c.user_id == user_id
        ).first()
        
        if not is_member and board.visibility == "private":
            raise PermissionDeniedException("Vous n'avez pas accès à ce board")
    
    def _is_board_admin(self, board_id: int, user_id: int) -> bool:
        """Vérifie si un utilisateur est administrateur d'un board"""
        membership = self.db.query(board.members).filter(
            board.members.c.user_id == user_id
        ).first()
        
        return membership and membership.role in ["admin", "owner"]
    
    def _is_board_member(self, board_id: int, user_id: int) -> bool:
        """Vérifie si un utilisateur est membre d'un board"""
        membership = self.db.query(board.members).filter(
            board.members.c.user_id == user_id
        ).first()
        
        return membership is not None
