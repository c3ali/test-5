Voici le code pour un store Vuex centralisé avec modules :

### `frontend/src/store/index.js`
```javascript
import Vue from 'vue';
import Vuex from 'vuex';
import auth from './modules/auth';
import users from './modules/users';
import products from './modules/products';
import cart from './modules/cart';

Vue.use(Vuex);

export default new Vuex.Store({
  // État global partagé entre tous les modules
  state: {
    appVersion: '1.0.0',
    isLoading: false,
    notification: {
      type: null,
      message: null,
      visible: false
    }
  },

  // Mutations globales
  mutations: {
    SET_LOADING(state, status) {
      state.isLoading = status;
    },
    SHOW_NOTIFICATION(state, { type, message }) {
      state.notification = {
        type,
        message,
        visible: true
      };
    },
    HIDE_NOTIFICATION(state) {
      state.notification.visible = false;
    }
  },

  // Actions globales
  actions: {
    showNotification({ commit }, payload) {
      commit('SHOW_NOTIFICATION', payload);
      setTimeout(() => {
        commit('HIDE_NOTIFICATION');
      }, 5000);
    }
  },

  // Getters globaux
  getters: {
    appVersion: state => state.appVersion,
    isLoading: state => state.isLoading,
    notification: state => state.notification
  },

  // Modules pour chaque entité
  modules: {
    auth,
    users,
    products,
    cart
  },

  // Active les modules namespaced pour mieux organiser le store
  strict: process.env.NODE_ENV !== 'production'
});
```

---

### Exemples de modules à créer dans le dossier `frontend/src/store/modules/` :

#### `frontend/src/store/modules/auth.js`
```javascript
import AuthService from '@/services/AuthService';

const state = {
  token: localStorage.getItem('token') || null,
  user: JSON.parse(localStorage.getItem('user')) || null,
  isAuthenticated: !!localStorage.getItem('token')
};

const mutations = {
  SET_TOKEN(state, token) {
    state.token = token;
    state.isAuthenticated = !!token;
  },
  SET_USER(state, user) {
    state.user = user;
  },
  CLEAR_AUTH(state) {
    state.token = null;
    state.user = null;
    state.isAuthenticated = false;
  }
};

const actions = {
  async login({ commit, dispatch }, credentials) {
    try {
      const response = await AuthService.login(credentials);
      const { token, user } = response.data;
      
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));
      
      commit('SET_TOKEN', token);
      commit('SET_USER', user);
      
      dispatch('showNotification', {
        type: 'success',
        message: 'Connexion réussie'
      }, { root: true });
      
      return Promise.resolve(user);
    } catch (error) {
      dispatch('showNotification', {
        type: 'error',
        message: error.response?.data?.message || 'Erreur de connexion'
      }, { root: true });
      
      return Promise.reject(error);
    }
  },

  logout({ commit, dispatch }) {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    commit('CLEAR_AUTH');
    
    dispatch('showNotification', {
      type: 'info',
      message: 'Déconnexion réussie'
    }, { root: true });
  },

  async refreshToken({ commit, dispatch }) {
    try {
      const response = await AuthService.refreshToken();
      const { token } = response.data;
      
      localStorage.setItem('token', token);
      commit('SET_TOKEN', token);
      
      return Promise.resolve(token);
    } catch (error) {
      dispatch('logout');
      return Promise.reject(error);
    }
  }
};

const getters = {
  token: state => state.token,
  user: state => state.user,
  isAuthenticated: state => state.isAuthenticated,
  userRole: state => state.user?.role || null
};

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
};
```

