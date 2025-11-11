import { createRouter, createWebHistory } from 'vue-router'
import UsersService from '../api/users'

const routes = [
  {
    path: '/',
    redirect: '/boards'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../components/Login.vue'),
    meta: { title: 'Connexion - Kanban Board', requiresGuest: true }
  },
  {
    path: '/boards',
    name: 'BoardList',
    component: () => import('../views/BoardList.vue'),
    meta: { title: 'Mes Tableaux - Kanban Board', requiresAuth: true }
  },
  {
    path: '/board/:id',
    name: 'KanbanBoard',
    component: () => import('../views/KanbanBoard.vue'),
    meta: { title: 'Tableau Kanban', requiresAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue'),
    meta: { title: '404' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard pour l'authentification
router.beforeEach((to, from, next) => {
  document.title = to.meta.title || 'Kanban Board'

  const isAuthenticated = UsersService.isAuthenticated()

  // Si la route nécessite l'authentification
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
  }
  // Si la route est pour les invités (login) et l'utilisateur est déjà connecté
  else if (to.meta.requiresGuest && isAuthenticated) {
    next('/boards')
  }
  // Sinon, continuer normalement
  else {
    next()
  }
})

export default router
