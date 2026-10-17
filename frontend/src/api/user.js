import request from '@/utils/request'
/**
 * 获取当前登录用户
 */
export function getUserInfo(data) {
  return request({
    url: '/api/user/info',
    method: 'get',
    data
  })
}

/**
 * 修改当前登录用户的个人信息
 */
export function updateUserInfo(data) {
  return request({
    url: '/api/user/update',
    method: 'put',
    data
  })
}
