import request from '@/utils/request'
/**
 * 获取当前登录用户
 */
export function getUserInfo(data) {
  return request({
    url: '/api/user/me',
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

/**
 * 修改密码
 */
export function updatePassword(data) {
  return request({
    url: '/api/user/password',
    method: 'put',
    data
  })
}

/**
 * 分页模糊查询用户列表
 */
export function getUserPageList(params) {
  return request({
    url: '/api/user/list',
    method: 'get',
    params
  })
}
