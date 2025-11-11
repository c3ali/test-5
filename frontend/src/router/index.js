import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import About from '@/views/About.vue'
import Login from '@/views/auth/Login.vue'
import Dashboard from '@/views/dashboard/Dashboard.vue'
import NotFound from '@/views/errors/NotFound.vue'
import store from '@/store'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: {
      title: 'Accueil',
      requiresAuth: false
    }
  },
  {
    path: '/about',
    name: 'About',
    component: About,
    meta: {
      title: 'À propos',
      requiresAuth: false
    }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      title: 'Connexion',
      requiresAuth: false,
      guestOnly: true
    }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: {
      title: 'Tableau de bord',
      requiresAuth: true
    }
  },
  // Routes avec lazy loading (chargement à la demande)
  {
    path: '/users',
    name: 'Users',
    component: () => import('@/views/users/UsersList.vue'),
    meta: {
      title: 'Utilisateurs',
      requiresAuth: true,
      roles: ['admin']
    }
  },
  {
    path: '/profile/:id?',
    name: 'Profile',
    component: () => import('@/views/profile/Profile.vue'),
    props: true,
    meta: {
      title: 'Profil',
      requiresAuth: true
    }
  },
  // Redirections
  {
    path: '/home',
    redirect: '/'
  },
  // Route 404 - Doit être la dernière
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound,
    meta: {
      title: 'Page non trouvée'
    }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // Retourne à la position précédente si le bouton "précédent" est utilisé
    if (savedPosition) {
      return savedPosition
    }
    // Sinon, scroll en haut de la page
    return { top: 0, behavior: 'smooth' }
  }
})

// Guards de navigation
router.beforeEach(async (to, from, next) => {
  // Mettre à jour le titre de la page
  document.title = `${to.meta.title || 'App'} - Mon Application`

  // Vérifier si la route nécessite une authentification
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const isAuthenticated = store.getters['auth/isAuthenticated']
  const userRole = store.getters['auth/userRole']

  // Vérifier si la route est réservée aux invités (non connectés)
  if (to.meta.guestOnly && isAuthenticated) {
    return next('/dashboard')
  }

  if (requiresAuth && !isAuthenticated) {
    // Rediriger vers la page de login si non authentifié
    return next({
      path: '/login',
      query: { redirect: to.fullPath }
    })
  }

  // Vérifier les rôles si nécessaire
  if (to.meta.roles && !to.meta.roles.includes(userRole)) {
    return next('/dashboard')
  }

  next()
})

// Guard après la navigation
router.afterEach((to, from) => {
  // Log de navigation (utile pour l'analytics)
  console.log(`[Router] Navigating from "${from.path}" to "${to.path}"`)
})

export default router
```

## Explications clés :

1. **Structure des routes** : Chaque route a un `path`, `name`, `component` et des `meta` données
2. **Meta champs** :
   - `title` : Pour le titre de la page
   - `requiresAuth` : Route protégée
   - `guestOnly` : Accessible uniquement aux non-connectés
   - `roles` : Permissions par rôle

3. **Lazy loading** : Utilisation de `() => import()` pour charger les composants à la demande

4. **Guards de navigation** :
   - Vérification d'authentification
   - Gestion des rôles utilisateur
   - Redirection automatique

5. **Scroll behavior** : Maintient la position lors de la navigation ou scroll en haut

6. **404 handling** : Capture toutes les routes non définies

7. **Variables d'environnement** : Utilise `import.meta.env.BASE_URL` pour la base URL

Pour utiliser ce routeur dans `main.js` :

```javascript
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

createApp(App)
  .use(store)
  .use(router)
  .mount('#app')