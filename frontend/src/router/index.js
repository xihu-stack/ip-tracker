import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Employees from '../views/Employees.vue'
import History from '../views/History.vue'
import Guide from '../views/Guide.vue'
import Login from '../views/Login.vue'

const routes = [
  { path: '/login', name: 'Login', component: Login, meta: { public: true } },
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/employees', name: 'Employees', component: Employees },
  { path: '/history', name: 'History', component: History },
  { path: '/guide', name: 'Guide', component: Guide },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.public) {
    next(token && to.path === '/login' ? '/' : undefined)
  } else {
    next(token ? undefined : '/login')
  }
})

export default router
