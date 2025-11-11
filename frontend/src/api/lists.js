// frontend/src/api/lists.js
// Service API pour les opérations sur les listes

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3000/api';
const TIMEOUT = 10000; // 10 secondes

/**
 * Configuration des headers pour les requêtes API
 * @returns {Object} Headers avec token d'authentification si disponible
 */
const getHeaders = () => {
  const token = localStorage.getItem('authToken');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

/**
 * Gère la réponse de l'API
 * @param {Response} response - Objet Response de fetch
 * @returns {Promise<Object>} Données JSON ou erreur
 */
const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Une erreur est survenue' }));
    throw new Error(error.message || `Erreur ${response.status}`);
  }
  return response.json();
};

/**
 * Configure un timeout pour la requête fetch
 * @param {Promise} promise - Promise fetch
 * @returns {Promise} Promise avec timeout
 */
const withTimeout = (promise) => {
  return Promise.race([
    promise,
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Timeout de la requête')), TIMEOUT)
    )
  ]);
};

/**
 * Récupère toutes les listes de l'utilisateur connecté
 * @returns {Promise<Array>} Tableau des listes
 */
export const getAllLists = async () => {
  try {
    const response = await withTimeout(
      fetch(`${API_BASE_URL}/lists`, {
        method: 'GET',
        headers: getHeaders()
      })
    );
    return await handleResponse(response);
  } catch (error) {
    console.error('Erreur lors de la récupération des listes:', error);
    throw error;
  }
};

/**
 * Récupère une liste spécifique par son ID
 * @param {string} listId - ID de la liste
 * @returns {Promise<Object>} La liste demandée
 */
export const getListById = async (listId) => {
  try {
    const response = await withTimeout(
      fetch(`${API_BASE_URL}/lists/${listId}`, {
        method: 'GET',
        headers: getHeaders()
      })
    );
    return await handleResponse(response);
  } catch (error) {
    console.error(`Erreur lors de la récupération de la liste ${listId}:`, error);
    throw error;
  }
};

/**
 * Crée une nouvelle liste
 * @param {Object} listData - Données de la liste { name, description, color }
 * @returns {Promise<Object>} La liste créée
 */
export const createList = async (listData) => {
  try {
    const response = await withTimeout(
      fetch(`${API_BASE_URL}/lists`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(listData)
      })
    );
    return await handleResponse(response);
  } catch (error) {
    console.error('Erreur lors de la création de la liste:', error);
    throw error;
  }
};

/**
 * Met à jour une liste existante
 * @param {string} listId - ID de la liste
 * @param {Object} updates - Champs à mettre à jour { name, description, color, archived }
 * @returns {Promise<Object>} La liste mise à jour
 */
export const updateList = async (listId, updates) => {
  try {
    const response = await withTimeout(
      fetch(`${API_BASE_URL}/lists/${listId}`, {
        method: 'PATCH',
        headers: getHeaders(),
        body: JSON.stringify(updates)
      })
    );
    return await handleResponse(response);
  } catch (error) {
    console.error(`Erreur lors de la mise à jour de la liste ${listId}:`, error);
    throw error;
  }
};

/**
 * Supprime une liste
 * @param {string} listId - ID de la liste
 * @returns {Promise<Object>} Confirmation de suppression
 */
export const deleteList = async (listId) => {
  try {
    const response = await withTimeout(
      fetch(`${API_BASE_URL}/lists/${listId}`, {
        method: 'DELETE',
        headers: getHeaders()
      })
    );
    return await handleResponse(response);
  } catch (error) {
    console.error(`Erreur lors de la suppression de la liste ${listId}:`, error);
    throw error;
  }
};

/**
 * Archive/désarchive une liste
 * @param {string} listId - ID de la liste
 * @param {boolean} archived - État d'archivage
 * @returns {Promise<Object>} La liste mise à jour
 */
export const toggleArchiveList = async (listId, archived = true) => {
  return updateList(listId, { archived });
};

/**
 * Duplique une liste
 * @param {string} listId - ID de la liste à dupliquer
 * @returns {Promise<Object>} La nouvelle liste dupliquée
 */
export const duplicateList = async (listId) => {
  try {
    const response = await withTimeout(
      fetch(`${API_BASE_URL}/lists/${listId}/duplicate`, {
        method: 'POST',
        headers: getHeaders()
      })
    );
    return await handleResponse(response);
  } catch (error) {
    console.error(`Erreur lors de la duplication de la liste ${listId}:`, error);
    throw error;
  }
};

/**
 * Partage une liste avec un autre utilisateur
 * @param {string} listId - ID de la liste
 * @param {string} email - Email de l'utilisateur à qui partager
 * @param {string} permission - Permission ('read' ou 'write')
 * @returns {Promise<Object>} Confirmation du partage
 */
export const shareList = async (listId, email, permission = 'read') => {
  try {
    const response = await withTimeout(
      fetch(`${API_BASE_URL}/lists/${listId}/share`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ email, permission })
      })
    );
    return await handleResponse(response);
  } catch (error) {
    console.error(`Erreur lors du partage de la liste ${listId}:`, error);
    throw error;
  }
};

export default {
  getAllLists,
  getListById,
  createList,
  updateList,
  deleteList,
  toggleArchiveList,
  duplicateList,
  shareList
};