<template>
  <el-container class="app-container">
    <el-aside v-if="showSidebar" width="220px" class="sidebar">
      <div class="sidebar-logo">
        <img class="logo-img" src="/logo.png" alt="Sellixon" />
        <div class="logo-text">
          <span class="logo-sub">IP 定位追踪平台</span>
        </div>
      </div>
      <el-menu :default-active="currentPath" router class="sidebar-menu">
        <el-menu-item index="/">
          <el-icon><Monitor /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/employees">
          <el-icon><User /></el-icon>
          <span>员工列表</span>
        </el-menu-item>
        <el-menu-item index="/history">
          <el-icon><Clock /></el-icon>
          <span>IP 历史</span>
        </el-menu-item>
        <el-menu-item index="/location">
          <el-icon><LocationInformation /></el-icon>
          <span>位置动态</span>
        </el-menu-item>
        <el-menu-item index="/guide">
          <el-icon><Document /></el-icon>
          <span>使用说明</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <div class="current-user">
          <el-icon><UserFilled /></el-icon>
          <span>{{ currentUser || '未知用户' }}</span>
        </div>
        <div class="footer-btn" v-if="!isSsoLogin" @click="showChangePassword = true">
          <el-icon><Key /></el-icon>
          <span>修改密码</span>
        </div>
        <div class="footer-btn logout-btn" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          <span>退出登录</span>
        </div>
        <div class="footer-version" v-if="appVersion">v{{ appVersion }}</div>
      </div>
    </el-aside>
    <el-container>
      <el-main :class="showSidebar ? 'main-content' : 'main-fullscreen'">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="showChangePassword" title="修改密码" width="400px" :close-on-click-modal="false">
      <el-form :model="pwdForm" label-width="80px">
        <el-form-item label="原密码">
          <el-input v-model="pwdForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="至少 8 位，需包含字母和数字" />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="pwdForm.confirm" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showChangePassword = false">取消</el-button>
        <el-button type="primary" :loading="pwdLoading" @click="handleChangePassword">确认修改</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { changePassword } from './api'

const route = useRoute()
const router = useRouter()
const currentPath = computed(() => route.path)
// 所有 meta.public 的页面（/login、/admin-login、/sso）都是全屏认证页，不显示后台侧边栏
const showSidebar = computed(() => !route.meta.public)

const appVersion = ref('')
const appSSOLogoutUrl = ref('')

// 从 JWT 解出当前登录用户名（sub = 管理员账号或 SSO 域账号）
// localStorage 非响应式，依赖路由变化触发重算（登录/回跳后立即刷新）
const tokenInfo = computed(() => {
  void route.fullPath
  try {
    const token = localStorage.getItem('token') || ''
    const payload = token.split('.')[1]
    if (!payload) return { sub: '', login: '' }
    const b64 = payload.replace(/-/g, '+').replace(/_/g, '/')
    const decoded = JSON.parse(atob(b64 + '='.repeat((4 - b64.length % 4) % 4)))
    return { sub: decoded.sub || '', login: decoded.login || '' }
  } catch {
    return { sub: '', login: '' }
  }
})
const currentUser = computed(() => tokenInfo.value.sub)
// SSO 登录的账号没有本地密码，不提供修改密码入口
const isSsoLogin = computed(() => {
  if (tokenInfo.value.login) return tokenInfo.value.login === 'sso'
  // 旧令牌无 login 字段时按是否持有门户令牌推断
  return !!localStorage.getItem('sso_id_token')
})

onMounted(async () => {
  try {
    const [verRes, cfgRes] = await Promise.all([fetch('/api/version'), fetch('/api/auth/config')])
    appVersion.value = (await verRes.json()).version || ''
    appSSOLogoutUrl.value = (await cfgRes.json()).logout_url || ''
  } catch {}
})

function passwordOk(p) {
  return p.length >= 8 && /[A-Za-z]/.test(p) && /\d/.test(p)
}

function handleLogout() {
  const idToken = localStorage.getItem('sso_id_token') || ''
  localStorage.removeItem('token')
  localStorage.removeItem('sso_id_token')
  if (appSSOLogoutUrl.value && idToken) {
    // SSO 登录的会话：带 id_token_hint 跳门户全局登出。
    // 不带 post_logout_redirect_uri——门户通常要求该地址预先登记（未登记会 400），
    // 让门户显示自己的登出确认页即可，会话清除后用户再访问本系统会要求重新登录
    const params = new URLSearchParams()
    params.set('id_token_hint', idToken)
    window.location.href = appSSOLogoutUrl.value + (appSSOLogoutUrl.value.includes('?') ? '&' : '?') + params.toString()
  } else {
    // 账号密码登录（无门户令牌）：仅清除本系统会话，回登录停留页
    router.push('/login?stay=1')
  }
}

const showChangePassword = ref(false)
const pwdLoading = ref(false)
const pwdForm = ref({ old_password: '', new_password: '', confirm: '' })

async function handleChangePassword() {
  if (!pwdForm.value.old_password || !pwdForm.value.new_password) {
    ElMessage.warning('请填写完整')
    return
  }
  if (pwdForm.value.new_password !== pwdForm.value.confirm) {
    ElMessage.warning('两次密码不一致')
    return
  }
  if (!passwordOk(pwdForm.value.new_password)) {
    ElMessage.warning('新密码至少 8 位，且需同时包含字母和数字')
    return
  }
  pwdLoading.value = true
  try {
    await changePassword({ old_password: pwdForm.value.old_password, new_password: pwdForm.value.new_password })
    ElMessage.success('密码修改成功，请重新登录')
    localStorage.removeItem('token')
    showChangePassword.value = false
    pwdForm.value = { old_password: '', new_password: '', confirm: '' }
    router.push('/login')
  } catch {
  } finally {
    pwdLoading.value = false
  }
}
</script>

