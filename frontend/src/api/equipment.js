import request from '@/utils/request'

/**
 * 分页模糊查询实验室
 */
export function getEquipmentPageList(params) {
  return request({
    url: '/api/equipment/list',
    method: 'get',
    params
  })
}

/**
 * 新增实验室
 */
export function createEquipment(data) {
  return request({
    url: '/api/equipment',
    method: 'post',
    data
  })
}

/**
 * 修改实验室
 */
export function updateEquipment(equipmentId, data) {
  return request({
    url: `/api/equipment/${equipmentId}`,
    method: 'put',
    data
  })
}

/**
 * 删除实验室
 */
export function deleteEquipment(equipmentId) {
  return request({
    url: `/api/equipment/${equipmentId}`,
    method: 'delete'
  })
}
