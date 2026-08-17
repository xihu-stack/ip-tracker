<template>
  <div>
    <div class="page-header">
      <div>
        <h2>实时监控仪表盘</h2>
        <p class="page-sub">设备在线状态 · 地理分布 · 上报动态（每 30 秒自动刷新）</p>
      </div>
      <span class="live-badge">● LIVE</span>
    </div>

    <el-row :gutter="16">
      <el-col :span="6" :xs="24" :sm="12" :md="6" v-for="item in statCards" :key="item.label">
        <div class="stat-card" :style="{ '--card-accent': item.color, '--card-bg': item.bg }">
          <div class="stat-icon-wrap" :style="{ background: item.bg }">
            <el-icon :size="22" :style="{ color: item.color }"><component :is="item.icon" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value" :style="{ color: item.color }">{{ item.value }}</div>
            <div class="stat-label">{{ item.label }}</div>
          </div>
          <div class="stat-spark" v-if="item.spark" :title="'最近24小时上报趋势'">
            <span
              v-for="(n, i) in item.spark" :key="i" class="spark-bar"
              :style="{ height: sparkH(n, item.spark), background: item.color }"
            ></span>
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
                <el-tag :type="row.status === 'never' ? 'danger' : (row.status === 'stale' ? 'info' : 'warning')" size="small">
                  {{ row.status === 'never' ? '从未上报' : (row.status === 'stale' ? '失联30天+' : '离线') }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 中国地图 + 城市排行 -->
    <el-row :gutter="16" class="map-row">
      <el-col :span="16" :xs="24">
        <el-card class="map-card">
          <template #header>
            <div class="card-title">
              <span class="dot dot-blue"></span> 设备分布地图
              <span class="map-hint">滚轮缩放 · 拖拽移动 · 悬停查看设备明细</span>
            </div>
          </template>
          <div ref="mapChart" class="map-canvas"></div>
        </el-card>
      </el-col>
      <el-col :span="8" :xs="24">
        <el-card class="rank-card">
          <template #header>
            <div class="card-title">
              <span class="dot dot-orange"></span> 城市设备排行
            </div>
          </template>
          <el-alert
            v-if="unmappedList.length"
            type="warning" :closable="false" show-icon class="unmapped-alert"
            :title="`有 ${unmappedTotal} 台设备未能定位到地图`"
          >
            <template #default>
              {{ unmappedList.map(u => `${u.city}×${u.count}`).join('、') }}（多为归属地查询失败或境外 IP）
            </template>
          </el-alert>
          <div class="rank-list" v-if="rankList.length">
            <div v-for="(item, idx) in rankList" :key="item.city" class="rank-item">
              <span class="rank-no" :class="'top' + Math.min(idx + 1, 4)">{{ idx + 1 }}</span>
              <span class="rank-name" :title="item.city">{{ shortCity(item.city) }}</span>
              <div class="rank-bar-wrap">
                <div class="rank-bar" :style="{ width: barWidth(item.count) + '%' }"></div>
              </div>
              <span class="rank-count">{{ item.count }} 台</span>
            </div>
          </div>
          <el-empty v-else description="暂无定位数据" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
// ECharts 按需引入：只打包用到的图表类型，显著减小体积
import * as echarts from 'echarts/core'
import { MapChart, ScatterChart, EffectScatterChart } from 'echarts/charts'
import { GeoComponent, TooltipComponent } from 'echarts/components'
import { LabelLayout } from 'echarts/features'
import { CanvasRenderer } from 'echarts/renderers'
import { getDashboard, getEmployees, getMapData } from '../api'

echarts.use([MapChart, ScatterChart, EffectScatterChart, GeoComponent, TooltipComponent, LabelLayout, CanvasRenderer])

const stats = ref({ total_employees: 0, online_count: 0, offline_count: 0, day_records: 0, total_records: 0 })
const recentEmployees = ref([])
const offlineList = ref([])
const mapChart = ref(null)
let chartInstance = null

const rankList = computed(() => [...mapPoints.value].sort((a, b) => b.count - a.count))
const mapPoints = ref([])
const unmappedList = ref([])
const unmappedTotal = computed(() => unmappedList.value.reduce((s, u) => s + u.count, 0))

function shortCity(name) {
  return String(name || '').split('-').pop()
}

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ))
}

