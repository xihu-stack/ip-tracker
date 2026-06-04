<template>
  <div>
    <h2 style="margin-bottom: 20px">员工列表</h2>
    <el-card>
      <div class="toolbar">
        <el-input v-model="search" placeholder="搜索主机名或姓名" style="width: 300px" clearable @clear="loadData" @keyup.enter="loadData">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button type="primary" @click="loadData">查询</el-button>
      </div>

      <el-table :data="employees" stripe v-loading="loading">
        <el-table-column label="员工姓名" width="140">
          <template #default="{ row }">
            <span v-if="row.name">{{ row.name }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="hostname" label="主机名" />
        <el-table-column prop="latest_ip" label="最新 IP" />
        <el-table-column prop="latest_city" label="所在城市" />
        <el-table-column prop="latest_time" label="最后上报时间" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_online ? 'success' : 'info'" size="small">
              {{ row.is_online ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="210">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openEdit(row)">编辑</el-button>
            <el-button type="primary" link size="small" @click="viewHistory(row)">查看历史</el-button>
            <el-popconfirm title="确定删除该员工及其所有上报记录？" confirm-button-text="删除" cancel-button-text="取消" confirm-button-type="danger" @confirm="handleDelete(row)">
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
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
          @current-change="loadData"
          @size-change="loadData"
        />
      </div>
    </el-card>

    <!-- 编辑姓名弹窗 -->
    <el-dialog v-model="editVisible" title="编辑员工姓名" width="400px">
      <el-form label-width="80px">
        <el-form-item label="主机名">
          <el-input :model-value="editRow?.hostname" disabled />
        </el-form-item>
        <el-form-item label="员工姓名">
          <el-input v-model="editName" placeholder="请输入员工姓名" @keyup.enter="saveName" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="saveName" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getEmployees, updateEmployee, deleteEmployee } from '../api'

const router = useRouter()
const employees = ref([])
const loading = ref(false)
const search = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const editVisible = ref(false)
const editRow = ref(null)
const editName = ref('')
const saving = ref(false)

async function loadData() {
  loading.value = true
  try {
    const res = await getEmployees({ search: search.value, page: page.value, page_size: pageSize.value })
    employees.value = res.data.data
    total.value = res.data.total
  } catch {
  } finally {
    loading.value = false
  }
}

function openEdit(row) {
  editRow.value = row
  editName.value = row.name || ''
  editVisible.value = true
}

async function saveName() {
  saving.value = true
  try {
    await updateEmployee(editRow.value.id, { name: editName.value })
    ElMessage.success('保存成功')
    editVisible.value = false
    loadData()
  } catch {
  } finally {
    saving.value = false
  }
}

function viewHistory(row) {
  router.push({ path: '/history', query: { employee_id: row.id, hostname: row.hostname } })
}

async function handleDelete(row) {
  try {
    await deleteEmployee(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch {}
}

onMounted(loadData)
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.text-muted { color: #909399; }
</style>
