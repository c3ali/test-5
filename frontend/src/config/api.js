// frontend/src/config/api.js
// Configuration de l'API

// Base URL de l'API - utilise l'URL actuelle en production
export const API_BASE_URL = window.location.origin + '/api/v1';

// Configuration axios par défaut
export const API_CONFIG = {
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
};

// Endpoints
export const ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
  },
  USERS: '/users',
  BOARDS: '/boards',
  LISTS: '/lists',
  CARDS: '/cards',
  LABELS: '/labels',
};

export default {
  API_BASE_URL,
  API_CONFIG,
  ENDPOINTS,
};
