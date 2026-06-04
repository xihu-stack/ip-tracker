<template>
  <div>
    <div class="page-header">
      <h2>实时监控仪表盘</h2>
      <span class="live-badge">● LIVE</span>
    </div>

    <el-row :gutter="20">
      <el-col :span="6" v-for="item in statCards" :key="item.label">
        <div class="stat-card" :style="{ borderColor: item.color + '33' }">
          <div class="stat-icon" :style="{ color: item.color, boxShadow: '0 0 20px ' + item.color + '22' }">
            <el-icon :size="24"><component :is="item.icon" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value" :style="{ color: item.color }">{{ item.value }}</div>
            <div class="stat-label">{{ item.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
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
    <el-card style="margin-top: 20px">
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
  { label: '设备总数', value: stats.value.total_employees, color: '#409EFF', icon: 'Monitor' },
  { label: '当前在线', value: stats.value.online_count, color: '#67C23A', icon: 'Connection' },
  { label: '离线设备', value: stats.value.offline_count, color: '#F56C6C', icon: 'Warning' },
  { label: '今日上报', value: stats.value.day_records, color: '#E6A23C', icon: 'DataLine' },
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
      backgroundColor: 'rgba(8,14,32,0.92)',
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
  margin-bottom: 24px;
}
.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}
.live-badge {
  font-size: 11px;
  color: #67C23A;
  background: rgba(103,194,58,0.1);
  padding: 2px 8px;
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
  border: 1px solid #ebeef5;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s;
}
.stat-card:hover {
  transform: translateY(-2px);
  border-color: rgba(0, 212, 255, 0.15);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
}
.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  background: rgba(0, 212, 255, 0.04);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
  font-family: 'Courier New', monospace;
}
.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 6px;
}

/* 卡片标题 */
.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}
.dot { width: 8px; height: 8px; border-radius: 50%; }
.dot-green { background: #67C23A; }
.dot-red { background: #F56C6C; }
.dot-blue { background: #409EFF; }

.sub-text { color: #909399; font-size: 12px; }
</style>
