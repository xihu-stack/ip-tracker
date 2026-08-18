import { createRouter, createWebHistory } from 'vue-router'

// 路由懒加载：每个页面独立分包，首屏只加载登录页所需的代码
const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { public: true } },
  // 管理员密码登录独立入口（SSO 启用时普通 /login 只走统一门户）
  { path: '/admin-login', name: 'AdminLogin', component: () => import('../views/Login.vue'), meta: { public: true } },
  { path: '/sso', name: 'SsoCallback', component: () => import('../views/SsoCallback.vue'), meta: { public: true } },
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
  { path: '/employees', name: 'Employees', component: () => import('../views/Employees.vue') },
  { path: '/history', name: 'History', component: () => import('../views/History.vue') },
  { path: '/location', name: 'Location', component: () => import('../views/Location.vue') },
  { path: '/guide', name: 'Guide', component: () => import('../views/Guide.vue') },
  { path: '/settings', name: 'Settings', component: () => import('../views/Settings.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.public) {
    next(token && (to.path === '/login' || to.path === '/admin-login') ? '/' : undefined)
  } else {
    // 记住原路径，登录（密码或 SSO）后回到这里
    next(token ? undefined : { path: '/login', query: { redirect: to.fullPath } })
  }
})

export default router
