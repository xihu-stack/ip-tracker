<template>
  <div>
    <div class="page-header">
      <h2>实时监控仪表盘</h2>
      <span class="live-badge">● LIVE</span>
    </div>

    <el-row :gutter="16">
      <el-col :span="6" v-for="item in statCards" :key="item.label">
        <div class="stat-card" :style="{ '--card-accent': item.color, '--card-bg': item.bg }">
          <div class="stat-icon-wrap" :style="{ background: item.bg }">
            <el-icon :size="22" :style="{ color: item.color }"><component :is="item.icon" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value" :style="{ color: item.color }">{{ item.value }}</div>
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
                <span v-if="row.name">{{ row.name }} <span class="sub-text">({{ row.hostname }})</span></span>
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
                <span v-if="row.name">{{ row.name }} <span class="sub-text">({{ row.hostname }})</span></span>
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
  { label: '设备总数', value: stats.value.total_employees, color: '#2563eb', bg: '#eff6ff', icon: 'Monitor' },
  { label: '当前在线', value: stats.value.online_count, color: '#16a34a', bg: '#f0fdf4', icon: 'Connection' },
  { label: '离线设备', value: stats.value.offline_count, color: '#dc2626', bg: '#fef2f2', icon: 'Warning' },
  { label: '今日上报', value: stats.value.day_records, color: '#d97706', bg: '#fffbeb', icon: 'DataLine' },
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
      backgroundColor: 'rgba(255,255,255,0.96)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#1e293b', fontSize: 13 },
      confine: true,
      extraCssText: 'box-shadow: 0 4px 16px rgba(0,0,0,0.12); border-radius: 8px;',
      formatter(params) {
        if (params.seriesType === 'effectScatter') {
          const d = params.data
          const maxShow = 5
          const emps = d.employees.length > maxShow
            ? d.employees.slice(0, maxShow).join('、') + ` 等${d.employees.length}台`
            : d.employees.join('、')
          return `<div style="max-width:280px;word-break:break-all"><b style="color:#2563eb;font-size:14px">${d.name}</b><br/><span style="color:#64748b">设备数量：</span><b>${d.value[2]}</b> 台<br/><span style="color:#64748b">设备：</span>${emps}</div>`
        }
        return params.name
      }
    },
    geo: {
      map: 'china',
      roam: true,
      zoom: 1.2,
      center: [104, 36],
      itemStyle: {
        areaColor: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: '#dbe4f0' },
            { offset: 1, color: '#c8d5e5' }
          ]
        },
        borderColor: '#b0bfd2',
        borderWidth: 0.6
      },
      emphasis: {
        itemStyle: {
          areaColor: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: '#c7d6ea' },
              { offset: 1, color: '#b3c5dc' }
            ]
          }
        },
        label: { show: true, color: '#475569', fontSize: 10 }
      },
      label: { show: true, color: 'rgba(71,85,105,0.4)', fontSize: 9 }
    },
    // 缩放动画
    animation: true,
    animationDuration: 800,
    animationEasing: 'cubicOut',
    series: [
      // 热力光晕底层
      {
        type: 'scatter',
        coordinateSystem: 'geo',
        data: scatterData,
        symbolSize(val) { return Math.sqrt(val[2]) * 18 + 8 },
        itemStyle: { color: 'rgba(37, 99, 235, 0.07)' },
        silent: true,
        z: 1
      },
      // 涟漪散点
      {
        type: 'effectScatter',
        coordinateSystem: 'geo',
        data: scatterData,
        symbolSize(val) { return Math.sqrt(val[2]) * 5 + 6 },
        rippleEffect: { brushType: 'stroke', scale: 3.5, period: 4 },
        itemStyle: {
          color: {
            type: 'radial', x: 0.5, y: 0.5, r: 0.5,
            colorStops: [
              { offset: 0, color: '#60a5fa' },
              { offset: 0.6, color: '#2563eb' },
              { offset: 1, color: '#1d4ed8' }
            ]
          },
          shadowBlur: 16,
          shadowColor: 'rgba(37, 99, 235, 0.5)'
        },
        label: { show: false },
        z: 2
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
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; }
.live-badge {
  font-size: 11px;
  color: var(--success);
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
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
  background: #fff;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.2s;
}
.stat-card:hover {
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  transform: translateY(-1px);
}
.stat-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
  font-family: 'Courier New', monospace;
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
.dot { width: 8px; height: 8px; border-radius: 50%; }
.dot-green { background: var(--success); }
.dot-red { background: var(--danger); }
.dot-blue { background: var(--accent); }

.sub-text { color: var(--text-muted); font-size: 12px; }
</style>
