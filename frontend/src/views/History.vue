<template>
  <div>
    <div class="page-header">
      <div>
        <h2>IP 历史查询</h2>
        <p class="page-sub">按员工和日期范围追溯公网 IP 变更轨迹</p>
      </div>
    </div>
    <el-card>
      <div class="filter-bar">
        <el-select v-model="selectedEmployee" placeholder="选择员工" filterable style="width: 280px" @change="loadRecords">
          <el-option v-for="emp in employeeList" :key="emp.id" :label="emp.name ? emp.name + ' (' + emp.hostname + ')' : emp.hostname" :value="emp.id" />
        </el-select>
        <el-date-picker v-model="startDate" type="date" placeholder="开始日期" value-format="YYYY-MM-DD" style="width: 150px" @change="loadRecords" />
        <span class="text-muted">至</span>
        <el-date-picker v-model="endDate" type="date" placeholder="结束日期" value-format="YYYY-MM-DD" style="width: 150px" @change="loadRecords" />
        <el-button type="primary" @click="loadRecords">查询</el-button>
      </div>

      <el-table :data="records" stripe v-loading="loading" empty-text="请选择员工查看 IP 历史记录">
        <el-table-column prop="reported_at" label="上报时间" width="200" />
        <el-table-column prop="ip" label="公网 IP" width="180" />
        <el-table-column label="所在城市">
          <template #default="{ row }">
            <span>{{ row.city }}</span>
            <el-tag v-if="row.city_source === 'manual'" size="small" effect="plain" style="margin-left:6px; color:#d97706; border-color:#fcd34d; background:#fffbeb">人工</el-tag>
            <el-button link type="primary" size="small" style="margin-left:6px" @click="openEditCity(row)">改</el-button>
          </template>
        </el-table-column>
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

    <!-- 修改城市弹窗 -->
    <el-dialog v-model="editCityVisible" title="修正城市" width="420px">
      <el-form label-width="90px">
        <el-form-item label="IP">
          <el-input :model-value="editRow?.ip" disabled />
        </el-form-item>
        <el-form-item label="时间">
          <el-input :model-value="editRow?.reported_at" disabled />
        </el-form-item>
        <el-form-item label="城市">
          <el-input v-model="editCity" placeholder="如 江苏-苏州市，填 未知 可清除定位" />
        </el-form-item>
      </el-form>
      <div style="font-size:12px;color:var(--text-muted);line-height:1.8">
        修正后的值标记为「人工」，在线解析和自动修正都不会再覆盖它。
      </div>
      <template #footer>
        <el-button @click="editCityVisible = false">取消</el-button>
        <el-button type="primary" :loading="editSaving" @click="saveCity">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getEmployees, getEmployeeRecords, updateRecord } from '../api'

const route = useRoute()
const employeeList = ref([])
const selectedEmployee = ref(null)
const startDate = ref('')
const endDate = ref('')
const records = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const editCityVisible = ref(false)
const editRow = ref(null)
const editCity = ref('')
const editSaving = ref(false)

function openEditCity(row) {
  editRow.value = row
  editCity.value = row.city === '未知' ? '' : row.city
  editCityVisible.value = true
}

async function saveCity() {
  editSaving.value = true
  try {
    await updateRecord(editRow.value.id, { city: editCity.value.trim() || '未知' })
    ElMessage.success('已修正')
    editCityVisible.value = false
    loadRecords()
  } catch {} finally {
    editSaving.value = false
  }
}

async function loadEmployeeList() {
  try {
    const res = await getEmployees({ page: 1, page_size: 500 })
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
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.text-muted { color: #909399; }
</style>