function barWidth(count) {
  const max = rankList.value[0]?.count || 1
  return Math.max(8, Math.round(count / max * 100))
}

const statCards = computed(() => [
  { label: '设备总数', value: stats.value.total_employees, color: '#2563eb', bg: '#eff6ff', icon: 'Monitor' },
  { label: '当前在线', value: stats.value.online_count, color: '#16a34a', bg: '#f0fdf4', icon: 'Connection' },
  { label: '离线设备', value: stats.value.offline_count, color: '#dc2626', bg: '#fef2f2', icon: 'Warning' },
  { label: '今日上报', value: stats.value.day_records, color: '#d97706', bg: '#fffbeb', icon: 'DataLine', spark: stats.value.hourly?.map(h => h.count) },
])

function sparkH(n, arr) {
  const max = Math.max(...arr, 1)
  return `${Math.max(3, Math.round(n / max * 26))}px`
}

let chinaJsonPromise = null
function getChinaJson() {
  if (!chinaJsonPromise) {
    chinaJsonPromise = fetch('/china.json').then(resp => resp.json())
  }
  return chinaJsonPromise
}

async function initMap(mapData) {
  if (!mapChart.value) return
  const chinaJson = await getChinaJson()
  echarts.registerMap('china', chinaJson)
  // 只初始化一次，后续刷新仅更新数据——避免 dispose 重建导致用户的缩放/拖动视角被重置
  if (!chartInstance) {
    chartInstance = echarts.init(mapChart.value)
  }

  const scatterData = mapData.map(item => ({
    name: item.city,
    value: [item.lng, item.lat, item.count],
    employees: item.employees
  }))
  // 按数量降序：大的先画在底层，小的后画在顶层，不遮挡
  scatterData.sort((a, b) => b.value[2] - a.value[2])

  chartInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.96)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#1e293b', fontSize: 13 },
      confine: true,
      extraCssText: 'box-shadow: 0 4px 16px rgba(0,0,0,0.12); border-radius: 8px;',
      formatter(params) {
        if (params.seriesType !== 'effectScatter') return params.name
        const d = params.data
        const maxShow = 8
        const list = d.employees.slice(0, maxShow)
          .map(n => `<div style="line-height:1.9">· ${escapeHtml(n)}</div>`)
          .join('')
        const more = d.employees.length > maxShow
          ? `<div style="color:#94a3b8;line-height:1.9">…共 ${d.employees.length} 台</div>`
          : ''
        return `<div style="max-width:260px;overflow-wrap:anywhere">` +
          `<b style="color:#ea580c;font-size:14px">${escapeHtml(shortCity(d.name))}</b>` +
          `<span style="color:#64748b"> · ${d.value[2]} 台设备</span>` +
          `<div style="margin-top:4px">${list}${more}</div></div>`
      }
    },
    geo: {
      map: 'china',
      roam: true,
      zoom: 1.2,
      center: [104, 36],
      itemStyle: {
        areaColor: '#ffffff',
        borderColor: '#c2d4ec',
        borderWidth: 1,
        shadowColor: 'rgba(30, 80, 160, 0.20)',
        shadowBlur: 12
      },
      emphasis: {
        itemStyle: { areaColor: '#eaf2fd' },
        label: { show: false }
      },
      label: { show: false }
    },
    animation: true,
    animationDuration: 800,
    animationEasing: 'cubicOut',
    series: [
      // 底层光晕：设备越多光圈越大，但设上限（90px）防止大城市糊成一片盖住周边
      {
        type: 'scatter',
        coordinateSystem: 'geo',
        data: scatterData,
        symbolSize(val) { return Math.min(18 + Math.sqrt(val[2]) * 14, 90) },
        itemStyle: { color: 'rgba(234, 88, 12, 0.10)' },
        silent: true,
        z: 1
      },
      // 橙色涟漪散点 + 城市名/设备数标注（重叠自动隐藏，缩放后自动补显）
      {
        type: 'effectScatter',
        coordinateSystem: 'geo',
        data: scatterData,
        symbolSize(val) { return Math.min(10 + Math.sqrt(val[2]) * 4, 30) },
        rippleEffect: { brushType: 'stroke', scale: 3, period: 4 },
        itemStyle: {
          color: {
            type: 'radial', x: 0.5, y: 0.5, r: 0.5,
            colorStops: [
              { offset: 0, color: '#fdba74' },
              { offset: 0.55, color: '#f97316' },
              { offset: 1, color: '#ea580c' }
            ]
          },
          borderColor: '#ffffff',
          borderWidth: 2,
          shadowBlur: 10,
          shadowColor: 'rgba(234, 88, 12, 0.55)'
        },
        label: {
          show: true,
          position: 'top',
          distance: 8,
          formatter: p => `${shortCity(p.name)} ${p.value[2]}台`,
          color: '#9a3412',
          fontSize: 13,
          fontWeight: 700,
          textBorderColor: '#ffffff',
          textBorderWidth: 3
        },
        // 相近城市（如苏州/南京）标签重叠时上下错开，而不是隐藏
        labelLayout: { moveOverlap: 'shiftY' },
        emphasis: { scale: 1.4 },
        z: 2
      }
    ]
  })
}