#### `frontend/src/store/modules/users.js`
```javascript
import UserService from '@/services/UserService';

const state = {
  users: [],
  currentUser: null,
  totalUsers: 0,
  pagination: {
    page: 1,
    limit: 10
  }
};

const mutations = {
  SET_USERS(state, users) {
    state.users = users;
  },
  SET_CURRENT_USER(state, user) {
    state.currentUser = user;
  },
  SET_TOTAL_USERS(state, total) {
    state.totalUsers = total;
  },
  SET_PAGINATION(state, pagination) {
    state.pagination = { ...state.pagination, ...pagination };
  },
  ADD_USER(state, user) {
    state.users.push(user);
  },
  UPDATE_USER(state, updatedUser) {
    const index = state.users.findIndex(u => u.id === updatedUser.id);
    if (index !== -1) {
      state.users.splice(index, 1, updatedUser);
    }
  },
  DELETE_USER(state, userId) {
    state.users = state.users.filter(u => u.id !== userId);
  }
};

const actions = {
  async fetchUsers({ commit, state }, params = {}) {
    try {
      commit('SET_LOADING', true, { root: true });
      const response = await UserService.getAll({
        page: state.pagination.page,
        limit: state.pagination.limit,
        ...params
      });
      
      commit('SET_USERS', response.data.users);
      commit('SET_TOTAL_USERS', response.data.total);
      return Promise.resolve(response.data);
    } catch (error) {
      commit('SHOW_NOTIFICATION', {
        type: 'error',
        message: 'Erreur lors du chargement des utilisateurs'
      }, { root: true });
      return Promise.reject(error);
    } finally {
      commit('SET_LOADING', false, { root: true });
    }
  },

  async fetchUser({ commit }, userId) {
    try {
      const response = await UserService.getById(userId);
      commit('SET_CURRENT_USER', response.data);
      return Promise.resolve(response.data);
    } catch (error) {
      return Promise.reject(error);
    }
  },

  async createUser({ commit, dispatch }, userData) {
    try {
      const response = await UserService.create(userData);
      commit('ADD_USER', response.data);
      
      dispatch('showNotification', {
        type: 'success',
        message: 'Utilisateur créé avec succès'
      }, { root: true });
      
      return Promise.resolve(response.data);
    } catch (error) {
      dispatch('showNotification', {
        type: 'error',
        message: error.response?.data?.message || 'Erreur de création'
      }, { root: true });
      
      return Promise.reject(error);
    }
  },

  async updateUser({ commit, dispatch }, { userId, userData }) {
    try {
      const response = await UserService.update(userId, userData);
      commit('UPDATE_USER', response.data);
      
      dispatch('showNotification', {
        type: 'success',
        message: 'Utilisateur mis à jour'
      }, { root: true });
      
      return Promise.resolve(response.data);
    } catch (error) {
      dispatch('showNotification', {
        type: 'error',
        message: error.response?.data?.message || 'Erreur de mise à jour'
      }, { root: true });
      
      return Promise.reject(error);
    }
  },

  async deleteUser({ commit, dispatch }, userId) {
    try {
      await UserService.delete(userId);
      commit('DELETE_USER', userId);
      
      dispatch('showNotification', {
        type: 'success',
        message: 'Utilisateur supprimé'
      }, { root: true });
      
      return Promise.resolve();
    } catch (error) {
      dispatch('showNotification', {
        type: 'error',
        message: error.response?.data?.message || 'Erreur de suppression'
      }, { root: true });
      
      return Promise.reject(error);
    }
  }
};

const getters = {
  users: state => state.users,
  currentUser: state => state.currentUser,
  totalUsers: state => state.totalUsers,
  pagination: state => state.pagination,
  getUserById: state => id => state.users.find(u => u.id === id)
};

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
};
```

#### `frontend/src/store/modules/products.js`
```javascript
import ProductService from '@/services/ProductService';

const state = {
  products: [],
  categories: [],
  currentProduct: null,
  filters: {
    search: '',
    category: null,
    sortBy: 'name',
    sortOrder: 'asc'
  }
};

const mutations = {
  SET_PRODUCTS(state, products) {
    state.products = products;
  },
  SET_CATEGORIES(state, categories) {
    state.categories = categories;
  },
  SET_CURRENT_PRODUCT(state, product) {
    state.currentProduct = product;
  },
  SET_FILTERS(state, filters) {
    state.filters = { ...state.filters, ...filters };
  },
  ADD_PRODUCT(state, product) {
    state.products.push(product);
  },
  UPDATE_PRODUCT(state, updatedProduct) {
    const index = state.products.findIndex(p => p.id === updatedProduct.id);
    if (index !== -1) {
      state.products.splice(index, 1, updatedProduct);
    }
  },
  DELETE_PRODUCT(state, productId) {
    state.products = state.products.filter(p => p.id !== productId);
  }
};

const actions = {
  async fetchProducts({ commit, state }) {
    try {
      commit('SET_LOADING', true, { root: true });
      const response = await ProductService.getAll(state.filters);
      
      commit('SET_PRODUCTS', response.data.products);
      return Promise.resolve(response.data);
    } catch (error) {
      commit('SHOW_NOTIFICATION', {
        type: 'error',
        message: 'Erreur lors du chargement des produits'
      }, { root: true });
      return Promise.reject(error);
    } finally {
      commit('SET_LOADING', false, { root: true });
    }
  },

  async fetchProduct({ commit }, productId) {
    try {
      const response = await ProductService.getById(productId);
      commit('SET_CURRENT_PRODUCT', response.data);
      return Promise.resolve(response.data);
    } catch (error) {
      return Promise.reject(error);
    }
  },

  async fetchCategories({ commit }) {
    try {
      const response = await ProductService.getCategories();
      commit('SET_CATEGORIES', response.data);
      return Promise.resolve(response.data);
    } catch (error) {
      return Promise.reject(error);
    }
  },

  async createProduct({ commit, dispatch }, productData) {
    try {
      const response = await ProductService.create(productData);
      commit('ADD_PRODUCT', response.data);
      
      dispatch('showNotification', {
        type: 'success',
        message: 'Produit créé avec succès'
      }, { root: true });
      
      return Promise.resolve(response.data);
    } catch (error) {
      dispatch('showNotification', {
        type: 'error',
        message: error.response?.data?.message || 'Erreur de création'
      }, { root: true });
      
      return Promise.reject(error);
    }
  },

  async updateProduct({ commit, dispatch }, { productId, productData }) {
    try {
      const response = await ProductService.update(productId, productData);
      commit('UPDATE_PRODUCT', response.data);
      
      dispatch('showNotification', {
        type: 'success',
        message: 'Produit mis à jour'
      }, { root: true });
      
      return Promise.resolve(response.data);
    } catch (error) {
      dispatch('showNotification', {
        type: 'error',
        message: error.response?.data?.message || 'Erreur de mise à jour'
      }, { root: true });
      
      return Promise.reject(error);
    }
  },

  async deleteProduct({ commit, dispatch }, productId) {
    try {
      await ProductService.delete(productId);
      commit('DELETE_PRODUCT', productId);
      
      dispatch('showNotification', {
        type: 'success',
        message: 'Produit supprimé'
      }, { root: true });
      
      return Promise.resolve();
    } catch (error) {
      dispatch('showNotification', {
        type: 'error',
        message: error.response?.data?.message || 'Erreur de suppression'
      }, { root: true });
      
      return Promise.reject(error);
    }
  },

  updateFilters({ commit }, filters) {
    commit('SET_FILTERS', filters);
  }
};

const getters = {
  products: state => state.products,
  categories: state => state.categories,
  currentProduct: state => state.currentProduct,
  filters: state => state.filters,
  filteredProducts: state => {
    // Logique de filtrage côté client si nécessaire
    return state.products;
  },
  getProductById: state => id => state.products.find(p => p.id === id)
};

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
};
```

