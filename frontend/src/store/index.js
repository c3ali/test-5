import { createStore } from 'vuex'

export default createStore({
  state: {
    appVersion: '1.0.0',
    isLoading: false
  },
  mutations: {
    SET_LOADING(state, status) {
      state.isLoading = status
    }
  },
  actions: {
    setLoading({ commit }, status) {
      commit('SET_LOADING', status)
    }
  },
  getters: {
    appVersion: state => state.appVersion,
    isLoading: state => state.isLoading
  },
  modules: {}
})
