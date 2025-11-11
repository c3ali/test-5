// frontend/src/api/boards.js
// Service API pour les opérations sur les tableaux

import axios from 'axios';
import { API_BASE_URL } from '../config/api';

// Création d'une instance axios avec la configuration de base
const api = axios.create({
  baseURL: `${API_BASE_URL}/boards`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour ajouter le token d'authentification à chaque requête
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
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
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

/**
 * Récupère tous les tableaux de l'utilisateur
 * @returns {Promise<Array>} Liste des tableaux
 */
export const getAllBoards = async () => {
  try {
    const response = await api.get('/');
    return response.data;
  } catch (error) {
    console.error('Erreur lors de la récupération des tableaux:', error);
    throw error;
  }
};

/**
 * Récupère un tableau spécifique par son ID
 * @param {string} boardId - ID du tableau
 * @returns {Promise<Object>} Le tableau demandé
 */
export const getBoardById = async (boardId) => {
  try {
    const response = await api.get(`/${boardId}`);
    return response.data;
  } catch (error) {
    console.error(`Erreur lors de la récupération du tableau ${boardId}:`, error);
    throw error;
  }
};

/**
 * Crée un nouveau tableau
 * @param {Object} boardData - Données du tableau
 * @param {string} boardData.name - Nom du tableau
 * @param {string} boardData.description - Description du tableau
 * @param {string} boardData.color - Couleur du tableau (hex code)
 * @returns {Promise<Object>} Le tableau créé
 */
export const createBoard = async (boardData) => {
  try {
    const response = await api.post('/', boardData);
    return response.data;
  } catch (error) {
    console.error('Erreur lors de la création du tableau:', error);
    throw error;
  }
};

/**
 * Met à jour un tableau existant
 * @param {string} boardId - ID du tableau
 * @param {Object} updates - Champs à mettre à jour
 * @returns {Promise<Object>} Le tableau mis à jour
 */
export const updateBoard = async (boardId, updates) => {
  try {
    const response = await api.patch(`/${boardId}`, updates);
    return response.data;
  } catch (error) {
    console.error(`Erreur lors de la mise à jour du tableau ${boardId}:`, error);
    throw error;
  }
};

/**
 * Supprime un tableau
 * @param {string} boardId - ID du tableau
 * @returns {Promise<void>}
 */
export const deleteBoard = async (boardId) => {
  try {
    await api.delete(`/${boardId}`);
  } catch (error) {
    console.error(`Erreur lors de la suppression du tableau ${boardId}:`, error);
    throw error;
  }
};

/**
 * Duplique un tableau
 * @param {string} boardId - ID du tableau à dupliquer
 * @param {Object} options - Options de duplication
 * @returns {Promise<Object>} Le nouveau tableau dupliqué
 */
export const duplicateBoard = async (boardId, options = {}) => {
  try {
    const response = await api.post(`/${boardId}/duplicate`, options);
    return response.data;
  } catch (error) {
    console.error(`Erreur lors de la duplication du tableau ${boardId}:`, error);
    throw error;
  }
};

/**
 * Ajoute un membre à un tableau
 * @param {string} boardId - ID du tableau
 * @param {Object} memberData - Données du membre
 * @param {string} memberData.userId - ID de l'utilisateur
 * @param {string} memberData.role - Rôle du membre (admin, member, viewer)
 * @returns {Promise<Object>} Le membre ajouté
 */
export const addBoardMember = async (boardId, memberData) => {
  try {
    const response = await api.post(`/${boardId}/members`, memberData);
    return response.data;
  } catch (error) {
    console.error(`Erreur lors de l'ajout d'un membre au tableau ${boardId}:`, error);
    throw error;
  }
};

/**
 * Supprime un membre d'un tableau
 * @param {string} boardId - ID du tableau
 * @param {string} userId - ID de l'utilisateur à retirer
 * @returns {Promise<void>}
 */
export const removeBoardMember = async (boardId, userId) => {
  try {
    await api.delete(`/${boardId}/members/${userId}`);
  } catch (error) {
    console.error(`Erreur lors de la suppression du membre du tableau ${boardId}:`, error);
    throw error;
  }
};

/**
 * Récupère les statistiques d'un tableau
 * @param {string} boardId - ID du tableau
 * @returns {Promise<Object>} Les statistiques
 */
export const getBoardStats = async (boardId) => {
  try {
    const response = await api.get(`/${boardId}/stats`);
    return response.data;
  } catch (error) {
    console.error(`Erreur lors de la récupération des statistiques du tableau ${boardId}:`, error);
    throw error;
  }
};

/**
 * Recherche des tableaux par nom ou description
 * @param {string} query - Terme de recherche
 * @returns {Promise<Array>} Liste des tableaux correspondants
 */
export const searchBoards = async (query) => {
  try {
    const response = await api.get('/search', {
      params: { q: query },
    });
    return response.data;
  } catch (error) {
    console.error('Erreur lors de la recherche de tableaux:', error);
    throw error;
  }
};

export default {
  getAllBoards,
  getBoardById,
  createBoard,
  updateBoard,
  deleteBoard,
  duplicateBoard,
  addBoardMember,
  removeBoardMember,
  getBoardStats,
  searchBoards,
};