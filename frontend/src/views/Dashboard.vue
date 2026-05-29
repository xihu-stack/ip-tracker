<template>
  <div>
    <h2 style="margin-bottom: 20px">仪表盘</h2>
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="text-align: center">
            <div style="font-size: 36px; font-weight: bold; color: #409EFF">{{ stats.total_employees }}</div>
            <div style="color: #909399; margin-top: 8px">设备总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="text-align: center">
            <div style="font-size: 36px; font-weight: bold; color: #67C23A">{{ stats.online_count }}</div>
            <div style="color: #909399; margin-top: 8px">当前在线</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="text-align: center">
            <div style="font-size: 36px; font-weight: bold; color: #F56C6C">{{ stats.offline_count }}</div>
            <div style="color: #909399; margin-top: 8px">离线设备</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="text-align: center">
            <div style="font-size: 36px; font-weight: bold; color: #E6A23C">{{ stats.day_records }}</div>
            <div style="color: #909399; margin-top: 8px">今日上报</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span style="color: #67C23A">在线设备</span>
          </template>
          <el-table :data="recentEmployees.filter(e => e.is_online)" stripe empty-text="暂无在线设备">
            <el-table-column label="设备" min-width="140">
              <template #default="{ row }">
                <span v-if="row.name">{{ row.name }} <span style="color: #909399; font-size: 12px">({{ row.hostname }})</span></span>
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
            <span style="color: #F56C6C">离线 / 异常设备</span>
          </template>
          <el-table :data="offlineList" stripe empty-text="所有设备正常">
            <el-table-column label="设备" min-width="140">
              <template #default="{ row }">
                <span v-if="row.name">{{ row.name }} <span style="color: #909399; font-size: 12px">({{ row.hostname }})</span></span>
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
        <span>设备分布地图</span>
      </template>
      <div ref="mapChart" style="height: 500px; width: 100%"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getDashboard, getEmployees, getMapData } from '../api'

const stats = ref({ total_employees: 0, online_count: 0, offline_count: 0, day_records: 0, total_records: 0 })
const recentEmployees = ref([])
const offlineList = ref([])
const mapChart = ref(null)

let chartInstance = null

async function initMap(mapData) {
  if (!mapChart.value) return

  // 加载中国地图 GeoJSON
  const resp = await fetch('/china.json')
  const chinaJson = await resp.json()
  echarts.registerMap('china', chinaJson)

  if (chartInstance) {
    chartInstance.dispose()
  }
  chartInstance = echarts.init(mapChart.value)

  // 构造散点数据
  const scatterData = mapData.map(item => ({
    name: item.city,
    value: [item.lng, item.lat, item.count],
    employees: item.employees
  }))

  chartInstance.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0,0,0,0.75)',
      borderColor: '#f5c542',
      borderWidth: 1,
      textStyle: { color: '#fff' },
      formatter(params) {
        if (params.seriesType === 'effectScatter') {
          const d = params.data
          return `<b style="color:#f5c542">${d.name}</b><br/>设备数量：${d.value[2]} 台<br/>设备：${d.employees.join('、')}`
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
        areaColor: '#e9eef5',
        borderColor: '#b0c4de',
        borderWidth: 1
      },
      emphasis: {
        itemStyle: {
          areaColor: '#d4e2f0'
        },
        label: {
          show: true,
          color: '#666',
          fontSize: 10
        }
      },
      label: {
        show: true,
        color: 'rgba(100,100,100,0.45)',
        fontSize: 9
      }
    },
    series: [
      {
        type: 'effectScatter',
        coordinateSystem: 'geo',
        data: scatterData,
        symbolSize(val) {
          return Math.max(14, val[2] * 12)
        },
        rippleEffect: {
          brushType: 'stroke',
          scale: 4,
          period: 3
        },
        itemStyle: {
          color: '#f5c542',
          shadowBlur: 15,
          shadowColor: 'rgba(245, 197, 66, 0.7)'
        },
        label: {
          show: true,
          formatter: '{b}',
          position: 'right',
          color: '#f5c542',
          fontSize: 12,
          fontWeight: 'bold'
        }
      },
      {
        type: 'scatter',
        coordinateSystem: 'geo',
        data: scatterData,
        symbolSize(val) {
          return Math.max(6, val[2] * 5)
        },
        itemStyle: {
          color: '#f5c542'
        },
        silent: true,
        z: 1
      }
    ]
  })
}

async function loadData() {
  try {
    const [dashRes, empRes, mapRes] = await Promise.all([
      getDashboard(),
      getEmployees({ page: 1, page_size: 100 }),
      getMapData()
    ])
    stats.value = dashRes.data
    recentEmployees.value = empRes.data.data
    offlineList.value = dashRes.data.offline_list || []

    await nextTick()
    if (mapRes.data && mapRes.data.length > 0) {
      initMap(mapRes.data)
    } else {
      // 没有地图数据也要显示空白地图
      initMap([])
    }
  } catch {}
}

onMounted(loadData)
</script>
