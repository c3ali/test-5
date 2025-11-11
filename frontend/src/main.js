// frontend/src/main.js
// Point d'entrée principal de l'application Vue.js

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import './assets/styles/main.css' // Import des styles globaux (optionnel)

/**
 * Crée et configure l'instance de l'application Vue
 */
const createVueApp = () => {
  // Initialisation de l'application avec le composant racine
  const app = createApp(App)

  // Installation du store (Vuex/Pinia) pour la gestion d'état
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
```

### Version alternative avec configuration avancée

Si vous avez besoin d'une configuration plus complète avec gestion d'erreurs et plugins supplémentaires :

```javascript
// frontend/src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import { createPinia } from 'pinia' // Si vous utilisez Pinia (recommandé pour Vue 3)
import { createHead } from '@vueuse/head' // Pour la gestion du <head> (optionnel)

// Import des styles globaux
import './assets/styles/tailwind.css' // Exemple avec TailwindCSS
import './assets/styles/main.scss' // Ou SCSS

/**
 * Initialisation de l'application Vue
 */
async function initApp() {
  try {
    const app = createApp(App)
    
    // Utilisation de Pinia (store moderne pour Vue 3)
    const pinia = createPinia()
    app.use(pinia)
    
    // Remplacer par ceci si vous utilisez encore Vuex :
    // app.use(store)
    
    // Installation du router
    app.use(router)

    // Plugin pour la gestion du head (meta tags, etc.)
    const head = createHead()
    app.use(head)

    // Directive globale d'exemple
    app.directive('focus', {
      mounted(el) {
        el.focus()
      }
    })

    // Propriété globale
    app.config.globalProperties.$filters = {
      capitalize(value) {
        if (!value) return ''
        return value.toString().charAt(0).toUpperCase() + value.slice(1)
      }
    }

    // Configuration du mode développement
    if (process.env.NODE_ENV === 'development') {
      app.config.devtools = true
      app.config.performance = true
    }

    // Montage de l'application
    app.mount('#app')

    console.log('✅ Application Vue.js démarrée avec succès')
    
    return app
  } catch (error) {
    console.error('❌ Erreur lors du démarrage de l\'application:', error)
    throw error
  }
}

// Démarrage de l'application
const app = await initApp()

export default app
```

**Note importante** : Pour Vue 3, il est recommandé d'utiliser **Pinia** plutôt que Vuex comme store. Le code ci-dessus montre les deux approches. Assurez-vous d'installer les dépendances correspondantes :

```bash
# Pour Pinia (recommandé)
npm install pinia vue-router@4

# Pour Vuex (legacy)
npm install vuex@next vue-router@4
```

Le fichier attend que vous ayez :
- `frontend/src/App.vue` (composant racine)
- `frontend/src/router/index.js` (configuration du router)
- `frontend/src/store/index.js` (configuration du store)