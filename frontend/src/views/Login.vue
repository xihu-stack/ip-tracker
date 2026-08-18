<template>
  <div class="login-page">
    <!-- 左侧品牌展示区 -->
    <div class="brand-panel">
      <div class="brand-grid"></div>
      <div class="radar">
        <div class="radar-ring r1"></div>
        <div class="radar-ring r2"></div>
        <div class="radar-ring r3"></div>
        <div class="radar-sweep"></div>
        <span class="radar-dot d1"></span>
        <span class="radar-dot d2"></span>
        <span class="radar-dot d3"></span>
        <span class="radar-dot d4"></span>
      </div>
      <div class="brand-content">
        <img class="brand-logo" src="/logo.png" alt="Sellixon" />
        <h1>IP 定位追踪平台</h1>
        <p class="brand-sub">INTELLIGENT LOCATION TRACKING SYSTEM</p>
        <ul class="brand-features">
          <li><span class="feat-dot"></span>终端在线状态实时监测</li>
          <li><span class="feat-dot"></span>全国城市分布可视化地图</li>
          <li><span class="feat-dot"></span>IP 变更历史轨迹追溯</li>
        </ul>
      </div>
      <div class="brand-footer">SECURE ACCESS · ENCRYPTED CONNECTION</div>
    </div>

    <!-- 右侧登录表单区 -->
    <div class="form-panel">
      <div class="grid-bg"></div>

      <!-- SSO 模式：自动跳转统一门户 -->
      <div class="login-card" v-if="ssoEnabled && !showPwdForm">
        <div class="login-header">
          <h2>统一门户登录</h2>
          <p>{{ countdown > 0 ? `${countdown} 秒后自动跳转到统一门户…` : '正在跳转到统一门户…' }}</p>
        </div>
        <el-button size="large" class="login-btn" @click="goSso">
          前往统一门户登录
        </el-button>
        <div class="login-tip">
          <a class="pwd-link" @click.prevent="usePassword">改用账号密码登录</a>
        </div>
      </div>

      <!-- 账号密码模式 -->
      <div class="login-card" v-else>
        <div class="login-header">
          <h2>欢迎登录</h2>
          <p>请输入管理员账号</p>
        </div>
        <el-form :model="form" @submit.prevent="handleLogin" class="login-form">
          <div class="input-group">
            <div class="input-icon"><el-icon><User /></el-icon></div>
            <el-input v-model="form.username" placeholder="用户名" size="large" />
          </div>
          <div class="input-group">
            <div class="input-icon"><el-icon><Lock /></el-icon></div>
            <el-input v-model="form.password" type="password" placeholder="密码" size="large" show-password @keyup.enter="handleLogin" />
          </div>
          <el-button size="large" class="login-btn" :loading="loading" @click="handleLogin">
            <span v-if="!loading">登 录</span>
          </el-button>
        </el-form>
        <div class="login-tip" v-if="ssoEnabled">
          <a class="pwd-link" @click.prevent="goSso">使用统一门户登录</a>
        </div>
        <div class="login-tip" v-else>内网管理系统 · 如需重置密码请联系服务器管理员</div>
      </div>
      <div class="form-footer">IP TRACKER · ADMIN CONSOLE</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '../api'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const form = ref({ username: '', password: '' })

// SSO：启用时自动跳统一门户，保留账号密码应急入口（/login?pwd=1 直接进密码表单）
const ssoEnabled = ref(false)
const showPwdForm = ref(false)
const countdown = ref(3)
let ssoTimer = null

function goSso() {
  if (ssoTimer) { clearInterval(ssoTimer); ssoTimer = null }
  const target = String(route.query.redirect || '/')
  const safe = target.startsWith('/') && !target.startsWith('//') ? target : '/'
  window.location.href = '/api/auth/sso-login?redirect=' + encodeURIComponent(safe)
}

function usePassword() {
  if (ssoTimer) { clearInterval(ssoTimer); ssoTimer = null }
  showPwdForm.value = true
}

onMounted(async () => {
  if (route.query.pwd === '1') showPwdForm.value = true
  try {
    const res = await fetch('/api/auth/config')
    const data = await res.json()
    ssoEnabled.value = !!data.sso_enabled
  } catch {}
  if (ssoEnabled.value && !showPwdForm.value) {
    ssoTimer = setInterval(() => {
      countdown.value -= 1
      if (countdown.value <= 0) {
        clearInterval(ssoTimer)
        ssoTimer = null
        goSso()
      }
    }, 1000)
  }
})

