<template>
  <el-container style="min-height: 100vh">
    <el-aside v-if="showSidebar" width="220px" style="background: #304156; display: flex; flex-direction: column">
      <div style="height: 60px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 18px; font-weight: bold; border-bottom: 1px solid #3a4a5e">
        IP 定位追踪
      </div>
      <el-menu :default-active="currentPath" router background-color="#304156" text-color="#bfcbd9" active-text-color="#409EFF">
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
          <span>使用 说明</span>
        </el-menu-item>
      </el-menu>
      <div style="margin-top: auto; padding: 16px; border-top: 1px solid #3a4a5e">
        <el-button text style="color: #bfcbd9; width: 100%" @click="showChangePassword = true">
          <el-icon><Key /></el-icon>
          <span style="margin-left: 6px">修改密码</span>
        </el-button>
      </div>
    </el-aside>
    <el-container>
      <el-main :style="showSidebar ? 'background: #f0f2f5; padding: 20px' : 'padding: 0'">
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
    // 错误已由 axios 拦截器处理
  } finally {
    pwdLoading.value = false
  }
}
</script>
