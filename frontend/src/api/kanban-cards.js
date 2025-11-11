// frontend/src/api/kanban-cards.js
// Service API pour les opérations sur les cartes Kanban

import axios from 'axios';
import { API_BASE_URL } from '../config/api';

// Création d'une instance axios avec la configuration de base
const api = axios.create({
  baseURL: `${API_BASE_URL}/cards`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour ajouter le token d'authentification à chaque requête
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Intercepteur pour gérer les erreurs globales
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Rediriger vers la page de login si non authentifié
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

/**
 * Récupère toutes les cartes d'une liste
 * @param {string} listId - ID de la liste
 * @returns {Promise<Array>} Liste des cartes
 */
export const getListCards = async (listId) => {
  try {
    const response = await api.get('/', {
      params: { list_id: listId }
    });
    return response.data;
  } catch (error) {
    console.error(`Erreur lors de la récupération des cartes de la liste ${listId}:`, error);
    throw error;
  }
};

/**
 * Récupère une carte spécifique par son ID
 * @param {string} cardId - ID de la carte
 * @returns {Promise<Object>} La carte demandée
 */
export const getCardById = async (cardId) => {
  try {
    const response = await api.get(`/${cardId}`);
    return response.data;
  } catch (error) {
    console.error(`Erreur lors de la récupération de la carte ${cardId}:`, error);
    throw error;
  }
};

/**
 * Crée une nouvelle carte
 * @param {string} listId - ID de la liste
 * @param {Object} cardData - Données de la carte
 * @param {string} cardData.title - Titre de la carte
 * @param {string} cardData.description - Description de la carte
 * @param {number} cardData.position - Position dans la liste
 * @returns {Promise<Object>} La carte créée
 */
export const createCard = async (listId, cardData) => {
  try {
    const response = await api.post('/', {
      list_id: listId,
      ...cardData
    });
    return response.data;
  } catch (error) {
    console.error('Erreur lors de la création de la carte:', error);
    throw error;
  }
};

/**
 * Met à jour une carte existante
 * @param {string} cardId - ID de la carte
 * @param {Object} updates - Champs à mettre à jour
 * @returns {Promise<Object>} La carte mise à jour
 */
export const updateCard = async (cardId, updates) => {
  try {
    const response = await api.patch(`/${cardId}`, updates);
    return response.data;
  } catch (error) {
    console.error(`Erreur lors de la mise à jour de la carte ${cardId}:`, error);
    throw error;
  }
};

/**
 * Supprime une carte
 * @param {string} cardId - ID de la carte
 * @returns {Promise<void>}
 */
export const deleteCard = async (cardId) => {
  try {
    await api.delete(`/${cardId}`);
  } catch (error) {
    console.error(`Erreur lors de la suppression de la carte ${cardId}:`, error);
    throw error;
  }
};

/**
 * Déplace une carte vers une autre liste
 * @param {string} cardId - ID de la carte
 * @param {string} targetListId - ID de la liste de destination
 * @param {number} position - Position dans la nouvelle liste
 * @returns {Promise<Object>} La carte mise à jour
 */
export const moveCard = async (cardId, targetListId, position) => {
  try {
    const response = await api.patch(`/${cardId}/move`, {
      list_id: targetListId,
      position
    });
    return response.data;
  } catch (error) {
    console.error(`Erreur lors du déplacement de la carte ${cardId}:`, error);
    throw error;
  }
};

/**
 * Archive/désarchive une carte
 * @param {string} cardId - ID de la carte
 * @param {boolean} isArchived - État d'archivage
 * @returns {Promise<Object>} La carte mise à jour
 */
export const toggleArchiveCard = async (cardId, isArchived) => {
  return updateCard(cardId, { is_archived: isArchived });
};

/**
 * Duplique une carte
 * @param {string} cardId - ID de la carte à dupliquer
 * @returns {Promise<Object>} La nouvelle carte dupliquée
 */
export const duplicateCard = async (cardId) => {
  try {
    const response = await api.post(`/${cardId}/duplicate`);
    return response.data;
  } catch (error) {
    console.error(`Erreur lors de la duplication de la carte ${cardId}:`, error);
    throw error;
  }
};

export default {
  getListCards,
  getCardById,
  createCard,
  updateCard,
  deleteCard,
  moveCard,
  toggleArchiveCard,
  duplicateCard,
};
