import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截：注入 JWT token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：401 跳登录页
api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      if (router.currentRoute.value.path !== '/login') {
        ElMessage.error('登录已过期，请重新登录')
        router.push('/login')
      }
    } else {
      ElMessage.error(err.response?.data?.detail || '请求失败')
    }
    return Promise.reject(err)
  }
)

// 认证 API
export const login = (data) => api.post('/login', data)
export const changePassword = (data) => api.put('/change-password', data)

// 业务 API
export const reportIp = (data) => api.post('/report', data)
export const getDashboard = () => api.get('/dashboard')
export const getEmployees = (params) => api.get('/employees', { params })
export const getEmployeeRecords = (employeeId, params) => api.get(`/employees/${employeeId}/records`, { params })
export const getMapData = () => api.get('/map-data')
export const updateEmployee = (id, data) => api.put(`/employees/${id}`, data)

export default api
