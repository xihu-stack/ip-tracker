<template>
  <el-container class="app-container">
    <el-aside v-if="showSidebar" width="220px" class="sidebar">
      <div class="sidebar-logo">
        <div class="logo-dot"></div>
        <span>IP TRACKER</span>
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
/* 全局暗色主题 */
.app-container { background: #0d1117; }
.main-content { background: #0d1117; padding: 24px; min-height: 100vh; }
.main-fullscreen { padding: 0; }

/* 侧边栏 */
.sidebar {
  background: linear-gradient(180deg, #0b1120 0%, #0d1628 100%);
  border-right: 1px solid rgba(0, 212, 255, 0.08);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}
.sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 1px;
  height: 100%;
  background: linear-gradient(180deg, rgba(0,212,255,0.3), transparent 30%, transparent 70%, rgba(0,212,255,0.1));
}

/* Logo 区域 */
.sidebar-logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.08);
  color: #e0f0ff;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 4px;
  font-family: 'Courier New', monospace;
}
.logo-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #00d4ff;
  box-shadow: 0 0 8px #00d4ff, 0 0 20px rgba(0,212,255,0.3);
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 8px #00d4ff, 0 0 20px rgba(0,212,255,0.3); }
  50% { opacity: 0.6; box-shadow: 0 0 4px #00d4ff, 0 0 10px rgba(0,212,255,0.15); }
}

/* 菜单 */
.sidebar-menu {
  border-right: none !important;
  background: transparent !important;
  padding: 12px 0;
}
.sidebar-menu .el-menu-item {
  color: rgba(160, 190, 220, 0.6) !important;
  height: 48px;
  line-height: 48px;
  margin: 2px 12px;
  border-radius: 8px;
  transition: all 0.3s;
  position: relative;
}
.sidebar-menu .el-menu-item:hover {
  color: #a0c8e8 !important;
  background: rgba(0, 212, 255, 0.05) !important;
}
.sidebar-menu .el-menu-item.is-active {
  color: #00d4ff !important;
  background: rgba(0, 212, 255, 0.08) !important;
}
.sidebar-menu .el-menu-item.is-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: #00d4ff;
  border-radius: 0 3px 3px 0;
  box-shadow: 0 0 8px rgba(0,212,255,0.5);
}

/* 底部按钮 */
.sidebar-footer {
  margin-top: auto;
  padding: 12px 16px;
  border-top: 1px solid rgba(0, 212, 255, 0.08);
}
.footer-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  color: rgba(160, 190, 220, 0.5);
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.3s;
  font-size: 13px;
}
.footer-btn:hover {
  color: #a0c8e8;
  background: rgba(0, 212, 255, 0.05);
}
.logout-btn:hover {
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.05);
}

/* 全局 Element Plus 暗色覆盖 */
.el-card { background: #111827 !important; border: 1px solid rgba(0, 212, 255, 0.08) !important; color: #c0d8f0 !important; border-radius: 12px !important; }
.el-card__header { border-bottom: 1px solid rgba(0, 212, 255, 0.08) !important; color: #e0f0ff !important; }
.el-table { background: transparent !important; color: #a0b8d0 !important; }
.el-table tr { background: transparent !important; }
.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell { background: rgba(0,212,255,0.02) !important; }
.el-table th.el-table__cell { background: rgba(0,212,255,0.04) !important; color: #7aa0c0 !important; border-bottom: 1px solid rgba(0,212,255,0.08) !important; }
.el-table td.el-table__cell { border-bottom: 1px solid rgba(0,212,255,0.05) !important; }
.el-table__empty-text { color: rgba(0,212,255,0.2) !important; }
.el-pagination { --el-pagination-bg-color: transparent; --el-pagination-text-color: #7aa0c0; --el-pagination-button-bg-color: rgba(0,212,255,0.06); }
.el-dialog { background: #111827 !important; border: 1px solid rgba(0,212,255,0.1) !important; }
.el-dialog__title { color: #e0f0ff !important; }
.el-dialog__headerbtn .el-dialog__close { color: #7aa0c0 !important; }
.el-form-item__label { color: #7aa0c0 !important; }
.el-input__wrapper { background: rgba(0,212,255,0.04) !important; border: 1px solid rgba(0,212,255,0.1) !important; box-shadow: none !important; }
.el-input__inner { color: #c0d8f0 !important; }
.el-button--primary { background: linear-gradient(135deg, #0066cc, #00aaff) !important; border: none !important; }
.el-button--primary:hover { background: linear-gradient(135deg, #0088ee, #00ccff) !important; box-shadow: 0 0 16px rgba(0,170,255,0.3) !important; }
.el-tag--dark.el-tag--success { background: rgba(103,194,58,0.15) !important; border-color: rgba(103,194,58,0.3) !important; color: #67C23A !important; }
.el-tag--dark.el-tag--danger { background: rgba(245,108,108,0.15) !important; border-color: rgba(245,108,108,0.3) !important; color: #F56C6C !important; }
.el-tag.el-tag--success { background: rgba(103,194,58,0.1) !important; border-color: rgba(103,194,58,0.2) !important; color: #67C23A !important; }
.el-tag.el-tag--info { background: rgba(144,164,183,0.1) !important; border-color: rgba(144,164,183,0.2) !important; color: #90a3b7 !important; }
.el-tag.el-tag--warning { background: rgba(230,162,60,0.1) !important; border-color: rgba(230,162,60,0.2) !important; color: #E6A23C !important; }
.el-tag.el-tag--danger { background: rgba(245,108,108,0.1) !important; border-color: rgba(245,108,108,0.2) !important; color: #F56C6C !important; }
.el-loading-mask { background: rgba(13,17,23,0.7) !important; }
.el-overlay { background-color: rgba(0,0,0,0.6) !important; }
h2 { color: #e0f0ff !important; }
.el-alert { background: rgba(0,212,255,0.04) !important; border: 1px solid rgba(0,212,255,0.1) !important; }
.el-alert__title { color: #a0c8e8 !important; }
.el-step__title { color: #a0c8e8 !important; }
.el-step__description { color: #7aa0c0 !important; }
.el-step__head.is-finish { color: #00d4ff !important; border-color: #00d4ff !important; }
.el-step__head.is-success { color: #67C23A !important; border-color: #67C23A !important; }
.el-timeline-item__wrapper { color: #a0b8d0 !important; }
.el-timeline-item__tail { border-left-color: rgba(0,212,255,0.15) !important; }
code { background: rgba(0,212,255,0.08) !important; color: #00d4ff !important; padding: 2px 6px; border-radius: 3px; }
p, span { color: #a0b8d0; }
.el-select .el-input__wrapper { background: rgba(0,212,255,0.04) !important; }
input[type="date"] { background: rgba(0,212,255,0.04) !important; border: 1px solid rgba(0,212,255,0.1) !important; color: #c0d8f0 !important; color-scheme: dark; }
</style>
