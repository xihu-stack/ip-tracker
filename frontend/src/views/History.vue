<template>
  <div>
    <h2 style="margin-bottom: 20px">IP 历史查询</h2>
    <el-card>
      <div class="filter-bar">
        <el-select v-model="selectedEmployee" placeholder="选择员工" filterable style="width: 280px" @change="loadRecords">
          <el-option v-for="emp in employeeList" :key="emp.id" :label="emp.name ? emp.name + ' (' + emp.hostname + ')' : emp.hostname" :value="emp.id" />
        </el-select>
        <input type="date" v-model="startDate" @change="loadRecords" class="date-input" />
        <span class="text-muted">至</span>
        <input type="date" v-model="endDate" @change="loadRecords" class="date-input" />
        <el-button type="primary" @click="loadRecords">查询</el-button>
      </div>

      <el-table :data="records" stripe v-loading="loading" empty-text="请选择员工查看 IP 历史记录">
        <el-table-column prop="reported_at" label="上报时间" width="200" />
        <el-table-column prop="ip" label="公网 IP" width="180" />
        <el-table-column prop="city" label="所在城市" />
      </el-table>

      <div class="pagination-wrap">
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

<style scoped>
.filter-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.date-input {
  height: 32px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 0 10px;
  color: var(--text-primary);
  background: var(--bg-input);
  font-size: 14px;
}
.date-input::-webkit-calendar-picker-indicator {
  filter: invert(0.7);
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.text-muted { color: var(--text-muted); }
</style>
