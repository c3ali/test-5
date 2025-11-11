# backend/websocket.py
"""
Gestionnaire WebSocket pour les mises à jour en temps réel des modifications de tableau.
Gère les connexions clients, la diffusion des changements et la synchronisation entre utilisateurs.
"""

import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field, ValidationError
from enum import Enum

# Configuration du logger
logger = logging.getLogger(__name__)

class ActionType(str, Enum):
    """Types d'actions supportées sur le tableau"""
    CREATE_CARD = "create_card"
    UPDATE_CARD = "update_card"
    DELETE_CARD = "delete_card"
    MOVE_CARD = "move_card"
    CREATE_COLUMN = "create_column"
    UPDATE_COLUMN = "delete_column"
    DELETE_COLUMN = "delete_column"
    CURSOR_MOVE = "cursor_move"  # Pour montrer les curseurs des autres utilisateurs

class WebSocketMessage(BaseModel):
    """Modèle de validation pour les messages WebSocket entrants"""
    action: ActionType
    data: dict = Field(..., description="Données spécifiques à l'action")
    board_id: str = Field(..., description="ID du tableau concerné")
    user_id: str = Field(..., description="ID de l'utilisateur émetteur")
    timestamp: float = Field(default_factory=lambda: __import__('time').time())

class ConnectionManager:
    """
    Gère les connexions WebSocket actives.
    Utilise un système de "rooms" pour isoler les tableaux.
    """
    
    def __init__(self):
        # board_id -> ensemble de connexions WebSocket
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # websocket -> board_id (pour faciliter la déconnexion)
        self.connection_board_map: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, board_id: str):
        """Établit une nouvelle connexion WebSocket pour un tableau spécifique"""
        await websocket.accept()
        
        if board_id not in self.active_connections:
            self.active_connections[board_id] = set()
        
        self.active_connections[board_id].add(websocket)
        self.connection_board_map[websocket] = board_id
        
        logger.info(f"Client connecté au tableau {board_id}. Total clients: {len(self.active_connections[board_id])}")
    
    def disconnect(self, websocket: WebSocket):
        """Déconnecte un client et nettoie les ressources"""
        board_id = self.connection_board_map.get(websocket)
        
        if board_id and board_id in self.active_connections:
            self.active_connections[board_id].discard(websocket)
            
            # Nettoyage si plus aucune connexion sur ce tableau
            if not self.active_connections[board_id]:
                del self.active_connections[board_id]
                logger.info(f"Room supprimée pour le tableau {board_id}")
        
        if websocket in self.connection_board_map:
            del self.connection_board_map[websocket]
        
        logger.info(f"Client déconnecté du tableau {board_id}")
    
    async def broadcast_to_board(
        self, 
        message: dict, 
        board_id: str, 
        exclude_client: WebSocket = None
    ):
        """
        Diffuse un message à tous les clients connectés sur un tableau.
        Peut exclure un client spécifique (l'émetteur).
        """
        if board_id not in self.active_connections:
            return
        
        disconnected_clients = []
        
        for connection in self.active_connections[board_id]:
            if connection == exclude_client:
                continue
            
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Erreur envoi message: {e}")
                disconnected_clients.append(connection)
        
        # Nettoyage des clients déconnectés
        for client in disconnected_clients:
            self.disconnect(client)
    
    def get_connected_users_count(self, board_id: str) -> int:
        """Retourne le nombre d'utilisateurs connectés sur un tableau"""
        return len(self.active_connections.get(board_id, set()))

# Instance globale du gestionnaire de connexions
manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, board_id: str, user_id: str):
    """
    Endpoint WebSocket principal pour les mises à jour de tableau en temps réel.
    
    Args:
        websocket: La connexion WebSocket
        board_id: Identifiant du tableau
        user_id: Identifiant de l'utilisateur
    """
    await manager.connect(websocket, board_id)
    
    try:
        # Envoi de confirmation de connexion
        await websocket.send_json({
            "type": "connection_established",
            "data": {
                "message": "Connecté au tableau en temps réel",
                "connected_users": manager.get_connected_users_count(board_id)
            }
        })
        
        # Diffusion aux autres utilisateurs qu'un nouveau client s'est connecté
        await manager.broadcast_to_board(
            {
                "type": "user_joined",
                "data": {
                    "user_id": user_id,
                    "connected_users": manager.get_connected_users_count(board_id)
                }
            },
            board_id,
            exclude_client=websocket
        )
        
        # Boucle de réception des messages
        while True:
            try:
                data = await websocket.receive_text()
                
                # Validation et parsing du message
                try:
                    message_data = json.loads(data)
                    validated_message = WebSocketMessage(**message_data)
                    
                    # Vérification que l'utilisateur envoie bien des données pour son propre board
                    if validated_message.board_id != board_id:
                        await websocket.send_json({
                            "type": "error",
                            "data": {"message": "Board ID mismatch"}
                        })
                        continue
                    
                    if validated_message.user_id != user_id:
                        await websocket.send_json({
                            "type": "error",
                            "data": {"message": "User ID mismatch"}
                        })
                        continue
                    
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": "Invalid JSON format"}
                    })
                    continue
                except ValidationError as e:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": f"Validation error: {e.errors()}"}
                    })
                    continue
                
                # Diffusion du message valide aux autres clients du même tableau
                await manager.broadcast_to_board(
                    {
                        "type": "board_update",
                        "action": validated_message.action.value,
                        "data": validated_message.data,
                        "user_id": user_id,
                        "timestamp": validated_message.timestamp
                    },
                    board_id,
                    exclude_client=websocket
                )
                
                # Confirmation d'envoi à l'émetteur
                await websocket.send_json({
                    "type": "ack",
                    "data": {"status": "broadcasted"}
                })
                
            except WebSocketDisconnect:
                logger.info(f"Client {user_id} déconnecté du tableau {board_id}")
                break
            except Exception as e:
                logger.error(f"Erreur inattendue: {e}")
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Internal server error"}
                })
    
    except Exception as e:
        logger.error(f"Erreur fatale sur le WebSocket: {e}")
    
    finally:
        # Déconnexion et nettoyage
        await manager.disconnect(websocket)
        
        # Notification aux autres utilisateurs
        await manager.broadcast_to_board(
            {
                "type": "user_left",
                "data": {
                    "user_id": user_id,
                    "connected_users": manager.get_connected_users_count(board_id)
                }
            },
            board_id
        )

# Pour utiliser ce WebSocket dans FastAPI :
# from fastapi import FastAPI
# app = FastAPI()
# 
# @app.websocket("/ws/board/{board_id}/{user_id}")
# async def board_websocket(websocket: WebSocket, board_id: str, user_id: str):
#     await websocket_endpoint(websocket, board_id, user_id)
