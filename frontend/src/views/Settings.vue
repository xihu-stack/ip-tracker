<template>
  <div>
    <div class="page-header">
      <div>
        <h2>系统设置</h2>
        <p class="page-sub">SSO 统一门户登录对接（保存后立即生效，无需重启服务）</p>
      </div>
    </div>

    <el-card>
      <template #header>
        <div class="card-title">
          <el-switch v-model="form.sso_enabled" active-text="启用 SSO 统一门户登录" />
        </div>
      </template>

      <el-alert type="info" :closable="false" class="mb16" show-icon>
        <template #title>
          在企业 SSO 侧创建应用时，回调地址（Redirect URI）填写：
          <el-text type="primary" size="large" class="callback-url">{{ callbackUrl }}</el-text>
          <el-button link type="primary" size="small" @click="copyCallback">复制</el-button>
        </template>
        <div style="line-height: 1.9">
          本系统使用标准 OAuth2 授权码流程：未登录访问会自动跳转统一门户，登录后自动返回原页面；
          SSO 用户首次登录自动开户；账号密码登录始终保留（应急入口 <code>/login?pwd=1</code>）。
        </div>
      </el-alert>

      <el-form :model="form" label-width="130px" class="settings-form">
        <el-form-item label="授权地址" required>
          <el-input v-model="form.sso_auth_url" placeholder="https://sso.company.com/authorize" />
        </el-form-item>
        <el-form-item label="Token 地址" required>
          <el-input v-model="form.sso_token_url" placeholder="https://sso.company.com/token" />
        </el-form-item>
        <el-form-item label="用户信息地址">
          <el-input v-model="form.sso_userinfo_url" placeholder="https://sso.company.com/userinfo" />
        </el-form-item>
        <el-form-item label="客户端 ID" required>
          <el-input v-model="form.sso_client_id" placeholder="SSO 侧创建应用得到的 Client ID" />
        </el-form-item>
        <el-form-item label="客户端密钥">
          <el-input
            v-model="form.sso_client_secret" type="password" show-password
            :placeholder="hasSecret ? '已保存（不修改请留空）' : 'Client Secret'"
          />
        </el-form-item>
        <el-form-item label="Scope">
          <el-input v-model="form.sso_scope" placeholder="openid profile email" />
        </el-form-item>
        <el-form-item label="用户名字段">
          <el-select v-model="form.sso_username_field" filterable allow-create default-first-option
                     placeholder="自动识别（常见字段）" style="width: 100%">
            <el-option label="自动识别（推荐）" value="" />
            <el-option label="account" value="account" />
            <el-option label="loginName" value="loginName" />
            <el-option label="preferred_username" value="preferred_username" />
            <el-option label="username" value="username" />
            <el-option label="login" value="login" />
            <el-option label="sub" value="sub" />
            <el-option label="email" value="email" />
            <el-option label="name" value="name" />
          </el-select>
          <div class="field-hint">自建 SSO 返回的用户信息里用户名字段各不相同，登录报"没有可用的用户名"时在此指定</div>
        </el-form-item>

        <el-divider content-position="left">SSO 访问白名单（第二层控制）</el-divider>
        <el-alert type="warning" :closable="false" class="mb16" show-icon>
          <template #title>
            两个名单都留空 = 不限制（所有能通过企业 SSO 认证的人都能登录本系统）。
            建议至少配置其一；命中任一名单即允许登录。
          </template>
          第一层控制在企业 SSO 侧（把本应用的授权范围限制到指定用户/组），此处为本系统的兜底闸门。
        </el-alert>
        <el-form-item label="允许的用户名">
          <el-input v-model="form.sso_allowed_users" type="textarea" :rows="3"
            placeholder="zhangsan, lisi, wangwu（逗号或换行分隔，不区分大小写）" />
        </el-form-item>
        <el-form-item label="允许的邮箱后缀">
          <el-input v-model="form.sso_allowed_domains"
            placeholder="@huashen.bio, @subs.huashen.bio（逗号分隔，匹配以该后缀结尾的邮箱账号）" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存配置</el-button>
          <el-button :loading="testing" @click="testConn">测试连接</el-button>
          <el-button link type="primary" @click="goSsoTest">打开 SSO 登录实测 →</el-button>
        </el-form-item>
      </el-form>

      <el-descriptions v-if="testResult" :column="1" border class="mb16" title="连通性测试结果">
        <el-descriptions-item v-for="(v, k) in testResult.results" :key="k" :label="k">
          <el-tag :type="v.status === 'OK' || v.status.startsWith('可达') ? 'success' : 'danger'" size="small">{{ v.status }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const form = ref({
  sso_enabled: false,
  sso_auth_url: '',
  sso_token_url: '',
  sso_userinfo_url: '',
  sso_client_id: '',
  sso_client_secret: '',
  sso_scope: 'openid profile email',
  sso_username_field: '',
  sso_allowed_users: '',
  sso_allowed_domains: '',
})
const hasSecret = ref(false)
const saving = ref(false)
const testing = ref(false)
const testResult = ref(null)

const callbackUrl = computed(() => window.location.origin + '/api/auth/callback')

async function load() {
  try {
    const res = await api.get('/settings/sso')
    form.value = { ...res.data, sso_client_secret: '' }
    hasSecret.value = !!res.data.sso_has_secret
  } catch {}
}

async function save() {
  saving.value = true
  try {
    const res = await api.put('/settings/sso', form.value)
    ElMessage.success(res.data.message || '已保存')
    await load()
  } catch {} finally {
    saving.value = false
  }
}

async function testConn() {
  testing.value = true
  testResult.value = null
  try {
    const res = await api.post('/settings/sso/test')
    testResult.value = res.data
    if (res.data.ok) ElMessage.success(res.data.message)
    else ElMessage.warning(res.data.message)
  } catch {} finally {
    testing.value = false
  }
}

function goSsoTest() {
  window.open('/api/auth/sso-login?redirect=/', '_blank')
}

function copyCallback() {
  navigator.clipboard?.writeText(callbackUrl.value)
  ElMessage.success('已复制')
}

onMounted(load)
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
.settings-form { max-width: 640px; }
.callback-url { font-family: Consolas, 'Courier New', monospace; }
.field-hint { font-size: 12px; color: var(--text-muted); line-height: 1.6; margin-top: 4px; }
.card-title { display: flex; align-items: center; }
</style>
