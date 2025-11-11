/**
 * Module Vuex pour la gestion des cartes avec actions asynchrones
 * @module card
 */

// État initial du module
const state = {
  /** @type {Array<Object>} Liste des cartes */
  cards: [],
  /** @type {boolean} Indique si une opération est en cours */
  isLoading: false,
  /** @type {string|null} Message d'erreur */
  error: null,
  /** @type {Object|null} Carte sélectionnée */
  selectedCard: null,
  /** @type {Object} Filtres actifs */
  filters: {
    search: '',
    category: null
  }
}

/**
 * Getters pour accéder aux données du state
 */
const getters = {
  /**
   * Retourne toutes les cartes
   * @param {Object} state - État du module
   * @returns {Array<Object>}
   */
  allCards: (state) => state.cards,

  /**
   * Retourne les cartes filtrées selon les critères actifs
   * @param {Object} state - État du module
   * @returns {Array<Object>}
   */
  filteredCards: (state) => {
    let filtered = state.cards
    
    // Filtrage par recherche
    if (state.filters.search) {
      const searchTerm = state.filters.search.toLowerCase()
      filtered = filtered.filter(card => 
        card.title.toLowerCase().includes(searchTerm) ||
        card.description.toLowerCase().includes(searchTerm)
      )
    }
    
    // Filtrage par catégorie
    if (state.filters.category) {
      filtered = filtered.filter(card => card.category === state.filters.category)
    }
    
    return filtered
  },

  /**
   * Retourne la carte sélectionnée
   * @param {Object} state - État du module
   * @returns {Object|null}
   */
  currentCard: (state) => state.selectedCard,

  /**
   * Indique si une opération est en cours
   * @param {Object} state - État du module
   * @returns {boolean}
   */
  isLoading: (state) => state.isLoading,

  /**
   * Retourne le message d'erreur
   * @param {Object} state - État du module
   * @returns {string|null}
   */
  error: (state) => state.error,

  /**
   * Retourne le nombre total de cartes
   * @param {Object} state - État du module
   * @returns {number}
   */
  cardCount: (state) => state.cards.length,

  /**
   * Retourne une carte par son ID
   * @param {Object} state - État du module
   * @returns {Function}
   */
  getCardById: (state) => (id) => {
    return state.cards.find(card => card.id === id)
  }
}

/**
 * Mutations synchrones pour modifier l'état
 */
const mutations = {
  /**
   * Définit la liste des cartes
   * @param {Object} state - État du module
   * @param {Array<Object>} cards - Liste des cartes
   */
  SET_CARDS(state, cards) {
    state.cards = cards
  },

  /**
   * Ajoute une nouvelle carte
   * @param {Object} state - État du module
   * @param {Object} card - Carte à ajouter
   */
  ADD_CARD(state, card) {
    state.cards.push(card)
  },

  /**
   * Met à jour une carte existante
   * @param {Object} state - État du module
   * @param {Object} updatedCard - Carte mise à jour
   */
  UPDATE_CARD(state, updatedCard) {
    const index = state.cards.findIndex(card => card.id === updatedCard.id)
    if (index !== -1) {
      state.cards.splice(index, 1, updatedCard)
    }
  },

  /**
   * Supprime une carte
   * @param {Object} state - État du module
   * @param {string|number} cardId - ID de la carte à supprimer
   */
  DELETE_CARD(state, cardId) {
    state.cards = state.cards.filter(card => card.id !== cardId)
  },

  /**
   * Définit la carte sélectionnée
   * @param {Object} state - État du module
   * @param {Object|null} card - Carte à sélectionner
   */
  SET_SELECTED_CARD(state, card) {
    state.selectedCard = card
  },

  /**
   * Définit le statut de chargement
   * @param {Object} state - État du module
   * @param {boolean} isLoading - Statut de chargement
   */
  SET_LOADING(state, isLoading) {
    state.isLoading = isLoading
  },

  /**
   * Définit le message d'erreur
   * @param {Object} state - État du module
   * @param {string|null} error - Message d'erreur
   */
  SET_ERROR(state, error) {
    state.error = error
  },

  /**
   * Définit les filtres
   * @param {Object} state - État du module
   * @param {Object} filters - Filtres à appliquer
   */
  SET_FILTERS(state, filters) {
    state.filters = { ...state.filters, ...filters }
  },

  /**
   * Réinitialise les filtres
   * @param {Object} state - État du module
   */
  RESET_FILTERS(state) {
    state.filters = {
      search: '',
      category: null
    }
  }
}

/**
 * Actions asynchrones
 */
