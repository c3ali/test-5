// frontend/src/store/modules/label.js
import api from '@/services/api';

// Constants for mutation types
const MUTATIONS = {
  SET_LABELS: 'SET_LABELS',
  SET_LABEL: 'SET_LABEL',
  ADD_LABEL: 'ADD_LABEL',
  UPDATE_LABEL: 'UPDATE_LABEL',
  DELETE_LABEL: 'DELETE_LABEL',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  RESET_ERROR: 'RESET_ERROR',
};

// Initial state
const initialState = {
  items: [],
  selectedItem: null,
  loading: false,
  error: null,
};

// Getters
const getters = {
  allLabels: (state) => state.items,
  selectedLabel: (state) => state.selectedItem,
  isLoading: (state) => state.loading,
  getError: (state) => state.error,
  getLabelById: (state) => (id) => state.items.find((label) => label.id === id),
  getLabelByName: (state) => (name) => state.items.find((label) => label.name === name),
  sortedLabels: (state) => {
    return [...state.items].sort((a, b) => a.name.localeCompare(b.name));
  },
};

// Mutations
const mutations = {
  [MUTATIONS.SET_LABELS](state, labels) {
    state.items = labels;
  },
  [MUTATIONS.SET_LABEL](state, label) {
    state.selectedItem = label;
  },
  [MUTATIONS.ADD_LABEL](state, label) {
    state.items.push(label);
  },
  [MUTATIONS.UPDATE_LABEL](state, updatedLabel) {
    const index = state.items.findIndex((label) => label.id === updatedLabel.id);
    if (index !== -1) {
      state.items.splice(index, 1, updatedLabel);
    }
  },
  [MUTATIONS.DELETE_LABEL](state, labelId) {
    state.items = state.items.filter((label) => label.id !== labelId);
  },
  [MUTATIONS.SET_LOADING](state, loading) {
    state.loading = loading;
  },
  [MUTATIONS.SET_ERROR](state, error) {
    state.error = error;
  },
  [MUTATIONS.RESET_ERROR](state) {
    state.error = null;
  },
};

// Actions
const actions = {
  // Load all labels
  async fetchLabels({ commit }) {
    commit(MUTATIONS.SET_LOADING, true);
    commit(MUTATIONS.RESET_ERROR);
    try {
      const response = await api.get('/labels');
      commit(MUTATIONS.SET_LABELS, response.data);
      return response.data;
    } catch (error) {
      commit(MUTATIONS.SET_ERROR, error.message || 'Failed to fetch labels');
      throw error;
    } finally {
      commit(MUTATIONS.SET_LOADING, false);
    }
  },

  // Load a single label by ID
  async fetchLabelById({ commit }, labelId) {
    commit(MUTATIONS.SET_LOADING, true);
    commit(MUTATIONS.RESET_ERROR);
    try {
      const response = await api.get(`/labels/${labelId}`);
      commit(MUTATIONS.SET_LABEL, response.data);
      return response.data;
    } catch (error) {
      commit(MUTATIONS.SET_ERROR, error.message || `Failed to fetch label with id ${labelId}`);
      throw error;
    } finally {
      commit(MUTATIONS.SET_LOADING, false);
    }
  },

  // Create a new label
  async createLabel({ commit }, labelData) {
    commit(MUTATIONS.SET_LOADING, true);
    commit(MUTATIONS.RESET_ERROR);
    try {
      const response = await api.post('/labels', labelData);
      commit(MUTATIONS.ADD_LABEL, response.data);
      return response.data;
    } catch (error) {
      commit(MUTATIONS.SET_ERROR, error.message || 'Failed to create label');
      throw error;
    } finally {
      commit(MUTATIONS.SET_LOADING, false);
    }
  },

  // Update an existing label
  async updateLabel({ commit }, { id, updateData }) {
    commit(MUTATIONS.SET_LOADING, true);
    commit(MUTATIONS.RESET_ERROR);
    try {
      const response = await api.put(`/labels/${id}`, updateData);
      commit(MUTATIONS.UPDATE_LABEL, response.data);
      return response.data;
    } catch (error) {
      commit(MUTATIONS.SET_ERROR, error.message || `Failed to update label with id ${id}`);
      throw error;
    } finally {
      commit(MUTATIONS.SET_LOADING, false);
    }
  },

  // Delete a label
  async deleteLabel({ commit }, labelId) {
    commit(MUTATIONS.SET_LOADING, true);
    commit(MUTATIONS.RESET_ERROR);
    try {
      await api.delete(`/labels/${labelId}`);
      commit(MUTATIONS.DELETE_LABEL, labelId);
      return labelId;
    } catch (error) {
      commit(MUTATIONS.SET_ERROR, error.message || `Failed to delete label with id ${labelId}`);
      throw error;
    } finally {
      commit(MUTATIONS.SET_LOADING, false);
    }
  },

  // Select a label
  selectLabel({ commit }, label) {
    commit(MUTATIONS.SET_LABEL, label);
  },

  // Clear selection
  clearSelection({ commit }) {
    commit(MUTATIONS.SET_LABEL, null);
  },

  // Clear error
  clearError({ commit }) {
    commit(MUTATIONS.RESET_ERROR);
  },
};

export default {
  namespaced: true,
  state: initialState,
  getters,
  mutations,
  actions,
};
```

### Points clés de ce module :

1. **Structure Vuex standard** : Utilise `state`, `getters`, `mutations`, `actions`
2. **Namespaced** : Activé pour éviter les conflits avec d'autres modules
3. **Constantes** : Tous les types de mutations sont définis en constantes pour maintenabilité
4. **Gestion des erreurs** : Capture et stocke les erreurs pour les afficher en UI
5. **État de chargement** : Permet d'afficher des indicateurs de chargement
6. **API dédiée** : Utilise un service API centralisé (à adapter selon votre projet)
7. **Getters utilitaires** : Fournit des méthodes pour rechercher, trier et filtrer les étiquettes

### Détails techniques :

- **API Service** : suppose un fichier `src/services/api.js` qui gère la configuration Axios
- **Structure des données** : suppose que les étiquettes ont au minimum un `id` et un `name`
- **Namespace** : le module est accessible via `this.$store.state.label` ou les helpers `mapState('label', ...)`
- **Gestion des erreurs** : stocke le message d'erreur pour affichage dans les composants