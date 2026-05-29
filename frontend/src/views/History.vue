<template>
  <div>
    <h2 style="margin-bottom: 20px">IP 历史查询</h2>
    <el-card>
      <div style="display: flex; gap: 12px; align-items: center; margin-bottom: 16px; flex-wrap: wrap">
        <el-select v-model="selectedEmployee" placeholder="选择员工" filterable style="width: 280px" @change="loadRecords">
          <el-option v-for="emp in employeeList" :key="emp.id" :label="emp.name ? emp.name + ' (' + emp.hostname + ')' : emp.hostname" :value="emp.id" />
        </el-select>
        <input type="date" v-model="startDate" @change="loadRecords" style="height: 32px; border: 1px solid #dcdfe6; border-radius: 4px; padding: 0 10px; color: #606266; font-size: 14px" />
        <span style="color: #909399">至</span>
        <input type="date" v-model="endDate" @change="loadRecords" style="height: 32px; border: 1px solid #dcdfe6; border-radius: 4px; padding: 0 10px; color: #606266; font-size: 14px" />
        <el-button type="primary" @click="loadRecords">查询</el-button>
      </div>

      <el-table :data="records" stripe v-loading="loading" empty-text="请选择员工查看 IP 历史记录">
        <el-table-column prop="reported_at" label="上报时间" width="200" />
        <el-table-column prop="ip" label="公网 IP" width="180" />
        <el-table-column prop="city" label="所在城市" />
      </el-table>

      <div style="display: flex; justify-content: flex-end; margin-top: 16px">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @current-change="loadRecords"
          @size-change="loadRecords"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getEmployees, getEmployeeRecords } from '../api'

const route = useRoute()
const employeeList = ref([])
const selectedEmployee = ref(null)
const startDate = ref(null)
const endDate = ref(null)
const records = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

async function loadEmployeeList() {
  try {
    const res = await getEmployees({ page: 1, page_size: 100 })
    employeeList.value = res.data.data

    if (route.query.employee_id) {
      selectedEmployee.value = parseInt(route.query.employee_id)
      loadRecords()
    }
  } catch {}
}

async function loadRecords() {
  if (!selectedEmployee.value) return
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value
    const res = await getEmployeeRecords(selectedEmployee.value, params)
    records.value = res.data.data
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

onMounted(loadEmployeeList)
</script>
