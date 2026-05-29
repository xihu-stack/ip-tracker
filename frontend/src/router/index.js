import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Employees from '../views/Employees.vue'
import History from '../views/History.vue'
import Guide from '../views/Guide.vue'

const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/employees', name: 'Employees', component: Employees },
  { path: '/history', name: 'History', component: History },
  { path: '/guide', name: 'Guide', component: Guide },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