const actions = {
  /**
   * Récupère la liste des cartes depuis l'API
   * @param {Object} context - Contexte Vuex
   * @returns {Promise<Array>}
   */
  async fetchCards({ commit }) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      // Simulation d'un appel API
      // À remplacer par un vrai appel : const response = await api.get('/cards')
      const mockCards = [
        { id: 1, title: 'Carte 1', description: 'Description 1', category: 'A' },
        { id: 2, title: 'Carte 2', description: 'Description 2', category: 'B' },
        { id: 3, title: 'Carte 3', description: 'Description 3', category: 'A' }
      ]
      
      await new Promise(resolve => setTimeout(resolve, 500)) // Simulation délai réseau
      
      commit('SET_CARDS', mockCards)
      return mockCards
    } catch (error) {
      const errorMessage = 'Erreur lors de la récupération des cartes'
      commit('SET_ERROR', errorMessage)
      throw new Error(errorMessage)
    } finally {
      commit('SET_LOADING', false)
    }
  },

  /**
   * Récupère une carte par son ID
   * @param {Object} context - Contexte Vuex
   * @param {string|number} cardId - ID de la carte
   * @returns {Promise<Object>}
   */
  async fetchCardById({ commit, getters }, cardId) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      // Vérification si la carte est déjà dans le store
      const cachedCard = getters.getCardById(cardId)
      if (cachedCard) {
        commit('SET_SELECTED_CARD', cachedCard)
        return cachedCard
      }
      
      // Simulation d'un appel API
      // À remplacer par : const response = await api.get(`/cards/${cardId}`)
      const mockCard = { 
        id: cardId, 
        title: `Carte ${cardId}`, 
        description: `Description ${cardId}`, 
        category: 'A' 
      }
      
      await new Promise(resolve => setTimeout(resolve, 300))
      
      commit('SET_SELECTED_CARD', mockCard)
      return mockCard
    } catch (error) {
      const errorMessage = `Erreur lors de la récupération de la carte ${cardId}`
      commit('SET_ERROR', errorMessage)
      throw new Error(errorMessage)
    } finally {
      commit('SET_LOADING', false)
    }
  },

  /**
   * Crée une nouvelle carte
   * @param {Object} context - Contexte Vuex
   * @param {Object} cardData - Données de la carte à créer
   * @returns {Promise<Object>}
   */
  async createCard({ commit }, cardData) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      // Simulation d'un appel API
      // À remplacer par : const response = await api.post('/cards', cardData)
      const newCard = {
        ...cardData,
        id: Date.now(), // Génération d'un ID temporaire
        createdAt: new Date().toISOString()
      }
      
      await new Promise(resolve => setTimeout(resolve, 400))
      
      commit('ADD_CARD', newCard)
      return newCard
    } catch (error) {
      const errorMessage = 'Erreur lors de la création de la carte'
      commit('SET_ERROR', errorMessage)
      throw new Error(errorMessage)
    } finally {
      commit('SET_LOADING', false)
    }
  },

  /**
   * Met à jour une carte existante
   * @param {Object} context - Contexte Vuex
   * @param {Object} cardData - Données de la carte à mettre à jour
   * @returns {Promise<Object>}
   */
  async updateCard({ commit }, cardData) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      // Simulation d'un appel API
      // À remplacer par : const response = await api.put(`/cards/${cardData.id}`, cardData)
      const updatedCard = {
        ...cardData,
        updatedAt: new Date().toISOString()
      }
      
      await new Promise(resolve => setTimeout(resolve, 400))
      
      commit('UPDATE_CARD', updatedCard)
      
      // Met à jour la carte sélectionnée si c'est la même
      commit('SET_SELECTED_CARD', updatedCard)
      
      return updatedCard
    } catch (error) {
      const errorMessage = `Erreur lors de la mise à jour de la carte ${cardData.id}`
      commit('SET_ERROR', errorMessage)
      throw new Error(errorMessage)
    } finally {
      commit('SET_LOADING', false)
    }
  },

  /**
   * Supprime une carte
   * @param {Object} context - Contexte Vuex
   * @param {string|number} cardId - ID de la carte à supprimer
   * @returns {Promise<void>}
   */
  async deleteCard({ commit }, cardId) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      // Simulation d'un appel API
      // À remplacer par : await api.delete(`/cards/${cardId}`)
      
      await new Promise(resolve => setTimeout(resolve, 300))
      
      commit('DELETE_CARD', cardId)
      
      // Réinitialise la sélection si la carte supprimée était sélectionnée
      if (state.selectedCard?.id === cardId) {
        commit('SET_SELECTED_CARD', null)
      }
    } catch (error) {
      const errorMessage = `Erreur lors de la suppression de la carte ${cardId}`
      commit('SET_ERROR', errorMessage)
      throw new Error(errorMessage)
    } finally {
      commit('SET_LOADING', false)
    }
  },

  /**
   * Applique des filtres aux cartes
   * @param {Object} context - Contexte Vuex
   * @param {Object} filters - Filtres à appliquer
   */
  applyFilters({ commit }, filters) {
    commit('SET_FILTERS', filters)
  },

  /**
   * Réinitialise les filtres
   * @param {Object} context - Contexte Vuex
   */
  resetFilters({ commit }) {
    commit('RESET_FILTERS')
  },

  /**
   * Sélectionne une carte
   * @param {Object} context - Contexte Vuex
   * @param {Object|null} card - Carte à sélectionner
   */
  selectCard({ commit }, card) {
    commit('SET_SELECTED_CARD', card)
  },

  /**
   * Efface le message d'erreur
   * @param {Object} context - Contexte Vuex
   */
  clearError({ commit }) {
    commit('SET_ERROR', null)
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}