<style>
/* ==================== 浅色清爽主题 ==================== */
:root {
  --bg-base: #f4f6fb;
  --bg-card: #ffffff;
  --bg-sidebar: #1e293b;
  --text-primary: #1e293b;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
  --border-color: #e2e8f0;
  --accent: #2563eb;
  --accent-light: rgba(37, 99, 235, 0.08);
  --success: #16a34a;
  --danger: #dc2626;
  --warning: #d97706;
}

body {
  margin: 0;
  background: var(--bg-base);
  color: var(--text-primary);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
}

::selection { background: rgba(37, 99, 235, 0.16); }
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-thumb { background: #c3cede; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #a9bbd1; }
::-webkit-scrollbar-track { background: transparent; }

/* 页面切换动画 */
.page-enter-active, .page-leave-active { transition: opacity 0.18s ease, transform 0.18s ease; }
.page-enter-from { opacity: 0; transform: translateY(8px); }
.page-leave-to { opacity: 0; transform: translateY(-4px); }

/* 统一页头 */
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 700; }
.page-sub { margin: 6px 0 0; font-size: 12.5px; color: var(--text-muted); }

.app-container { background: var(--bg-base); }
.main-content { background: linear-gradient(180deg, #f6f8fc 0%, #f2f5fa 100%); padding: 24px; min-height: 100vh; }
.main-fullscreen { padding: 0; }

/* ==================== 侧边栏 ==================== */
.sidebar {
  background: linear-gradient(180deg, #1e293b 0%, #141d2b 100%);
  border-right: none;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 2px 0 8px rgba(0,0,0,0.08);
  position: sticky;
  top: 0;
  height: 100vh;
  align-self: flex-start;
}

/* Logo */
.sidebar-logo {
  height: 68px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  padding: 0 20px;
  gap: 6px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.logo-img { height: 22px; width: auto; }
.logo-text { display: flex; flex-direction: column; }
.logo-sub { font-size: 11px; color: rgba(255,255,255,0.45); letter-spacing: 1px; }

/* 菜单 */
.sidebar-menu {
  border-right: none !important;
  background: transparent !important;
  padding: 8px 0;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}
.sidebar-menu .el-menu-item {
  color: rgba(255,255,255,0.6) !important;
  height: 44px;
  line-height: 44px;
  margin: 2px 10px;
  border-radius: 8px;
  transition: all 0.2s;
  position: relative;
  font-size: 14px;
}
.sidebar-menu .el-menu-item:hover {
  color: rgba(255,255,255,0.9) !important;
  background: rgba(255,255,255,0.06) !important;
}
.sidebar-menu .el-menu-item.is-active {
  color: #fff !important;
  background: rgba(37, 99, 235, 0.3) !important;
}
.sidebar-menu .el-menu-item.is-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: var(--accent);
  border-radius: 0 3px 3px 0;
}

/* 底部按钮 */
.sidebar-footer {
  margin-top: auto;
  padding: 10px;
  border-top: 1px solid rgba(255,255,255,0.06);
}
.footer-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  color: rgba(255,255,255,0.4);
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
  font-size: 13px;
}
.footer-btn:hover { color: rgba(255,255,255,0.7); background: rgba(255,255,255,0.06); }
.logout-btn:hover { color: var(--danger); background: rgba(220,38,38,0.1); }
.current-user {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  margin-bottom: 6px;
  border-radius: 6px;
  background: rgba(255,255,255,0.06);
  color: rgba(255,255,255,0.85);
  font-size: 13px;
  font-weight: 600;
  overflow: hidden;
}
.current-user span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.footer-version {
  margin-top: 4px;
  padding: 0 14px;
  font-size: 10px;
  color: rgba(255,255,255,0.25);
  font-family: 'Courier New', monospace;
  letter-spacing: 1px;
}

/* 窄屏适配 */
@media (max-width: 768px) {
  .page-header { flex-wrap: wrap; gap: 8px; }
  .el-dialog { width: 92vw !important; }
  .main-content { padding: 12px; }
}

/* ==================== 全局 Element Plus 覆盖 ==================== */
.el-card {
  border-radius: 12px !important;
  border: 1px solid var(--border-color) !important;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
  transition: box-shadow 0.2s ease;
}
.el-card:hover {
  box-shadow: 0 4px 16px rgba(15, 40, 90, 0.07) !important;
}
.el-table {
  --el-table-border-color: #eef2f7;
  --el-table-header-bg-color: #f8fafc;
}
.el-table th.el-table__cell {
  background: #f8fafc !important;
  color: #475569;
  font-weight: 600;
}
.el-dialog { border-radius: 12px; }
.el-tag { border-radius: 6px; }

.el-button--primary:not(.is-link) {
  background: var(--accent) !important;
  border: none !important;
}
.el-button--primary:not(.is-link):hover {
  background: #1d4ed8 !important;
  box-shadow: 0 2px 8px rgba(37,99,235,0.3) !important;
}
.el-button--primary.is-link { color: var(--accent) !important; }
.el-button--primary.is-link:hover { color: #1d4ed8 !important; }
.el-button--danger.is-link { color: var(--danger) !important; }
.el-button--danger.is-link:hover { color: #b91c1c !important; }

h2 { color: var(--text-primary) !important; }
code { background: #eef2ff; color: var(--accent); padding: 2px 6px; border-radius: 4px; font-size: 13px; }
</style>
