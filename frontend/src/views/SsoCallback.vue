<template>
  <div class="sso-waiting">
    <div class="sso-card">
      <el-icon class="is-loading" :size="28" color="#0b6ef5"><Loading /></el-icon>
      <p>{{ error ? 'SSO 登录失败' : '正在完成登录…' }}</p>
      <p class="sso-error" v-if="error">{{ error }}</p>
      <el-button v-if="error" type="primary" link @click="router.replace('/login')">返回重新登录</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const error = ref('')

onMounted(() => {
  const token = route.query.token
  const err = route.query.error
  if (err) {
    error.value = String(err)
    return
  }
  if (token) {
    localStorage.setItem('token', String(token))
    ElMessage.success('登录成功')
    const redirect = String(route.query.redirect || '/')
    // 只允许站内路径
    router.replace(redirect.startsWith('/') && !redirect.startsWith('//') ? redirect : '/')
  } else {
    router.replace('/login')
  }
})
</script>

<style scoped>
.sso-waiting {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, #f4f9ff 0%, #e8f2fd 45%, #dceafb 100%);
}
.sso-card {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #cfe0f4;
  border-radius: 16px;
  padding: 40px 56px;
  text-align: center;
  box-shadow: 0 20px 50px rgba(30, 90, 180, 0.12);
}
.sso-card p { margin: 14px 0 0; color: #10314f; font-size: 15px; }
.sso-error { color: #dc2626; font-size: 13px !important; word-break: break-all; }
</style>
