<template>
  <div class="login-wrapper">
    <!-- 浅色蓝图网格背景 -->
    <div class="grid-bg"></div>
    <div class="scan-line"></div>

    <!-- 浮动粒子 -->
    <div class="particles">
      <span v-for="i in 20" :key="i" class="dot" :style="dotStyle(i)"></span>
    </div>

    <!-- 登录卡片 -->
    <div class="login-card">
      <div class="card-glow"></div>
      <div class="login-header">
        <div class="logo-icon">
          <svg viewBox="0 0 40 40" fill="none">
            <circle cx="20" cy="20" r="8" stroke="#0b6ef5" stroke-width="2" opacity="0.9"/>
            <circle cx="20" cy="20" r="14" stroke="#0b6ef5" stroke-width="1" opacity="0.5"/>
            <circle cx="20" cy="20" r="18" stroke="#0b6ef5" stroke-width="0.5" opacity="0.3"/>
            <circle cx="20" cy="12" r="2" fill="#0b6ef5"/>
            <circle cx="28" cy="24" r="2" fill="#0b6ef5" opacity="0.7"/>
            <circle cx="12" cy="24" r="2" fill="#0b6ef5" opacity="0.5"/>
          </svg>
        </div>
        <h2>IP 定位追踪平台</h2>
        <p>INTELLIGENT LOCATION TRACKING SYSTEM</p>
      </div>
      <el-form :model="form" @submit.prevent="handleLogin" class="login-form">
        <div class="input-group">
          <div class="input-icon"><el-icon><User /></el-icon></div>
          <el-input v-model="form.username" placeholder="请输入用户名" size="large" />
        </div>
        <div class="input-group">
          <div class="input-icon"><el-icon><Lock /></el-icon></div>
          <el-input v-model="form.password" type="password" placeholder="请输入密码" size="large" show-password @keyup.enter="handleLogin" />
        </div>
        <el-button size="large" class="login-btn" :loading="loading" @click="handleLogin">
          <span v-if="!loading">登 录</span>
        </el-button>
      </el-form>
      <div class="login-footer">SECURE ACCESS · ENCRYPTED CONNECTION</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '../api'

const router = useRouter()
const loading = ref(false)
const form = ref({ username: '', password: '' })

function dotStyle(i) {
  const size = 2 + Math.random() * 3
  return {
    width: size + 'px',
    height: size + 'px',
    left: Math.random() * 100 + '%',
    top: Math.random() * 100 + '%',
    animationDelay: (Math.random() * 6) + 's',
    animationDuration: (4 + Math.random() * 6) + 's'
  }
}

async function handleLogin() {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const res = await login(form.value)
    localStorage.setItem('token', res.data.access_token)
    ElMessage.success('登录成功')
    router.push('/')
  } catch {
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, #f4f9ff 0%, #e8f2fd 45%, #dceafb 100%);
  position: relative;
  overflow: hidden;
}

/* 蓝图网格背景 */
.grid-bg {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(11, 110, 245, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(11, 110, 245, 0.07) 1px, transparent 1px);
  background-size: 60px 60px;
  animation: gridMove 20s linear infinite;
}
@keyframes gridMove {
  0% { transform: translate(0, 0); }
  100% { transform: translate(60px, 60px); }
}

/* 扫描线 */
.scan-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(11, 110, 245, 0.25), transparent);
  animation: scanDown 4s ease-in-out infinite;
}
@keyframes scanDown {
  0% { top: -2px; opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { top: 100%; opacity: 0; }
}

/* 浮动粒子 */
.particles .dot {
  position: absolute;
  background: #4aa3ff;
  border-radius: 50%;
  opacity: 0;
  animation: float-up linear infinite;
}
@keyframes float-up {
  0% { opacity: 0; transform: translateY(0) scale(1); }
  20% { opacity: 0.5; }
  80% { opacity: 0.25; }
  100% { opacity: 0; transform: translateY(-200px) scale(0.5); }
}

/* 登录卡片 */
.login-card {
  width: 420px;
  position: relative;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #cfe0f4;
  border-radius: 16px;
  padding: 48px 40px 36px;
  backdrop-filter: blur(20px);
  box-shadow:
    0 20px 50px rgba(30, 90, 180, 0.12),
    0 4px 12px rgba(30, 90, 180, 0.06);
  z-index: 1;
}

/* 卡片柔光 */
.card-glow {
  position: absolute;
  inset: -1px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(11, 110, 245, 0.12), transparent 40%, transparent 60%, rgba(74, 163, 255, 0.08));
  z-index: -1;
  animation: glowPulse 3s ease-in-out infinite alternate;
}
@keyframes glowPulse {
  0% { opacity: 0.5; }
  100% { opacity: 1; }
}

/* 头部 */
.login-header {
  text-align: center;
  margin-bottom: 36px;
}
.logo-icon {
  width: 56px;
  height: 56px;
  margin: 0 auto 16px;
  animation: logoSpin 10s linear infinite;
}
@keyframes logoSpin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.login-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #10314f;
  letter-spacing: 4px;
}
.login-header p {
  margin: 8px 0 0;
  font-size: 11px;
  color: #628cb8;
  letter-spacing: 3px;
  font-family: 'Courier New', monospace;
}

/* 输入框组 */
.input-group {
  position: relative;
  margin-bottom: 20px;
}
.input-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: #3f7ec9;
  font-size: 16px;
  z-index: 1;
}
.login-form :deep(.el-input__wrapper) {
  background: #ffffff;
  border: 1px solid #c4d7ee;
  border-radius: 8px;
  box-shadow: none;
  padding-left: 44px;
  transition: all 0.3s;
}
.login-form :deep(.el-input__wrapper:hover) {
  border-color: #8fb8e8;
}
.login-form :deep(.el-input__wrapper.is-focus) {
  border-color: #0b6ef5;
  box-shadow: 0 0 0 3px rgba(11, 110, 245, 0.12);
}
.login-form :deep(.el-input__inner) {
  color: #1a3a5c;
}
.login-form :deep(.el-input__inner::placeholder) {
  color: #94aac4;
}

/* 登录按钮 */
.login-btn {
  width: 100%;
  height: 48px;
  margin-top: 8px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #0b6ef5, #2b9cff);
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 8px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
}
.login-btn:hover {
  background: linear-gradient(135deg, #0a63dc, #1b8af0);
  box-shadow: 0 8px 20px rgba(11, 110, 245, 0.3);
  transform: translateY(-1px);
}
.login-btn::after {
  content: '';
  position: absolute;
  top: -50%;
  left: -60%;
  width: 40%;
  height: 200%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent);
  transform: skewX(-25deg);
  animation: btnShine 3s ease-in-out infinite;
}
@keyframes btnShine {
  0% { left: -60%; }
  40%, 100% { left: 140%; }
}

/* 底部 */
.login-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 10px;
  color: #8fa9c6;
  letter-spacing: 2px;
  font-family: 'Courier New', monospace;
}
</style>
