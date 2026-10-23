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