#### `frontend/src/store/modules/cart.js`
```javascript
const state = {
  items: JSON.parse(localStorage.getItem('cart')) || [],
  checkoutStatus: null
};

const mutations = {
  ADD_TO_CART(state, { product, quantity = 1 }) {
    const existingItem = state.items.find(item => item.product.id === product.id);
    
    if (existingItem) {
      existingItem.quantity += quantity;
    } else {
      state.items.push({ product, quantity });
    }
    
    localStorage.setItem('cart', JSON.stringify(state.items));
  },

  REMOVE_FROM_CART(state, productId) {
    state.items = state.items.filter(item => item.product.id !== productId);
    localStorage.setItem('cart', JSON.stringify(state.items));
  },

  UPDATE_QUANTITY(state, { productId, quantity }) {
    const item = state.items.find(item => item.product.id === productId);
    if (item) {
      item.quantity = quantity;
      localStorage.setItem('cart', JSON.stringify(state.items));
    }
  },

  CLEAR_CART(state) {
    state.items = [];
    state.checkoutStatus = null;
    localStorage.removeItem('cart');
  },

  SET_CHECKOUT_STATUS(state, status) {
    state.checkoutStatus = status;
  }
};

const actions = {
  addToCart({ commit, dispatch }, payload) {
    commit('ADD_TO_CART', payload);
    
    dispatch('showNotification', {
      type: 'success',
      message: 'Produit ajouté au panier'
    }, { root: true });
  },

  removeFromCart({ commit, dispatch }, productId) {
    commit('REMOVE_FROM_CART', productId);
    
    dispatch('showNotification', {
      type: 'info',
      message: 'Produit retiré du panier'
    }, { root: true });
  },

  updateQuantity({ commit }, { productId, quantity }) {
    if (quantity <= 0) {
      commit('REMOVE_FROM_CART', productId);
    } else {
      commit('UPDATE_QUANTITY', { productId, quantity });
    }
  },

  async checkout({ commit, dispatch, state }) {
    commit('SET_LOADING', true, { root: true });
    
    try {
      // Appel API pour le checkout
      // await OrderService.create(state.items);
      
      commit('CLEAR_CART');
      commit('SET_CHECKOUT_STATUS', 'success');
      
      dispatch('showNotification', {
        type: 'success',
        message: 'Commande passée avec succès !'
      }, { root: true });
      
      return Promise.resolve();
    } catch (error) {
      commit('SET_CHECKOUT_STATUS', 'failed');
      
      dispatch('showNotification', {
        type: 'error',
        message: 'Erreur lors du paiement'
      }, { root: true });
      
      return Promise.reject(error);
    } finally {
      commit('SET_LOADING', false, { root: true });
    }
  }
};

const getters = {
  items: state => state.items,
  cartTotal: state => {
    return state.items.reduce((total, item) => {
      return total + (item.product.price * item.quantity);
    }, 0);
  },
  cartCount: state => {
    return state.items.reduce((count, item) => count + item.quantity, 0);
  },
  checkoutStatus: state => state.checkoutStatus,
  isInCart: state => productId => {
    return state.items.some(item => item.product.id === productId);
  }
};

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
};
```

### Structure recommandée :
```
frontend/src/
├── store/
│   ├── index.js
│   └── modules/
│       ├── auth.js
│       ├── users.js
│       ├── products.js
│       └── cart.js
```

Ce store centralisé utilise :
- **Modules namespaced** pour éviter les conflits de nommage
- **LocalStorage** pour la persistance de l'authentification et du panier
- **Notifications globales** via des actions root
- **Gestion du chargement** global
- **Services API** séparés pour chaque entité
- **Getters** pour des accès optimisés aux données
- **Gestion d'erreurs** centralisée avec notifications