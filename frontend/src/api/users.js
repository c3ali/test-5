// frontend/src/api/users.js
// Service API pour l'authentification et gestion utilisateurs

import axios from 'axios';

// Configuration de l'instance Axios
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001/api';

const api = axios.create({
  baseURL: `${API_URL}/users`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour ajouter le token JWT à chaque requête
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

// Intercepteur pour gérer les erreurs de réponse
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token invalide ou expiré
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

/**
 * Service pour la gestion des utilisateurs et de l'authentification
 */
class UsersService {
  /**
   * Inscription d'un nouvel utilisateur
   * @param {Object} userData - Données utilisateur
   * @param {string} userData.username - Nom d'utilisateur
   * @param {string} userData.email - Email
   * @param {string} userData.password - Mot de passe
   * @returns {Promise<Object>} Utilisateur créé et token
   */
  static async register(userData) {
    try {
      const response = await api.post('/register', userData);
      const { user, token } = response.data;
      
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));
      
      return { user, token };
    } catch (error) {
      throw new Error(
        error.response?.data?.message || 'Erreur lors de l\'inscription'
      );
    }
  }

  /**
   * Connexion utilisateur
   * @param {Object} credentials - Identifiants
   * @param {string} credentials.email - Email
   * @param {string} credentials.password - Mot de passe
   * @returns {Promise<Object>} Utilisateur et token
   */
  static async login(credentials) {
    try {
      const response = await api.post('/login', credentials);
      const { user, token } = response.data;
      
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));
      
      return { user, token };
    } catch (error) {
      throw new Error(
        error.response?.data?.message || 'Erreur lors de la connexion'
      );
    }
  }

  /**
   * Déconnexion utilisateur
   */
  static logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }

  /**
   * Récupérer le profil de l'utilisateur connecté
   * @returns {Promise<Object>} Profil utilisateur
   */
  static async getProfile() {
    try {
      const response = await api.get('/profile');
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.message || 'Erreur lors de la récupération du profil'
      );
    }
  }

  /**
   * Mettre à jour le profil utilisateur
   * @param {Object} updateData - Données à mettre à jour
   * @returns {Promise<Object>} Utilisateur mis à jour
   */
  static async updateProfile(updateData) {
    try {
      const response = await api.put('/profile', updateData);
      const updatedUser = response.data;
      
      // Mettre à jour le localStorage
      localStorage.setItem('user', JSON.stringify(updatedUser));
      
      return updatedUser;
    } catch (error) {
      throw new Error(
        error.response?.data?.message || 'Erreur lors de la mise à jour du profil'
      );
    }
  }

  /**
   * Changer le mot de passe
   * @param {Object} passwordData - Données du mot de passe
   * @param {string} passwordData.currentPassword - Mot de passe actuel
   * @param {string} passwordData.newPassword - Nouveau mot de passe
   * @returns {Promise<Object>} Réponse du serveur
   */
  static async changePassword(passwordData) {
    try {
      const response = await api.put('/profile/password', passwordData);
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.message || 'Erreur lors du changement de mot de passe'
      );
    }
  }

  /**
   * Supprimer le compte utilisateur
   * @returns {Promise<Object>} Réponse du serveur
   */
  static async deleteAccount() {
    try {
      const response = await api.delete('/profile');
      this.logout();
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.message || 'Erreur lors de la suppression du compte'
      );
    }
  }

  /**
   * Demander la réinitialisation du mot de passe
   * @param {string} email - Email de l'utilisateur
   * @returns {Promise<Object>} Réponse du serveur
   */
  static async forgotPassword(email) {
    try {
      const response = await api.post('/forgot-password', { email });
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.message || 'Erreur lors de la demande de réinitialisation'
      );
    }
  }

  /**
   * Réinitialiser le mot de passe avec un token
   * @param {string} token - Token de réinitialisation
   * @param {string} newPassword - Nouveau mot de passe
   * @returns {Promise<Object>} Réponse du serveur
   */
  static async resetPassword(token, newPassword) {
    try {
      const response = await api.post('/reset-password', {
        token,
        newPassword,
      });
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.message || 'Erreur lors de la réinitialisation du mot de passe'
      );
    }
  }

  // --- ADMINISTRATION (requiert des privilèges admin) ---

  /**
   * Récupérer tous les utilisateurs (Admin uniquement)
   * @returns {Promise<Array>} Liste des utilisateurs
   */
  static async getAllUsers() {
    try {
      const response = await api.get('/');
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.message || 'Erreur lors de la récupération des utilisateurs'
      );
    }
  }

  /**
   * Récupérer un utilisateur par ID (Admin uniquement)
   * @param {string} userId - ID de l'utilisateur
   * @returns {Promise<Object>} Utilisateur
   */
  static async getUserById(userId) {
    try {
      const response = await api.get(`/${userId}`);
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.message || 'Erreur lors de la récupération de l\'utilisateur'
      );
    }
  }

  /**
   * Mettre à jour un utilisateur (Admin uniquement)
   * @param {string} userId - ID de l'utilisateur
   * @param {Object} updateData - Données à mettre à jour
   * @returns {Promise<Object>} Utilisateur mis à jour
   */
  static async updateUser(userId, updateData) {
    try {
      const response = await api.put(`/${userId}`, updateData);
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.message || 'Erreur lors de la mise à jour de l\'utilisateur'
      );
    }
  }

  /**
   * Supprimer un utilisateur (Admin uniquement)
   * @param {string} userId - ID de l'utilisateur
   * @returns {Promise<Object>} Réponse du serveur
   */
  static async deleteUser(userId) {
    try {
      const response = await api.delete(`/${userId}`);
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.message || 'Erreur lors de la suppression de l\'utilisateur'
      );
    }
  }

  /**
   * Vérifier si l'utilisateur est authentifié
   * @returns {boolean}
   */
  static isAuthenticated() {
    return !!localStorage.getItem('token');
  }

  /**
   * Récupérer l'utilisateur stocké en local
   * @returns {Object|null}
   */
  static getCurrentUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  }

  /**
   * Vérifier si l'utilisateur a un rôle spécifique
   * @param {string} role - Rôle à vérifier
   * @returns {boolean}
   */
  static hasRole(role) {
    const user = this.getCurrentUser();
    return user?.roles?.includes(role) || false;
  }

  /**
   * Rafraîchir le token d'accès
   * @returns {Promise<Object>} Nouveau token
   */
  static async refreshToken() {
    try {
      const response = await api.post('/refresh-token');
      const { token } = response.data;
      
      localStorage.setItem('token', token);
      return { token };
    } catch (error) {
      this.logout();
      throw new Error(
        error.response?.data?.message || 'Session expirée, veuillez vous reconnecter'
      );
    }
  }
}

export default UsersService;
export { api };