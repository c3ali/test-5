// frontend/src/utils/websocket.js
/**
 * Gestionnaire WebSocket client pour les mises à jour en temps réel
 * Singleton Pattern pour une seule connexion partagée dans l'application
 */

class WebSocketManager {
  constructor(options = {}) {
    // Configuration
    this.url = options.url || this.getWebSocketURL();
    this.reconnectInterval = options.reconnectInterval || 1000; // ms
    this.maxReconnectInterval = options.maxReconnectInterval || 30000; // ms
    this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
    this.pingInterval = options.pingInterval || 30000; // ms
    this.pongTimeout = options.pongTimeout || 5000; // ms
    
    // État
    this.ws = null;
    this.isConnected = false;
    this.shouldReconnect = false;
    this.reconnectAttempts = 0;
    this.reconnectTimer = null;
    this.pingTimer = null;
    this.pongTimer = null;
    
    // File d'attente pour les messages envoyés hors connexion
    this.messageQueue = [];
    
    // Gestionnaires d'événements
    this.eventListeners = new Map();
    this.globalListeners = [];
    
    // Identifiant pour les messages de type request/response
    this.messageIdCounter = 0;
    this.pendingRequests = new Map();
  }

  /**
   * Détermine l'URL WebSocket en fonction de l'environnement
   */
  getWebSocketURL() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const path = process.env.VUE_APP_WS_PATH || '/ws';
    return `${protocol}//${host}${path}`;
  }

  /**
   * Établit la connexion WebSocket
   */
  connect() {
    if (this.isConnected || this.ws?.readyState === WebSocket.CONNECTING) {
      console.warn('[WebSocket] Connexion déjà en cours ou établie');
      return;
    }

    try {
      console.log(`[WebSocket] Connexion à ${this.url}...`);
      this.shouldReconnect = true;
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = this.onOpen.bind(this);
      this.ws.onmessage = this.onMessage.bind(this);
      this.ws.onclose = this.onClose.bind(this);
      this.ws.onerror = this.onError.bind(this);
    } catch (error) {
      console.error('[WebSocket] Erreur lors de la création de la connexion:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Gère l'événement onopen
   */
  onOpen() {
    console.log('[WebSocket] Connexion établie');
    this.isConnected = true;
    this.reconnectAttempts = 0;
    
    // Envoyer les messages en attente
    this.flushMessageQueue();
    
    // Démarrer le heartbeat
    this.startHeartbeat();
    
    // Notifier les listeners
    this.emit('connected');
  }

  /**
   * Gère l'événement onmessage
   */
  onMessage(event) {
    try {
      const data = JSON.parse(event.data);
      console.debug('[WebSocket] Message reçu:', data);
      
      // Vérifier si c'est un pong
      if (data.type === 'pong') {
        this.handlePong();
        return;
      }
      
      // Vérifier si c'est une réponse à une requête
      if (data.messageId && this.pendingRequests.has(data.messageId)) {
        const { resolve, reject, timeout } = this.pendingRequests.get(data.messageId);
        clearTimeout(timeout);
        this.pendingRequests.delete(data.messageId);
        
        if (data.error) {
          reject(new Error(data.error));
        } else {
          resolve(data);
        }
        return;
      }
      
      // Émettre l'événement aux listeners spécifiques
      if (data.event) {
        this.emit(data.event, data.data);
      }
      
      // Émettre aux listeners globaux
      this.globalListeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('[WebSocket] Erreur dans le listener global:', error);
        }
      });
      
    } catch (error) {
      console.error('[WebSocket] Erreur de parsing du message:', error);
    }
  }

  /**
   * Gère l'événement onclose
   */
  onClose(event) {
    console.log(`[WebSocket] Connexion fermée (Code: ${event.code})`);
    this.isConnected = false;
    this.stopHeartbeat();
    
    // Notifier les listeners
    this.emit('disconnected', { code: event.code, reason: event.reason });
    
    // Tenter de se reconnecter si nécessaire
    if (this.shouldReconnect) {
      this.scheduleReconnect();
    }
  }

  /**
   * Gère l'événement onerror
   */
  onError(error) {
    console.error('[WebSocket] Erreur:', error);
    this.emit('error', error);
  }

  /**
   * Envoie un message au serveur
   */
  send(data) {
    const message = typeof data === 'string' ? data : JSON.stringify(data);
    
    if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
      console.debug('[WebSocket] Message envoyé:', data);
      this.ws.send(message);
    } else {
      console.warn('[WebSocket] Non connecté, mise en file d\'attente du message');
      this.messageQueue.push(message);
    }
  }

  /**
   * Envoie un message avec attente d'une réponse
   */
  sendWithResponse(data, timeout = 10000) {
    return new Promise((resolve, reject) => {
      const messageId = ++this.messageIdCounter;
      const message = {
        ...data,
        messageId,
        timestamp: Date.now()
      };
      
      // Configurer le timeout
      const timeoutId = setTimeout(() => {
        this.pendingRequests.delete(messageId);
        reject(new Error('Timeout de la requête WebSocket'));
      }, timeout);
      
      // Stocker la promesse
      this.pendingRequests.set(messageId, { resolve, reject, timeout: timeoutId });
      
      // Envoyer le message
      this.send(message);
    });
  }

  /**
   * S'abonner à un événement spécifique
   */
  on(event, callback) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(callback);
    
    // Retourner une fonction de désabonnement
    return () => this.off(event, callback);
  }

  /**
   * Se désabonner d'un événement
   */
  off(event, callback) {
    if (this.eventListeners.has(event)) {
      const listeners = this.eventListeners.get(event);
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
      if (listeners.length === 0) {
        this.eventListeners.delete(event);
      }
    }
  }

  /**
   * Ajouter un listener global pour tous les messages
   */
  addGlobalListener(callback) {
    this.globalListeners.push(callback);
    
    // Retourner une fonction de suppression
    return () => {
      const index = this.globalListeners.indexOf(callback);
      if (index > -1) {
        this.globalListeners.splice(index, 1);
      }
    };
  }

  /**
   * Émet un événement aux listeners
   */
  emit(event, data) {
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`[WebSocket] Erreur dans le listener de l'événement "${event}":`, error);
        }
      });
    }
  }

  /**
   * Vide la file d'attente des messages
   */
  flushMessageQueue() {
    while (this.messageQueue.length > 0 && this.isConnected) {
      const message = this.messageQueue.shift();
      try {
        this.ws.send(message);
      } catch (error) {
        console.error('[WebSocket] Erreur lors de l\'envoi d\'un message en file d\'attente:', error);
        this.messageQueue.unshift(message);
        break;
      }
    }
  }

  /**
   * Programme une tentative de reconnexion
   */
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocket] Nombre maximal de tentatives de reconnexion atteint');
      this.emit('reconnect_failed');
      return;
    }
    
    const delay = Math.min(
      this.reconnectInterval * Math.pow(2, this.reconnectAttempts),
      this.maxReconnectInterval
    );
    
    console.log(`[WebSocket] Tentative de reconnexion #${this.reconnectAttempts + 1} dans ${delay}ms`);
    this.emit('reconnecting', { attempt: this.reconnectAttempts + 1, delay });
    
    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }

  /**
   * Démarre le heartbeat pour maintenir la connexion
   */
  startHeartbeat() {
    this.stopHeartbeat();
    
    this.pingTimer = setInterval(() => {
      this.send({ type: 'ping', timestamp: Date.now() });
      
      // Attendre le pong
      this.pongTimer = setTimeout(() => {
        console.warn('[WebSocket] Pong non reçu, déconnexion...');
        this.ws.close();
      }, this.pongTimeout);
    }, this.pingInterval);
  }

  /**
   * Gère la réponse pong
   */
  handlePong() {
    if (this.pongTimer) {
      clearTimeout(this.pongTimer);
      this.pongTimer = null;
    }
  }

  /**
   * Arrête le heartbeat
   */
  stopHeartbeat() {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
    if (this.pongTimer) {
      clearTimeout(this.pongTimer);
      this.pongTimer = null;
    }
  }

  /**
   * Déconnecte proprement
   */
  disconnect() {
    console.log('[WebSocket] Déconnexion demandée');
    this.shouldReconnect = false;
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.ws) {
      this.ws.close(1000, 'Déconnexion normale');
    }
  }

  /**
   * Vérifie si la connexion est active
   */
  get isAlive() {
    return this.isConnected && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Retourne les statistiques de connexion
   */
  getStats() {
    return {
      isConnected: this.isConnected,
      isAlive: this.isAlive,
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.maxReconnectAttempts,
      queuedMessages: this.messageQueue.length,
      pendingRequests: this.pendingRequests.size,
      url: this.url,
      readyState: this.ws?.readyState || WebSocket.CLOSED
    };
  }
}

