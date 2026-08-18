<template>
  <div>
    <div class="page-header">
      <div>
        <h2>位置动态</h2>
        <p class="page-sub">谁不在驻地办公 · 位置变更历史（驻地可在员工列表中编辑）</p>
      </div>
    </div>

    <el-row :gutter="16" class="mb16">
      <el-col :span="6" :xs="12" :sm="12" :md="6">
        <div class="mini-stat" style="--c: #dc2626; --bg: #fef2f2">
          <div class="mini-value">{{ summary.away }}</div>
          <div class="mini-label">异地办公中</div>
        </div>
      </el-col>
      <el-col :span="6" :xs="12" :sm="12" :md="6">
        <div class="mini-stat" style="--c: #16a34a; --bg: #f0fdf4">
          <div class="mini-value">{{ summary.home }}</div>
          <div class="mini-label">在驻地</div>
        </div>
      </el-col>
      <el-col :span="6" :xs="12" :sm="12" :md="6">
        <div class="mini-stat" style="--c: #94a3b8; --bg: #f8fafc">
          <div class="mini-value">{{ summary.unknown }}</div>
          <div class="mini-label">位置未知</div>
        </div>
      </el-col>
      <el-col :span="6" :xs="12" :sm="12" :md="6">
        <div class="mini-stat" style="--c: #d97706; --bg: #fffbeb">
          <div class="mini-value">{{ summary.no_base }}</div>
          <div class="mini-label">未设驻地</div>
        </div>
      </el-col>
    </el-row>

    <el-card class="mb16">
      <template #header>
        <div class="card-title">
          <span class="dot dot-red"></span> 当前不在驻地办公的人员
          <el-tag v-if="awayList.length" type="danger" size="small" effect="dark" class="ml8">{{ awayList.length }} 人</el-tag>
        </div>
      </template>
      <el-table :data="awayList" stripe v-loading="loading" empty-text="所有人员均在驻地办公 🎉">
        <el-table-column label="人员" min-width="150">
          <template #default="{ row }">
            <span v-if="row.name">{{ row.name }} <span class="sub-text">({{ row.hostname }})</span></span>
            <span v-else>{{ row.hostname }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="base_city" label="驻地" width="140">
          <template #default="{ row }">{{ shortCity(row.base_city) }}</template>
        </el-table-column>
        <el-table-column label="当前城市" width="140">
          <template #default="{ row }">
            <el-tag type="danger" size="small" effect="plain">{{ shortCity(row.current_city) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="current_ip" label="当前 IP" width="140" />
        <el-table-column prop="away_since" label="外出开始" width="150" />
        <el-table-column label="已外出时长" min-width="120">
          <template #default="{ row }">
            <span :class="{ 'long-away': (row.away_hours || 0) >= 72 }">{{ awayText(row.away_hours) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-title">
          <span class="dot dot-blue"></span> 最近 7 天位置变更记录
        </div>
      </template>
      <el-table :data="changes" stripe max-height="420" empty-text="最近 7 天没有位置变更">
        <el-table-column prop="time" label="时间" width="150" />
        <el-table-column label="人员" min-width="150">
          <template #default="{ row }">
            <span v-if="row.name">{{ row.name }} <span class="sub-text">({{ row.hostname }})</span></span>
            <span v-else>{{ row.hostname }}</span>
          </template>
        </el-table-column>
        <el-table-column label="位置变化" min-width="260">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ shortCity(row.from_city) }}</el-tag>
            <span class="arrow">→</span>
            <el-tag :type="row.is_away ? 'danger' : 'success'" size="small" effect="plain">{{ shortCity(row.to_city) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const summary = ref({ total: 0, base_set: 0, away: 0, home: 0, unknown: 0, no_base: 0 })
const awayList = ref([])
const changes = ref([])
const loading = ref(false)

function shortCity(name) {
  return String(name || '').split('-').pop() || '-'
}

function awayText(hours) {
  if (hours == null) return '—'
  if (hours < 1) return '刚离开'
  if (hours < 24) return `${Math.round(hours)} 小时`
  return `${Math.floor(hours / 24)} 天 ${Math.round(hours % 24)} 小时`
}

async function load() {
  loading.value = true
  try {
    const res = await api.get('/location-stats')
    summary.value = res.data.summary
    awayList.value = res.data.away_list
    changes.value = res.data.changes
  } catch {} finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
.ml8 { margin-left: 8px; }
.sub-text { color: var(--text-muted); font-size: 12px; }
.card-title { display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 14px; }
.dot { width: 8px; height: 8px; border-radius: 50%; }
.dot-red { background: var(--danger); }
.dot-blue { background: var(--accent); }
.arrow { margin: 0 8px; color: var(--text-muted); }
.long-away { color: var(--danger); font-weight: 600; }

.mini-stat {
  background: var(--bg);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 14px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.mini-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--c);
  font-family: 'Courier New', monospace;
}
.mini-label { font-size: 13px; color: var(--text-muted); margin-left: 12px; }
</style>
