// 发送请求的函数
import request from '@/utils/request'

/**
 * 登入请求
 * @param data
 * @returns
 */
export function loginAPi(data) {
  return request({
    url: '/api/auth/login',
    method: 'post',
    data
  })
}

/**
 * 注册请求
 */
export function registerAPi(data) {
  return request({
    url: '/api/auth/register',
    method: 'post',
    data
  })
}
