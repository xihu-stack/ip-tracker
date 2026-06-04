<template>
  <el-container class="app-container">
    <el-aside v-if="showSidebar" width="220px" class="sidebar">
      <div class="sidebar-logo">
        <div class="logo-ring">
          <svg viewBox="0 0 32 32" fill="none">
            <circle cx="16" cy="16" r="6" stroke="#2563eb" stroke-width="1.5" opacity="0.9"/>
            <circle cx="16" cy="16" r="11" stroke="#2563eb" stroke-width="0.8" opacity="0.35"/>
            <circle cx="16" cy="16" r="14" stroke="#2563eb" stroke-width="0.4" opacity="0.15"/>
            <circle cx="16" cy="10" r="1.5" fill="#2563eb"/>
          </svg>
        </div>
        <div class="logo-text">
          <span class="logo-title">IP TRACKER</span>
          <span class="logo-sub">定位追踪平台</span>
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
        <el-menu-item index="/guide">
          <el-icon><Document /></el-icon>
          <span>使用说明</span>
        </el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <div class="footer-btn" @click="showChangePassword = true">
          <el-icon><Key /></el-icon>
          <span>修改密码</span>
        </div>
        <div class="footer-btn logout-btn" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          <span>退出登录</span>
        </div>
      </div>
    </el-aside>
    <el-container>
      <el-main :class="showSidebar ? 'main-content' : 'main-fullscreen'">
        <router-view />
      </el-main>
    </el-container>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="showChangePassword" title="修改密码" width="400px" :close-on-click-modal="false">
      <el-form :model="pwdForm" label-width="80px">
        <el-form-item label="原密码">
          <el-input v-model="pwdForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.new_password" type="password" show-password />
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
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { changePassword } from './api'

const route = useRoute()
const router = useRouter()
const currentPath = computed(() => route.path)
const showSidebar = computed(() => route.path !== '/login')

function handleLogout() {
  localStorage.removeItem('token')
  router.push('/login')
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
  if (pwdForm.value.new_password.length < 6) {
    ElMessage.warning('新密码至少 6 位')
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

body { margin: 0; background: var(--bg-base); color: var(--text-primary); }

.app-container { background: var(--bg-base); }
.main-content { background: var(--bg-base); padding: 24px; min-height: 100vh; }
.main-fullscreen { padding: 0; }

/* ==================== 侧边栏 ==================== */
.sidebar {
  background: var(--bg-sidebar);
  border-right: none;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 2px 0 8px rgba(0,0,0,0.08);
}

/* Logo */
.sidebar-logo {
  height: 68px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 12px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.logo-ring { width: 34px; height: 34px; flex-shrink: 0; }
.logo-text { display: flex; flex-direction: column; }
.logo-title { color: #fff; font-size: 15px; font-weight: 700; letter-spacing: 3px; line-height: 1.2; }
.logo-sub { font-size: 10px; color: rgba(255,255,255,0.4); letter-spacing: 1px; }

/* 菜单 */
.sidebar-menu {
  border-right: none !important;
  background: transparent !important;
  padding: 8px 0;
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

/* ==================== 全局 Element Plus 覆盖 ==================== */
.el-card {
  border-radius: 10px !important;
  border: 1px solid var(--border-color) !important;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}

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
