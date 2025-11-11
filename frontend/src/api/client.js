import axios from 'axios';

// Création de l'instance Axios avec la configuration de base
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:3000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur de requête : ajoute le token d'authentification à chaque requête
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Intercepteur de réponse : gère les erreurs d'authentification et rafraîchit le token si nécessaire
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Si l'erreur est 401 (Unauthorized) et qu'on n'a pas déjà tenté de rafraîchir
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        // Appel à l'endpoint de rafraîchissement
        const response = await axios.post(
          `${process.env.REACT_APP_API_URL}/auth/refresh`,
          { refreshToken }
        );

        const { accessToken } = response.data;

        // Stockage du nouveau token
        localStorage.setItem('access_token', accessToken);

        // Mise à jour du header et relance de la requête originale
        originalRequest.headers.Authorization = `Bearer ${accessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Si le rafraîchissement échoue, déconnexion
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        // Redirection vers la page de login
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
        
        return Promise.reject(refreshError);
      }
    }

    // Gestion des autres erreurs
    if (error.response?.status === 403) {
      console.warn('Accès interdit : permissions insuffisantes');
    }

    return Promise.reject(error);
  }
);

// Fonctions utilitaires pour la gestion des tokens
export const setAuthTokens = (accessToken, refreshToken) => {
  localStorage.setItem('access_token', accessToken);
  if (refreshToken) {
    localStorage.setItem('refresh_token', refreshToken);
  }
};

export const clearAuthTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

export const getAccessToken = () => {
  return localStorage.getItem('access_token');
};

export default apiClient;