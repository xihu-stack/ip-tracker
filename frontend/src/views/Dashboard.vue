<template>
  <div>
    <div class="page-header">
      <h2>实时监控仪表盘</h2>
      <span class="live-badge">● LIVE</span>
    </div>

    <el-row :gutter="16">
      <el-col :span="6" v-for="item in statCards" :key="item.label">
        <div class="stat-card" :style="{ '--card-accent': item.color }">
          <div class="stat-icon-wrap">
            <el-icon :size="22"><component :is="item.icon" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ item.value }}</div>
            <div class="stat-label">{{ item.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-title">
              <span class="dot dot-green"></span> 在线设备
            </div>
          </template>
          <el-table :data="recentEmployees.filter(e => e.is_online)" stripe empty-text="暂无在线设备" max-height="360">
            <el-table-column label="设备" min-width="140">
              <template #default="{ row }">
                <span v-if="row.name" class="emp-name">{{ row.name }} <span class="sub-text">({{ row.hostname }})</span></span>
                <span v-else>{{ row.hostname }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="latest_ip" label="最新 IP" />
            <el-table-column prop="latest_city" label="城市" />
            <el-table-column prop="latest_time" label="上报时间" />
            <el-table-column label="状态" width="80">
              <template #default>
                <el-tag type="success" size="small">在线</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-title">
              <span class="dot dot-red"></span> 离线 / 异常设备
            </div>
          </template>
          <el-table :data="offlineList" stripe empty-text="所有设备正常" max-height="360">
            <el-table-column label="设备" min-width="140">
              <template #default="{ row }">
                <span v-if="row.name" class="emp-name">{{ row.name }} <span class="sub-text">({{ row.hostname }})</span></span>
                <span v-else>{{ row.hostname }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="latest_ip" label="最后 IP" />
            <el-table-column prop="latest_city" label="城市" />
            <el-table-column prop="latest_time" label="最后上报时间" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'never' ? 'danger' : 'warning'" size="small">
                  {{ row.status === 'never' ? '从未上报' : '离线' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 中国地图 -->
    <el-card style="margin-top: 16px">
      <template #header>
        <div class="card-title">
          <span class="dot dot-blue"></span> 设备分布地图
        </div>
      </template>
      <div ref="mapChart" style="height: 500px; width: 100%"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getDashboard, getEmployees, getMapData } from '../api'

const stats = ref({ total_employees: 0, online_count: 0, offline_count: 0, day_records: 0, total_records: 0 })
const recentEmployees = ref([])
const offlineList = ref([])
const mapChart = ref(null)
let chartInstance = null

const statCards = computed(() => [
  { label: '设备总数', value: stats.value.total_employees, color: '#00e5ff', icon: 'Monitor' },
  { label: '当前在线', value: stats.value.online_count, color: '#22c55e', icon: 'Connection' },
  { label: '离线设备', value: stats.value.offline_count, color: '#ef4444', icon: 'Warning' },
  { label: '今日上报', value: stats.value.day_records, color: '#f59e0b', icon: 'DataLine' },
])

async function initMap(mapData) {
  if (!mapChart.value) return
  const resp = await fetch('/china.json')
  const chinaJson = await resp.json()
  echarts.registerMap('china', chinaJson)
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(mapChart.value)

  const scatterData = mapData.map(item => ({
    name: item.city,
    value: [item.lng, item.lat, item.count],
    employees: item.employees
  }))

  chartInstance.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(8,14,32,0.95)',
      borderColor: '#00e5ff',
      borderWidth: 1,
      textStyle: { color: '#e0f0ff' },
      confine: true,
      formatter(params) {
        if (params.seriesType === 'effectScatter') {
          const d = params.data
          const maxShow = 5
          const emps = d.employees.length > maxShow
            ? d.employees.slice(0, maxShow).join('、') + ` 等${d.employees.length}台`
            : d.employees.join('、')
          return `<div style="max-width:260px;word-break:break-all"><b style="color:#00e5ff">${d.name}</b><br/>设备数量：${d.value[2]} 台<br/>设备：${emps}</div>`
        }
        return params.name
      }
    },
    geo: {
      map: 'china',
      roam: true,
      zoom: 1.2,
      center: [104, 36],
      itemStyle: { areaColor: '#0d1b2a', borderColor: '#1b3a5c', borderWidth: 1 },
      emphasis: { itemStyle: { areaColor: '#1a3352' }, label: { show: true, color: '#7ec8e3', fontSize: 10 } },
      label: { show: true, color: 'rgba(120,160,200,0.35)', fontSize: 9 }
    },
    series: [
      {
        type: 'effectScatter',
        coordinateSystem: 'geo',
        data: scatterData,
        symbolSize: 16,
        rippleEffect: { brushType: 'stroke', scale: 4, period: 3 },
        itemStyle: { color: '#00e5ff', shadowBlur: 20, shadowColor: 'rgba(0, 229, 255, 0.6)' },
        label: {
          show: true,
          formatter(p) { return `${p.name}\n${p.value[2]}台` },
          position: 'right',
          color: '#ffffff',
          fontSize: 12,
          fontWeight: 'bold',
          lineHeight: 18,
          textBorderColor: '#000000',
          textBorderWidth: 2
        }
      }
    ]
  })
}

async function loadData() {
  try {
    const [dashRes, empRes, mapRes] = await Promise.all([getDashboard(), getEmployees({ page: 1, page_size: 100 }), getMapData()])
    stats.value = dashRes.data
    recentEmployees.value = empRes.data.data
    offlineList.value = dashRes.data.offline_list || []
    await nextTick()
    initMap(mapRes.data || [])
  } catch {}
}

onMounted(loadData)
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}
.live-badge {
  font-size: 11px;
  color: var(--success);
  background: rgba(34,197,94,0.1);
  border: 1px solid rgba(34,197,94,0.2);
  padding: 2px 10px;
  border-radius: 10px;
  font-family: 'Courier New', monospace;
  letter-spacing: 2px;
  animation: livePulse 2s ease-in-out infinite;
}
@keyframes livePulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* 统计卡片 */
.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}
.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--card-accent), transparent);
  opacity: 0.5;
}
.stat-card:hover {
  border-color: rgba(0,229,255,0.15);
  box-shadow: 0 4px 24px rgba(0,0,0,0.3);
  transform: translateY(-1px);
}
.stat-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(0,229,255,0.06);
  border: 1px solid rgba(0,229,255,0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--card-accent);
  flex-shrink: 0;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
  font-family: 'Courier New', monospace;
  color: var(--card-accent);
}
.stat-label {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}

/* 卡片标题 */
.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.dot-green {
  background: var(--success);
  box-shadow: 0 0 6px rgba(34,197,94,0.5);
}
.dot-red {
  background: var(--danger);
  box-shadow: 0 0 6px rgba(239,68,68,0.5);
}
.dot-blue {
  background: var(--accent);
  box-shadow: 0 0 6px rgba(0,229,255,0.5);
}

.sub-text { color: var(--text-muted); font-size: 12px; }
</style>
