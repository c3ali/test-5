// frontend/src/store/modules/user.js
import api from '@/services/api';
import { setAuthToken, clearAuthToken } from '@/utils/auth';

// États initial du module utilisateur
const state = {
  profile: null,          // Informations du profil utilisateur
  token: localStorage.getItem('access_token') || null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  loading: false,         // État de chargement pour les opérations
  error: null,            // Dernière erreur survenue
};

// Getters pour accéder aux données de l'état
const getters = {
  isAuthenticated: state => state.isAuthenticated,
  currentUser: state => state.profile,
  isLoading: state => state.loading,
  getError: state => state.error,
};

// Mutations pour modifier l'état (synchrones)
const mutations = {
  SET_USER(state, user) {
    state.profile = user;
  },
  SET_TOKEN(state, token) {
    state.token = token;
    state.isAuthenticated = !!token;
  },
  CLEAR_USER(state) {
    state.profile = null;
    state.token = null;
    state.isAuthenticated = false;
  },
  SET_LOADING(state, loading) {
    state.loading = loading;
  },
  SET_ERROR(state, error) {
    state.error = error;
  },
  CLEAR_ERROR(state) {
    state.error = null;
  },
};

// Actions pour les opérations asynchrones
const actions = {
  /**
   * Action de connexion
   * @param {Object} credentials - { email, password }
   */
  async login({ commit }, credentials) {
    commit('SET_LOADING', true);
    commit('CLEAR_ERROR');
    
    try {
      const response = await api.post('/auth/login', credentials);
      const { token, user } = response.data;
      
      // Stocker le token
      setAuthToken(token);
      commit('SET_TOKEN', token);
      commit('SET_USER', user);
      
      return Promise.resolve(user);
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Échec de la connexion';
      commit('SET_ERROR', errorMessage);
      return Promise.reject(error);
    } finally {
      commit('SET_LOADING', false);
    }
  },

  /**
   * Action d'inscription
   * @param {Object} userData - Données du nouvel utilisateur
   */
  async register({ commit }, userData) {
    commit('SET_LOADING', true);
    commit('CLEAR_ERROR');
    
    try {
      const response = await api.post('/auth/register', userData);
      const { token, user } = response.data;
      
      setAuthToken(token);
      commit('SET_TOKEN', token);
      commit('SET_USER', user);
      
      return Promise.resolve(user);
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Échec de l\'inscription';
      commit('SET_ERROR', errorMessage);
      return Promise.reject(error);
    } finally {
      commit('SET_LOADING', false);
    }
  },

  /**
   * Déconnexion de l'utilisateur
   */
  logout({ commit }) {
    clearAuthToken();
    commit('CLEAR_USER');
    commit('CLEAR_ERROR');
  },

  /**
   * Récupère le profil utilisateur depuis l'API
   */
  async fetchProfile({ commit, state }) {
    if (!state.token) return Promise.reject('Non authentifié');
    
    commit('SET_LOADING', true);
    commit('CLEAR_ERROR');
    
    try {
      const response = await api.get('/auth/profile');
      commit('SET_USER', response.data);
      return Promise.resolve(response.data);
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Échec de récupération du profil';
      commit('SET_ERROR', errorMessage);
      
      // Si erreur 401, déconnecter l'utilisateur
      if (error.response?.status === 401) {
        commit('CLEAR_USER');
        clearAuthToken();
      }
      
      return Promise.reject(error);
    } finally {
      commit('SET_LOADING', false);
    }
  },

  /**
   * Met à jour le profil utilisateur
   * @param {Object} updates - Champs à mettre à jour
   */
  async updateProfile({ commit }, updates) {
    commit('SET_LOADING', true);
    commit('CLEAR_ERROR');
    
    try {
      const response = await api.patch('/auth/profile', updates);
      commit('SET_USER', response.data);
      return Promise.resolve(response.data);
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Échec de la mise à jour du profil';
      commit('SET_ERROR', errorMessage);
      return Promise.reject(error);
    } finally {
      commit('SET_LOADING', false);
    }
  },

  /**
   * Rafraîchit le token d'accès
   */
  async refreshToken({ commit }) {
    try {
      const response = await api.post('/auth/refresh');
      const { token } = response.data;
      
      setAuthToken(token);
      commit('SET_TOKEN', token);
      return Promise.resolve(token);
    } catch (error) {
      commit('CLEAR_USER');
      clearAuthToken();
      return Promise.reject(error);
    }
  },

  /**
   * Efface les erreurs du state
   */
  clearError({ commit }) {
    commit('CLEAR_ERROR');
  },
};

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions,
};
```

### Fonctions utilitaires suggérées (`@/utils/auth.js`)

```javascript
// frontend/src/utils/auth.js

/**
 * Stocke le token JWT dans le localStorage et l'en-tête API
 */
export function setAuthToken(token) {
  localStorage.setItem('access_token', token);
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

/**
 * Supprime le token JWT du localStorage et des en-têtes API
 */
export function clearAuthToken() {
  localStorage.removeItem('access_token');
  delete api.defaults.headers.common['Authorization'];
}
```

### Configuration API suggérée (`@/services/api.js`)

```javascript
// frontend/src/services/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.VUE_APP_API_URL || 'http://localhost:3000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour gérer les erreurs 401
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Token expiré ou invalide
      // store.dispatch('user/logout');
    }
    return Promise.reject(error);
  }
);

export default api;
```

Ce module gère :
- ✅ Login / Logout / Register
- ✅ Stockage sécurisé du token JWT
- ✅ Profil utilisateur (lecture/écriture)
- ✅ États de chargement
- ✅ Gestion des erreurs
- ✅ Rafraîchissement automatique du token