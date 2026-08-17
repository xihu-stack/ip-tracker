import { createRouter, createWebHistory } from 'vue-router'

// 路由懒加载：每个页面独立分包，首屏只加载登录页所需的代码
const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { public: true } },
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
  { path: '/employees', name: 'Employees', component: () => import('../views/Employees.vue') },
  { path: '/history', name: 'History', component: () => import('../views/History.vue') },
  { path: '/guide', name: 'Guide', component: () => import('../views/Guide.vue') },
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
