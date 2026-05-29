import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

api.interceptors.response.use(
  res => res,
  err => {
    ElMessage.error(err.response?.data?.detail || '请求失败')
    return Promise.reject(err)
  }
)

export const reportIp = (data) => api.post('/report', data)
export const getDashboard = () => api.get('/dashboard')
export const getEmployees = (params) => api.get('/employees', { params })
export const getEmployeeRecords = (employeeId, params) => api.get(`/employees/${employeeId}/records`, { params })
export const getMapData = () => api.get('/map-data')
export const updateEmployee = (id, data) => api.put(`/employees/${id}`, data)

export default api
