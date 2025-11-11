// frontend/src/store/modules/board.js

// Constants for mutation types
const SET_BOARDS = 'SET_BOARDS';
const SET_BOARD = 'SET_BOARD';
const ADD_BOARD = 'ADD_BOARD';
const UPDATE_BOARD = 'UPDATE_BOARD';
const DELETE_BOARD = 'DELETE_BOARD';
const SET_LOADING = 'SET_LOADING';
const SET_ERROR = 'SET_ERROR';
const RESET_STATE = 'RESET_STATE';

/**
 * Module Vuex pour la gestion des tableaux (boards)
 * @module board
 */
export default {
  namespaced: true,

  /**
   * État initial du module
   * @property {Array} boards - Liste des tableaux
   * @property {Object|null} currentBoard - Tableau actuellement sélectionné
   * @property {boolean} loading - État de chargement
   * @property {string|null} error - Message d'erreur
   */
  state: {
    boards: [],
    currentBoard: null,
    loading: false,
    error: null,
  },

  /**
   * Getters pour accéder aux données de l'état
   */
  getters: {
    /**
     * Retourne tous les tableaux
     * @param {Object} state
     * @returns {Array} Liste des tableaux
     */
    allBoards: (state) => state.boards,

    /**
     * Retourne le tableau actuel
     * @param {Object} state
     * @returns {Object|null} Tableau actuel
     */
    currentBoard: (state) => state.currentBoard,

    /**
     * Vérifie si une opération est en cours
     * @param {Object} state
     * @returns {boolean}
     */
    isLoading: (state) => state.loading,

    /**
     * Retourne le message d'erreur
     * @param {Object} state
     * @returns {string|null}
     */
    getError: (state) => state.error,

    /**
     * Retourne un tableau par son ID
     * @param {Object} state
     * @returns {Function}
     */
    getBoardById: (state) => (id) => {
      return state.boards.find(board => board.id === id);
    },

    /**
     * Retourne le nombre de tableaux
     * @param {Object} state
     * @returns {number}
     */
    boardsCount: (state) => state.boards.length,
  },

  /**
   * Mutations pour modifier l'état (synchrones)
   */
  mutations: {
    /**
     * Définit la liste des tableaux
     * @param {Object} state
     * @param {Array} boards
     */
    [SET_BOARDS](state, boards) {
      state.boards = boards;
    },

    /**
     * Définit le tableau actuel
     * @param {Object} state
     * @param {Object} board
     */
    [SET_BOARD](state, board) {
      state.currentBoard = board;
    },

    /**
     * Ajoute un nouveau tableau à la liste
     * @param {Object} state
     * @param {Object} board
     */
    [ADD_BOARD](state, board) {
      state.boards.push(board);
    },

    /**
     * Met à jour un tableau existant
     * @param {Object} state
     * @param {Object} updatedBoard
     */
    [UPDATE_BOARD](state, updatedBoard) {
      const index = state.boards.findIndex(board => board.id === updatedBoard.id);
      if (index !== -1) {
        state.boards.splice(index, 1, updatedBoard);
      }
      // Met aussi à jour le currentBoard si c'est le même
      if (state.currentBoard && state.currentBoard.id === updatedBoard.id) {
        state.currentBoard = updatedBoard;
      }
    },

    /**
     * Supprime un tableau de la liste
     * @param {Object} state
     * @param {string|number} boardId
     */
    [DELETE_BOARD](state, boardId) {
      state.boards = state.boards.filter(board => board.id !== boardId);
      // Réinitialise le currentBoard si nécessaire
      if (state.currentBoard && state.currentBoard.id === boardId) {
        state.currentBoard = null;
      }
    },

    /**
     * Définit l'état de chargement
     * @param {Object} state
     * @param {boolean} loading
     */
    [SET_LOADING](state, loading) {
      state.loading = loading;
    },

    /**
     * Définit le message d'erreur
     * @param {Object} state
     * @param {string|null} error
     */
    [SET_ERROR](state, error) {
      state.error = error;
    },

    /**
     * Réinitialise l'état du module
     * @param {Object} state
     */
    [RESET_STATE](state) {
      state.boards = [];
      state.currentBoard = null;
      state.loading = false;
      state.error = null;
    },
  },

  /**
   * Actions pour effectuer des opérations asynchrones
   */
  actions: {
    /**
     * Récupère tous les tableaux depuis l'API
     * @param {Object} context
     * @returns {Promise<Array>}
     */
    async fetchBoards({ commit }) {
      commit(SET_LOADING, true);
      commit(SET_ERROR, null);
      try {
        // TODO: Remplacer par votre appel API réel
        const response = await fetch('/api/boards');
        if (!response.ok) throw new Error('Erreur lors de la récupération des tableaux');
        const boards = await response.json();
        commit(SET_BOARDS, boards);
        return boards;
      } catch (error) {
        commit(SET_ERROR, error.message);
        throw error;
      } finally {
        commit(SET_LOADING, false);
      }
    },

    /**
     * Récupère un tableau spécifique par son ID
     * @param {Object} context
     * @param {string|number} boardId
     * @returns {Promise<Object>}
     */
    async fetchBoard({ commit }, boardId) {
      commit(SET_LOADING, true);
      commit(SET_ERROR, null);
      try {
        // TODO: Remplacer par votre appel API réel
        const response = await fetch(`/api/boards/${boardId}`);
        if (!response.ok) throw new Error(`Erreur lors de la récupération du tableau ${boardId}`);
        const board = await response.json();
        commit(SET_BOARD, board);
        return board;
      } catch (error) {
        commit(SET_ERROR, error.message);
        throw error;
      } finally {
        commit(SET_LOADING, false);
      }
    },

    /**
     * Crée un nouveau tableau
     * @param {Object} context
     * @param {Object} boardData - Données du tableau à créer
     * @returns {Promise<Object>}
     */
    async createBoard({ commit }, boardData) {
      commit(SET_LOADING, true);
      commit(SET_ERROR, null);
      try {
        // TODO: Remplacer par votre appel API réel
        const response = await fetch('/api/boards', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(boardData),
        });
        if (!response.ok) throw new Error('Erreur lors de la création du tableau');
        const newBoard = await response.json();
        commit(ADD_BOARD, newBoard);
        commit(SET_BOARD, newBoard); // Définit comme tableau actuel
        return newBoard;
      } catch (error) {
        commit(SET_ERROR, error.message);
        throw error;
      } finally {
        commit(SET_LOADING, false);
      }
    },

    /**
     * Met à jour un tableau existant
     * @param {Object} context
     * @param {Object} payload - { id: string|number, data: Object }
     * @returns {Promise<Object>}
     */
    async updateBoard({ commit }, { id, data }) {
      commit(SET_LOADING, true);
      commit(SET_ERROR, null);
      try {
        // TODO: Remplacer par votre appel API réel
        const response = await fetch(`/api/boards/${id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error(`Erreur lors de la mise à jour du tableau ${id}`);
        const updatedBoard = await response.json();
        commit(UPDATE_BOARD, updatedBoard);
        return updatedBoard;
      } catch (error) {
        commit(SET_ERROR, error.message);
        throw error;
      } finally {
        commit(SET_LOADING, false);
      }
    },

    /**
     * Supprime un tableau
     * @param {Object} context
     * @param {string|number} boardId
     * @returns {Promise<void>}
     */
    async deleteBoard({ commit }, boardId) {
      commit(SET_LOADING, true);
      commit(SET_ERROR, null);
      try {
        // TODO: Remplacer par votre appel API réel
        const response = await fetch(`/api/boards/${boardId}`, {
          method: 'DELETE',
        });
        if (!response.ok) throw new Error(`Erreur lors de la suppression du tableau ${boardId}`);
        commit(DELETE_BOARD, boardId);
      } catch (error) {
        commit(SET_ERROR, error.message);
        throw error;
      } finally {
        commit(SET_LOADING, false);
      }
    },

    /**
     * Sélectionne un tableau comme actuel (sans appel API)
     * @param {Object} context
     * @param {Object} board
     * @returns {void}
     */
    selectBoard({ commit }, board) {
      commit(SET_BOARD, board);
    },

    /**
     * Nettoie les erreurs
     * @param {Object} context
     */
    clearError({ commit }) {
      commit(SET_ERROR, null);
    },

    /**
     * Réinitialise completement le state du module
     * @param {Object} context
     */
    reset({ commit }) {
      commit(RESET_STATE);
    },
  },
};