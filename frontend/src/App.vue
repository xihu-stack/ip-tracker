<template>
  <el-container class="app-container">
    <el-aside v-if="showSidebar" width="220px" class="sidebar">
      <div class="sidebar-logo">
        <div class="logo-ring">
          <svg viewBox="0 0 32 32" fill="none">
            <circle cx="16" cy="16" r="6" stroke="#00e5ff" stroke-width="1.5" opacity="0.9"/>
            <circle cx="16" cy="16" r="11" stroke="#00e5ff" stroke-width="0.8" opacity="0.4"/>
            <circle cx="16" cy="16" r="14" stroke="#00e5ff" stroke-width="0.4" opacity="0.15"/>
            <circle cx="16" cy="10" r="1.5" fill="#00e5ff"/>
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
    <el-dialog v-model="showChangePassword" title="修改密码" width="400px" :close-on-click-modal="false" class="dark-dialog">
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
/* ==================== 深色主题基础 ==================== */
:root {
  --bg-base: #0b1120;
  --bg-card: #111827;
  --bg-card-hover: #162032;
  --bg-input: #0d1525;
  --border-color: #1e2d45;
  --border-glow: rgba(0, 229, 255, 0.12);
  --text-primary: #e2e8f0;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --accent: #00e5ff;
  --accent-dim: rgba(0, 229, 255, 0.1);
  --success: #22c55e;
  --danger: #ef4444;
  --warning: #f59e0b;
}

* { box-sizing: border-box; }
body { margin: 0; background: var(--bg-base); color: var(--text-primary); font-family: -apple-system, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif; }

.app-container { background: var(--bg-base); }
.main-content { background: var(--bg-base); padding: 24px; min-height: 100vh; }
.main-fullscreen { padding: 0; }

/* ==================== 侧边栏 ==================== */
.sidebar {
  background: linear-gradient(180deg, #0d1525 0%, #0b1120 100%);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}
.sidebar::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 1px;
  height: 100%;
  background: linear-gradient(180deg, rgba(0,229,255,0.2), transparent 25%, transparent 75%, rgba(0,229,255,0.08));
  pointer-events: none;
}

/* Logo */
.sidebar-logo {
  height: 72px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 12px;
  border-bottom: 1px solid var(--border-color);
  position: relative;
}
.logo-ring {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  animation: slowSpin 12s linear infinite;
}
@keyframes slowSpin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.logo-text { display: flex; flex-direction: column; }
.logo-title {
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 3px;
  line-height: 1.2;
}
.logo-sub {
  font-size: 10px;
  color: var(--text-muted);
  letter-spacing: 1px;
}

/* 菜单 */
.sidebar-menu {
  border-right: none !important;
  background: transparent !important;
  padding: 12px 0;
}
.sidebar-menu .el-menu-item {
  color: var(--text-secondary) !important;
  height: 44px;
  line-height: 44px;
  margin: 2px 10px;
  border-radius: 8px;
  transition: all 0.25s;
  position: relative;
  font-size: 14px;
}
.sidebar-menu .el-menu-item:hover {
  color: var(--text-primary) !important;
  background: var(--accent-dim) !important;
}
.sidebar-menu .el-menu-item.is-active {
  color: var(--accent) !important;
  background: var(--accent-dim) !important;
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
  box-shadow: 0 0 8px rgba(0,229,255,0.5);
}

/* 底部按钮 */
.sidebar-footer {
  margin-top: auto;
  padding: 12px 10px;
  border-top: 1px solid var(--border-color);
}
.footer-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.25s;
  font-size: 13px;
}
.footer-btn:hover {
  color: var(--text-secondary);
  background: var(--accent-dim);
}
.logout-btn:hover {
  color: var(--danger);
  background: rgba(239, 68, 68, 0.08);
}

/* ==================== 全局 Element Plus 深色覆盖 ==================== */
/* 卡片 */
.el-card {
  background: var(--bg-card) !important;
  border: 1px solid var(--border-color) !important;
  border-radius: 12px !important;
  color: var(--text-primary) !important;
  box-shadow: 0 4px 24px rgba(0,0,0,0.2) !important;
}
.el-card__header {
  border-bottom: 1px solid var(--border-color) !important;
  color: var(--text-primary) !important;
  padding: 14px 20px !important;
}
.el-card__body { color: var(--text-primary) !important; }

/* 表格 */
.el-table {
  --el-table-bg-color: var(--bg-card) !important;
  --el-table-tr-bg-color: var(--bg-card) !important;
  --el-table-header-bg-color: #0f1729 !important;
  --el-table-row-hover-bg-color: var(--bg-card-hover) !important;
  --el-table-border-color: var(--border-color) !important;
  --el-table-text-color: var(--text-primary) !important;
  --el-table-header-text-color: var(--text-secondary) !important;
  color: var(--text-primary) !important;
}
.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell {
  background: rgba(255,255,255,0.015) !important;
}