onUnmounted(() => {
  if (ssoTimer) clearInterval(ssoTimer)
})

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
.login-page {
  min-height: 100vh;
  display: flex;
}

/* ===================== 左侧品牌区 ===================== */
.brand-panel {
  flex: 1.15;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 60px 72px;
  background:
    radial-gradient(ellipse at 20% 10%, rgba(64, 156, 255, 0.35), transparent 55%),
    radial-gradient(ellipse at 85% 90%, rgba(0, 212, 255, 0.18), transparent 50%),
    linear-gradient(150deg, #0a2e6e 0%, #0b5ed7 55%, #0b6ef5 100%);
  overflow: hidden;
}

/* 蓝图网格 */
.brand-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.06) 1px, transparent 1px);
  background-size: 56px 56px;
}

/* 雷达装饰 */
.radar {
  position: absolute;
  right: -140px;
  top: 50%;
  transform: translateY(-50%);
  width: 480px;
  height: 480px;
}
.radar-ring {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(126, 200, 255, 0.22);
}
.radar-ring.r1 { inset: 0; }
.radar-ring.r2 { inset: 18%; }
.radar-ring.r3 { inset: 36%; border-color: rgba(126, 200, 255, 0.35); }
.radar-sweep {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: conic-gradient(from 0deg, rgba(126, 200, 255, 0.35), transparent 70deg);
  animation: sweep 6s linear infinite;
}
@keyframes sweep {
  to { transform: rotate(360deg); }
}
.radar-dot {
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #9fdcff;
  box-shadow: 0 0 12px rgba(126, 200, 255, 0.9);
  animation: blink 3s ease-in-out infinite;
}
.radar-dot.d1 { left: 30%; top: 22%; }
.radar-dot.d2 { left: 62%; top: 46%; animation-delay: 0.8s; }
.radar-dot.d3 { left: 44%; top: 68%; animation-delay: 1.6s; }
.radar-dot.d4 { left: 20%; top: 52%; animation-delay: 2.2s; }
@keyframes blink {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

/* 品牌文案 */
.brand-content {
  position: relative;
  z-index: 1;
  max-width: 420px;
}
.brand-logo {
  height: 42px;
  width: auto;
  margin-bottom: 24px;
}
.brand-content h1 {
  margin: 0 0 12px;
  font-size: 34px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 4px;
}
.brand-sub {
  margin: 0 0 44px;
  font-size: 12px;
  color: rgba(198, 227, 255, 0.75);
  letter-spacing: 3px;
  font-family: 'Courier New', monospace;
}
.brand-features {
  list-style: none;
  margin: 0;
  padding: 0;
}
.brand-features li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  font-size: 15px;
  color: #e4f1ff;
}
.feat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4cd6ff;
  box-shadow: 0 0 10px rgba(76, 214, 255, 0.8);
  flex-shrink: 0;
}
.brand-footer {
  position: absolute;
  left: 72px;
  bottom: 32px;
  font-size: 10px;
  color: rgba(198, 227, 255, 0.4);
  letter-spacing: 2px;
  font-family: 'Courier New', monospace;
}

/* ===================== 右侧表单区 ===================== */
.form-panel {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(165deg, #f6faff 0%, #e9f2fc 100%);
  overflow: hidden;
  padding: 40px 24px;
}
.grid-bg {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(11, 110, 245, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(11, 110, 245, 0.05) 1px, transparent 1px);
  background-size: 60px 60px;
}

.login-card {
  width: 400px;
  max-width: 100%;
  position: relative;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #d3e3f7;
  border-radius: 16px;
  padding: 44px 40px 32px;
  box-shadow:
    0 20px 50px rgba(20, 80, 170, 0.12),
    0 4px 12px rgba(20, 80, 170, 0.06);
  z-index: 1;
}

.login-header {
  margin-bottom: 30px;
}
.login-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #10314f;
}
.login-header p {
  margin: 8px 0 0;
  font-size: 13px;
  color: #628cb8;
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

.login-tip {
  margin-top: 22px;
  text-align: center;
  font-size: 12px;
  color: #8fa9c6;
}
.pwd-link {
  color: #0b6ef5;
  cursor: pointer;
  font-size: 13px;
}
.pwd-link:hover { text-decoration: underline; }
.form-footer {
  position: absolute;
  bottom: 24px;
  font-size: 10px;
  color: #9db4d0;
  letter-spacing: 2px;
  font-family: 'Courier New', monospace;
}

/* 窄屏隐藏品牌区 */
@media (max-width: 900px) {
  .brand-panel { display: none; }
}
</style>