// Exporte une instance unique (singleton)
const websocket = new WebSocketManager();

// Auto-connect si l'environnement le demande
if (process.env.VUE_APP_WS_AUTO_CONNECT !== 'false') {
  // Attendre que l'application soit montée
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      websocket.connect();
    });
  } else {
    websocket.connect();
  }
}

export default websocket;
```

### Exemple d'utilisation :

```javascript
// Connexion et écoute d'événements
import ws from '@/utils/websocket';

// S'abonner aux mises à jour de tâches
const unsubscribe = ws.on('task:updated', (data) => {
  console.log('Tâche mise à jour:', data);
  // Mettre à jour le store Vuex/Pinia
  store.dispatch('tasks/updateTask', data);
});

// S'abonner aux notifications
ws.on('notification:new', (notification) => {
  store.dispatch('notifications/add', notification);
});

// Envoyer un message avec réponse
async function createTask(taskData) {
  try {
    const response = await ws.sendWithResponse({
      event: 'task:create',
      data: taskData
    });
    console.log('Tâche créée:', response);
    return response.data;
  } catch (error) {
    console.error('Erreur création tâche:', error);
    throw error;
  }
}

// Déconnexion propre
window.addEventListener('beforeunload', () => {
  ws.disconnect();
});
```

### Fonctionnalités principales :

1. **Singleton pattern** : Une seule connexion partagée dans toute l'application
2. **Reconnexion automatique** : Exponentielle backoff (1s, 2s, 4s, 8s... jusqu'à 30s)
3. **File d'attente des messages** : Les messages envoyés hors connexion sont stockés et envoyés à la reconnexion
4. **Heartbeat** : Ping/Pong pour détecter les connexions mortes
5. **Système d'événements** : Subscribe/unsubscribe avec pattern `event:data`
6. **Requêtes/Réponses** : Support des messages avec attente d'accusée de réception
7. **Logs détaillés** : Pour le débogage en développement
8. **Statistiques** : Méthode `getStats()` pour monitorer l'état
9. **Auto-connect** : Optionnel, configurable via variable d'environnement