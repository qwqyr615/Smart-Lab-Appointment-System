// 所有网络请求的统一入口
// 前端每次和后端交互（登录、获取列表、提交表单）经过它

import axios from 'axios'
import { getToken, logout } from './auth'
import { ElMessage } from 'element-plus'

// console.log(import.meta.env.VITE_API_BASE_URL)

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000 //30s
})

// 拦截器: 请求，返回
// 请求拦截器的配置
service.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (err) => Promise.reject(err)
)

// 返回的拦截器配置
/**
 * response: axios封装后的完整响应
 * err: AxiosError对象
 * data: 后端返回的JSON内容
 * return Promise.reject(data) 把失败的业务错误抛出去，让调用方 catch
 */
service.interceptors.response.use(
  (response) => {
    //response会被axios封装
    const data = response.data
    if (data.code !== 200) {
      ElMessage.error(data.message || '请求失败')
      if (data.code === 401) {
        logout()
        router.push('/login')
        return Promise.reject(data)
      }
      return Promise.reject(data) // 所有业务错误都 reject
    }
    return data
  },
  (err) => {
    if (err.response) {
      const httpStatusCode = err.response.status
      if (httpStatusCode === 401) {
        ElMessage.error('登录状态已失效，请重新登录')
        logout()
        router.push('/login')
      } else {
        ElMessage.error(err.response.data?.message || '请求失败')
      }
    } else {
      // 后端没启动，网络异常了
      ElMessage.error('网络异常，请检查后端服务')
    }
    return Promise.reject(err)
  }
)

export default service
