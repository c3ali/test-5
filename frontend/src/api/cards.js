import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001/api';

/**
 * Service API pour les opérations sur les cartes
 * Gère le CRUD et les opérations spécifiques pour les cartes du jeu
 */
const cardsApi = {
  /**
   * Récupère toutes les cartes
   * @param {Object} filters - Filtres optionnels (deck, type, rarity)
   * @returns {Promise<Array>} Liste des cartes
   */
  getAllCards: async (filters = {}) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/cards`, { params: filters });
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération des cartes:', error);
      throw error;
    }
  },

  /**
   * Récupère une carte par son ID
   * @param {string} cardId - ID de la carte
   * @returns {Promise<Object>} La carte trouvée
   */
  getCardById: async (cardId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/cards/${cardId}`);
      return response.data;
    } catch (error) {
      console.error(`Erreur lors de la récupération de la carte ${cardId}:`, error);
      throw error;
    }
  },

  /**
   * Crée une nouvelle carte
   * @param {Object} cardData - Données de la carte à créer
   * @returns {Promise<Object>} La carte créée
   */
  createCard: async (cardData) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/cards`, cardData, {
        headers: {
          'Content-Type': 'application/json',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la création de la carte:', error);
      throw error;
    }
  },

  /**
   * Met à jour une carte existante
   * @param {string} cardId - ID de la carte à mettre à jour
   * @param {Object} cardData - Nouvelles données de la carte
   * @returns {Promise<Object>} La carte mise à jour
   */
  updateCard: async (cardId, cardData) => {
    try {
      const response = await axios.put(`${API_BASE_URL}/cards/${cardId}`, cardData, {
        headers: {
          'Content-Type': 'application/json',
        },
      });
      return response.data;
    } catch (error) {
      console.error(`Erreur lors de la mise à jour de la carte ${cardId}:`, error);
      throw error;
    }
  },

  /**
   * Supprime une carte
   * @param {string} cardId - ID de la carte à supprimer
   * @returns {Promise<void>}
   */
  deleteCard: async (cardId) => {
    try {
      await axios.delete(`${API_BASE_URL}/cards/${cardId}`);
    } catch (error) {
      console.error(`Erreur lors de la suppression de la carte ${cardId}:`, error);
      throw error;
    }
  },

  /**
   * Récupère les cartes par deck
   * @param {string} deckId - ID du deck
   * @returns {Promise<Array>} Liste des cartes du deck
   */
  getCardsByDeck: async (deckId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/decks/${deckId}/cards`);
      return response.data;
    } catch (error) {
      console.error(`Erreur lors de la récupération des cartes du deck ${deckId}:`, error);
      throw error;
    }
  },

  /**
   * Recherche des cartes par terme
   * @param {string} searchTerm - Terme de recherche
   * @returns {Promise<Array>} Liste des cartes correspondantes
   */
  searchCards: async (searchTerm) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/cards/search`, {
        params: { q: searchTerm },
      });
      return response.data;
    } catch (error) {
      console.error(`Erreur lors de la recherche des cartes avec le terme "${searchTerm}":`, error);
      throw error;
    }
  },

  /**
   * Récupère les statistiques des cartes
   * @returns {Promise<Object>} Statistiques des cartes
   */
  getCardStats: async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/cards/stats`);
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération des statistiques des cartes:', error);
      throw error;
    }
  },
};

export default cardsApi;