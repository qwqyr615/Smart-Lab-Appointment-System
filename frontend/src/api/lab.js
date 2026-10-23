import request from '@/utils/request'

/**
 * 分页查询实验室
 */
export function getLabPageList(params) {
  return request({
    url: '/api/lab/list',
    method: 'get',
    params
  })
}

/**
 * 根据ID查询实验室详情
 */
export function getLab(lab_id) {
  return request({
    url: `/api/lab/${lab_id}`,
    method: 'get'
  })
}

/**
 * 新增实验室
 */
export function createLab(data) {
  return request({
    url: '/api/lab',
    method: 'post',
    data
  })
}

/**
 * 修改实验室
 */
export function updateLab(labId, data) {
  return request({
    url: `/api/lab/${labId}`,
    method: 'put',
    data
  })
}

/**
 * 删除实验室
 */
export function deleteLab(labId) {
  return request({
    url: `/api/lab/${labId}`,
    method: 'delete'
  })
}
