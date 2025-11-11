// frontend/src/api/labels.js
// Service API pour les opérations sur les étiquettes

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3000/api';
const TOKEN_KEY = 'auth_token';

/**
 * Récupère le token d'authentification depuis le localStorage
 */
const getAuthToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * Configuration des headers par défaut pour les requêtes API
 */
const getDefaultHeaders = () => {
  const headers = {
    'Content-Type': 'application/json',
  };
  
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
};

/**
 * Gère la réponse de l'API
 * Lance une erreur si la réponse n'est pas OK
 */
const handleResponse = async (response) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `Erreur ${response.status}: ${response.statusText}`);
  }
  return response.json();
};

/**
 * Récupère toutes les étiquettes
 * @returns {Promise<Array>} Liste des étiquettes
 */
export const getAllLabels = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/labels`, {
      method: 'GET',
      headers: getDefaultHeaders(),
    });
    return await handleResponse(response);
  } catch (error) {
    console.error('Erreur lors de la récupération des étiquettes:', error);
    throw error;
  }
};

/**
 * Récupère une étiquette par son ID
 * @param {string|number} id - ID de l'étiquette
 * @returns {Promise<Object>} L'étiquette trouvée
 */
export const getLabelById = async (id) => {
  try {
    const response = await fetch(`${API_BASE_URL}/labels/${id}`, {
      method: 'GET',
      headers: getDefaultHeaders(),
    });
    return await handleResponse(response);
  } catch (error) {
    console.error(`Erreur lors de la récupération de l'étiquette ${id}:`, error);
    throw error;
  }
};

/**
 * Crée une nouvelle étiquette
 * @param {Object} labelData - Données de l'étiquette à créer
 * @param {string} labelData.name - Nom de l'étiquette
 * @param {string} labelData.color - Couleur hexadécimale (optionnel)
 * @returns {Promise<Object>} L'étiquette créée
 */
export const createLabel = async (labelData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/labels`, {
      method: 'POST',
      headers: getDefaultHeaders(),
      body: JSON.stringify(labelData),
    });
    return await handleResponse(response);
  } catch (error) {
    console.error('Erreur lors de la création de l\'étiquette:', error);
    throw error;
  }
};

/**
 * Met à jour une étiquette existante
 * @param {string|number} id - ID de l'étiquette
 * @param {Object} labelData - Données à mettre à jour
 * @returns {Promise<Object>} L'étiquette mise à jour
 */
export const updateLabel = async (id, labelData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/labels/${id}`, {
      method: 'PUT',
      headers: getDefaultHeaders(),
      body: JSON.stringify(labelData),
    });
    return await handleResponse(response);
  } catch (error) {
    console.error(`Erreur lors de la mise à jour de l'étiquette ${id}:`, error);
    throw error;
  }
};

/**
 * Supprime une étiquette
 * @param {string|number} id - ID de l'étiquette
 * @returns {Promise<void>}
 */
export const deleteLabel = async (id) => {
  try {
    const response = await fetch(`${API_BASE_URL}/labels/${id}`, {
      method: 'DELETE',
      headers: getDefaultHeaders(),
    });
    return await handleResponse(response);
  } catch (error) {
    console.error(`Erreur lors de la suppression de l'étiquette ${id}:`, error);
    throw error;
  }
};

/**
 * Recherche des étiquettes par nom
 * @param {string} query - Terme de recherche
 * @returns {Promise<Array>} Liste des étiquettes correspondantes
 */
export const searchLabels = async (query) => {
  try {
    const params = new URLSearchParams({ q: query });
    const response = await fetch(`${API_BASE_URL}/labels/search?${params}`, {
      method: 'GET',
      headers: getDefaultHeaders(),
    });
    return await handleResponse(response);
  } catch (error) {
    console.error(`Erreur lors de la recherche d'étiquettes avec "${query}":`, error);
    throw error;
  }
};

export default {
  getAllLabels,
  getLabelById,
  createLabel,
  updateLabel,
  deleteLabel,
  searchLabels,
};