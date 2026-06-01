<template>
  <div class="login-wrapper">
    <!-- 动态背景网格 -->
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
            <circle cx="20" cy="20" r="8" stroke="#00d4ff" stroke-width="2" opacity="0.8"/>
            <circle cx="20" cy="20" r="14" stroke="#00d4ff" stroke-width="1" opacity="0.4"/>
            <circle cx="20" cy="20" r="18" stroke="#00d4ff" stroke-width="0.5" opacity="0.2"/>
            <circle cx="20" cy="12" r="2" fill="#00d4ff"/>
            <circle cx="28" cy="24" r="2" fill="#00d4ff" opacity="0.6"/>
            <circle cx="12" cy="24" r="2" fill="#00d4ff" opacity="0.4"/>
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
  background: #0a0e1a;
  position: relative;
  overflow: hidden;
}

/* 动态网格背景 */
.grid-bg {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px);
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
  background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.15), transparent);
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
  background: #00d4ff;
  border-radius: 50%;
  opacity: 0;
  animation: float-up linear infinite;
}
@keyframes float-up {
  0% { opacity: 0; transform: translateY(0) scale(1); }
  20% { opacity: 0.6; }
  80% { opacity: 0.3; }
  100% { opacity: 0; transform: translateY(-200px) scale(0.5); }
}

/* 登录卡片 */
.login-card {
  width: 420px;
  position: relative;
  background: rgba(12, 20, 40, 0.85);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 16px;
  padding: 48px 40px 36px;
  backdrop-filter: blur(20px);
  z-index: 1;
}

/* 卡片外发光 */
.card-glow {
  position: absolute;
  inset: -1px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), transparent 40%, transparent 60%, rgba(0, 212, 255, 0.05));
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
  color: #e0f0ff;
  letter-spacing: 4px;
}
.login-header p {
  margin: 8px 0 0;
  font-size: 11px;
  color: rgba(0, 212, 255, 0.5);
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
  color: rgba(0, 212, 255, 0.5);
  font-size: 16px;
  z-index: 1;
}
.login-form :deep(.el-input__wrapper) {
  background: rgba(0, 212, 255, 0.04);
  border: 1px solid rgba(0, 212, 255, 0.12);
  border-radius: 8px;
  box-shadow: none;
  padding-left: 44px;
  transition: all 0.3s;
}
.login-form :deep(.el-input__wrapper:hover) {
  border-color: rgba(0, 212, 255, 0.3);
}
.login-form :deep(.el-input__wrapper.is-focus) {
  border-color: #00d4ff;
  box-shadow: 0 0 12px rgba(0, 212, 255, 0.15);
}
.login-form :deep(.el-input__inner) {
  color: #c0d8f0;
}
.login-form :deep(.el-input__inner::placeholder) {
  color: rgba(0, 212, 255, 0.25);
}

/* 登录按钮 */
.login-btn {
  width: 100%;
  height: 48px;
  margin-top: 8px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #0066cc, #00aaff);
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 8px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
}
.login-btn:hover {
  background: linear-gradient(135deg, #0088ee, #00ccff);
  box-shadow: 0 0 24px rgba(0, 170, 255, 0.35);
  transform: translateY(-1px);
}
.login-btn::after {
  content: '';
  position: absolute;
  top: -50%;
  left: -60%;
  width: 40%;
  height: 200%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
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
  color: rgba(0, 212, 255, 0.2);
  letter-spacing: 2px;
  font-family: 'Courier New', monospace;
}
</style>
