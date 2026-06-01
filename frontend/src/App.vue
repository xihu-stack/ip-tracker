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
/* 全局主题 */
.app-container { background: #f0f2f5; }
.main-content { background: #f0f2f5; padding: 24px; min-height: 100vh; }
.main-fullscreen { padding: 0; }

/* 侧边栏 */
.sidebar {
  background: #304156;
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
  border-bottom: 1px solid #3a4a5e;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 4px;
}
.logo-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #409EFF;
  box-shadow: 0 0 8px #409EFF;
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 8px #409EFF; }
  50% { opacity: 0.5; box-shadow: 0 0 4px #409EFF; }
}

/* 菜单 */
.sidebar-menu {
  border-right: none !important;
  background: transparent !important;
  padding: 12px 0;
}
.sidebar-menu .el-menu-item {
  color: #bfcbd9 !important;
  height: 48px;
  line-height: 48px;
  margin: 2px 12px;
  border-radius: 8px;
  transition: all 0.3s;
  position: relative;
}
.sidebar-menu .el-menu-item:hover {
  color: #fff !important;
  background: rgba(255, 255, 255, 0.05) !important;
}
.sidebar-menu .el-menu-item.is-active {
  color: #409EFF !important;
  background: rgba(64, 158, 255, 0.1) !important;
}
.sidebar-menu .el-menu-item.is-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: #409EFF;
  border-radius: 0 3px 3px 0;
  box-shadow: 0 0 8px rgba(64,158,255,0.5);
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
  color: #8aa0b8;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.3s;
  font-size: 13px;
}
.footer-btn:hover {
  color: #bfcbd9;
  background: rgba(255, 255, 255, 0.05);
}
.logout-btn:hover {
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.05);
}

/* 全局 Element Plus 覆盖 - 浅色科技风 */
.el-card { border-radius: 12px !important; }
.el-button--primary { background: linear-gradient(135deg, #1a6dcc, #409EFF) !important; border: none !important; }
.el-button--primary:hover { box-shadow: 0 2px 12px rgba(64,158,255,0.4) !important; }
</style>
