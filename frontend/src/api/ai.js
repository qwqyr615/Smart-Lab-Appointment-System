import request from '@/utils/request'

export function chat(data) {
  return request({
    url: '/api/ai/chat',
    method: 'post',
    data,
    timeout: 180000
  })
}
