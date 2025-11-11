// frontend/src/main.js
// Point d'entrée principal de l'application Vue.js

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

/**
 * Crée et configure l'instance de l'application Vue
 */
const createVueApp = () => {
  // Initialisation de l'application avec le composant racine
  const app = createApp(App)

  // Installation du store (Vuex) pour la gestion d'état
  app.use(store)

  // Installation du router pour la navigation
  app.use(router)

  // Montage de l'application sur l'élément DOM avec l'id 'app'
  app.mount('#app')

  return app
}

// Création et démarrage de l'application
const app = createVueApp()

// Export pour utilisation potentielle dans des tests ou autres modules
export default app