/* 按钮 */
.el-button--primary:not(.is-link) {
  background: linear-gradient(135deg, #0891b2, #00e5ff) !important;
  border: none !important;
  color: #fff !important;
}
.el-button--primary:not(.is-link):hover {
  box-shadow: 0 2px 16px rgba(0,229,255,0.3) !important;
}
.el-button--primary.is-link {
  color: var(--accent) !important;
}
.el-button--primary.is-link:hover {
  color: #33ecff !important;
}
.el-button--danger.is-link {
  color: var(--danger) !important;
}
.el-button--danger.is-link:hover {
  color: #f87171 !important;
}
.el-button--default {
  background: var(--bg-card-hover) !important;
  border-color: var(--border-color) !important;
  color: var(--text-secondary) !important;
}
.el-button--default:hover {
  border-color: var(--accent) !important;
  color: var(--accent) !important;
}

/* 输入框 */
.el-input__wrapper {
  background: var(--bg-input) !important;
  border: 1px solid var(--border-color) !important;
  box-shadow: none !important;
  color: var(--text-primary) !important;
}
.el-input__wrapper:hover { border-color: rgba(0,229,255,0.3) !important; }
.el-input__wrapper.is-focus { border-color: var(--accent) !important; box-shadow: 0 0 8px rgba(0,229,255,0.1) !important; }
.el-input__inner { color: var(--text-primary) !important; }
.el-input__inner::placeholder { color: var(--text-muted) !important; }
.el-input.is-disabled .el-input__wrapper { background: rgba(255,255,255,0.03) !important; }

/* Select 下拉 */
.el-select .el-input__wrapper { background: var(--bg-input) !important; }
.el-select-dropdown { background: var(--bg-card) !important; border: 1px solid var(--border-color) !important; }
.el-select-dropdown__item { color: var(--text-primary) !important; }
.el-select-dropdown__item.hover, .el-select-dropdown__item:hover { background: var(--accent-dim) !important; }
.el-select-dropdown__item.selected { color: var(--accent) !important; }
.el-popper.is-light { background: var(--bg-card) !important; border: 1px solid var(--border-color) !important; }
.el-popper.is-light .el-popper__arrow::before { background: var(--bg-card) !important; border-color: var(--border-color) !important; }

/* 分页 */
.el-pagination {
  --el-pagination-bg-color: var(--bg-card) !important;
  --el-pagination-text-color: var(--text-secondary) !important;
  --el-pagination-button-bg-color: var(--bg-card-hover) !important;
  --el-pagination-button-color: var(--text-secondary) !important;
  --el-pagination-hover-color: var(--accent) !important;
}
.el-pager li {
  background: var(--bg-card-hover) !important;
  color: var(--text-secondary) !important;
}
.el-pager li:hover, .el-pager li.is-active { color: var(--accent) !important; }
.el-pagination__total { color: var(--text-secondary) !important; }
.el-pagination__jump { color: var(--text-secondary) !important; }

/* 对话框 */
.dark-dialog .el-dialog {
  background: var(--bg-card) !important;
  border: 1px solid var(--border-color) !important;
}
.dark-dialog .el-dialog__header { color: var(--text-primary) !important; }
.dark-dialog .el-dialog__title { color: var(--text-primary) !important; }
.dark-dialog .el-dialog__body { color: var(--text-primary) !important; }
.el-dialog { background: var(--bg-card) !important; }
.el-dialog__header { color: var(--text-primary) !important; }
.el-dialog__title { color: var(--text-primary) !important; }
.el-dialog__body { color: var(--text-primary) !important; }
.el-overlay-dialog { background: rgba(0,0,0,0.6) !important; }

/* 标签 */
.el-tag--info { background: rgba(100,116,139,0.15) !important; border-color: rgba(100,116,139,0.2) !important; color: var(--text-secondary) !important; }
.el-tag--success { background: rgba(34,197,94,0.12) !important; border-color: rgba(34,197,94,0.2) !important; color: var(--success) !important; }
.el-tag--danger { background: rgba(239,68,68,0.12) !important; border-color: rgba(239,68,68,0.2) !important; color: var(--danger) !important; }
.el-tag--warning { background: rgba(245,158,11,0.12) !important; border-color: rgba(245,158,11,0.2) !important; color: var(--warning) !important; }

/* Alert */
.el-alert--info { background: rgba(0,229,255,0.06) !important; border: 1px solid rgba(0,229,255,0.15) !important; }
.el-alert--info .el-alert__title { color: var(--accent) !important; }

/* Timeline / Steps */
.el-timeline-item__wrapper { color: var(--text-primary) !important; }
.el-timeline-item__content { color: var(--text-primary) !important; }
.el-step__title { color: var(--text-primary) !important; }
.el-step__description { color: var(--text-secondary) !important; }
.el-step.is-success .el-step__title { color: var(--success) !important; }

/* Loading */
.el-loading-mask { background: rgba(11,17,32,0.8) !important; }

/* Popconfirm */
.el-popconfirm { color: var(--text-primary) !important; }
.el-popconfirm__action .el-button--primary { background: var(--danger) !important; }

/* 表单标签 */
.el-form-item__label { color: var(--text-secondary) !important; }

/* 标题 */
h2 { color: var(--text-primary) !important; }
code { background: rgba(0,229,255,0.08) !important; color: var(--accent) !important; padding: 2px 6px; border-radius: 4px; font-size: 13px; }
</style>
