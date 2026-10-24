import request from '@/utils/request'

/**
 * 创建预约
 */
export function createReservation(data) {
  return request({
    url: '/api/reservation',
    method: 'post',
    data
  })
}

/**
 *  查看预约记录
 */
export function getReservationPageList(params) {
  return request({
    url: '/api/reservation/list',
    method: 'get',
    params
  })
}

/**
 * 取消预约
 */
export function cancelReservation(id) {
  return request({
    url: `/api/reservation/${id}/cancel`,
    method: 'put'
  })
}

/**
 * 审核预约
 */
export function auditReservation(id, status) {
  return request({
    url: `/api/reservation/${id}/audit`,
    method: 'put',
    data: { status }
  })
}