async function loadData() {
  try {
    const [dashRes, empRes, mapRes] = await Promise.all([getDashboard(), getEmployees({ page: 1, page_size: 500 }), getMapData()])
    stats.value = dashRes.data
    recentEmployees.value = empRes.data.data
    offlineList.value = dashRes.data.offline_list || []
    // 兼容新旧后端格式：新版返回 {points, unmapped}，旧版直接返回数组
    const raw = mapRes.data
    if (Array.isArray(raw)) {
      mapPoints.value = raw
      unmappedList.value = []
    } else {
      mapPoints.value = raw.points || []
      unmappedList.value = raw.unmapped || []
    }
    await nextTick()
    initMap(mapPoints.value)
  } catch {}
}

let refreshTimer = null
onMounted(() => {
  loadData()
  refreshTimer = setInterval(loadData, 30000)
})
onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
.page-header h2 { margin: 0; font-size: 20px; font-weight: 700; }
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
  position: relative;
  overflow: hidden;
}
.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--card-accent);
  opacity: 0.9;
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
  font-variant-numeric: tabular-nums;
}
.stat-label {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}

/* 今日上报迷你趋势（最近24小时） */
.stat-spark {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 28px;
  margin-left: auto;
  opacity: 0.55;
}
.spark-bar {
  width: 4px;
  border-radius: 1px;
  min-height: 3px;
  display: inline-block;
}

/* 卡片标题 */
.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
}
.map-hint {
  margin-left: auto;
  font-weight: 400;
  font-size: 12px;
  color: var(--text-muted);
}
.dot { width: 8px; height: 8px; border-radius: 50%; }
.dot-green { background: var(--success); }
.dot-red { background: var(--danger); }
.dot-blue { background: var(--accent); }
.dot-orange { background: #f97316; }

/* 地图 + 排行双栏 */
.map-row { margin-top: 16px; }
.rank-card { height: 100%; }
.rank-list { display: flex; flex-direction: column; max-height: 460px; overflow-y: auto; }
.rank-item { display: flex; align-items: center; gap: 10px; padding: 9px 4px; border-bottom: 1px dashed var(--border-color); }
.rank-item:last-child { border-bottom: none; }
.rank-no { width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; color: #94a3b8; background: #f1f5f9; flex-shrink: 0; }
.rank-no.top1 { background: #ea580c; color: #fff; }
.rank-no.top2 { background: #f97316; color: #fff; }
.rank-no.top3 { background: #fdba74; color: #9a3412; }
.rank-name { width: 84px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; color: var(--text-primary); flex-shrink: 0; }
.rank-bar-wrap { flex: 1; height: 8px; background: #f1f5f9; border-radius: 4px; overflow: hidden; }
.rank-bar { height: 100%; background: linear-gradient(90deg, #fdba74, #f97316); border-radius: 4px; }
.rank-count { font-size: 13px; font-weight: 600; color: var(--text-secondary); flex-shrink: 0; }
.unmapped-alert { margin-bottom: 10px; }

/* 地图画布：浅蓝海洋渐变衬托白色陆地 */
.map-canvas {
  height: 500px;
  width: 100%;
  background: linear-gradient(180deg, #ecf4fe 0%, #dce9fb 100%);
  border-radius: 8px;
}

.sub-text { color: var(--text-muted); font-size: 12px; }
</style>
