import { getToken, logout } from '@/utils/auth'
import router from '@/router'

// 模型思考、工具执行期间可能一段时间没有字节，超过这个时间就认为卡死
const IDLE_TIMEOUT_MS = 90000

/**
 * SSE 流式对话。onEvent(evt) 每收到一条 data 回调一次。
 * signal 传 AbortController.signal，用于用户点"停止"或离开页面时取消。
 */
export async function chatStream(data, onEvent, { signal } = {}) {
  const baseURL = import.meta.env.VITE_API_BASE_URL || ''
  const token = getToken()
  const res = await fetch(`${baseURL}/api/ai/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      // EventSource 带不了自定义头；fetch 可以带 JWT
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify(data),
    signal
  })

  if (res.status === 401) {
    // 和 axios 拦截器保持一致：清凭证并回登录页
    logout()
    router.push('/login')
    throw new Error('登录已失效，请重新登录')
  }
  if (!res.ok || !res.body) {
    const payload = await res.json().catch(() => null)
    throw new Error(payload?.message || '流式接口请求失败')
  }

  const contentType = res.headers.get('content-type') || ''
  // 若被全局异常收成普通 JSON，不能按 SSE 去拆
  if (!contentType.includes('text/event-stream')) {
    const payload = await res.json().catch(() => null)
    throw new Error(payload?.message || '流式接口返回异常')
  }

  // getReader：按二进制块读响应体，不是等全部下载完
  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  // buffer：TCP 可能把半条 SSE 拆开送达，要先攒着
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await readWithTimeout(reader, IDLE_TIMEOUT_MS)
      // HTTP 流结束不等于 Agent 已完成，必须收到业务结束事件。
      if (done) {
        throw new Error(
          '响应中断，未收到结束事件；若涉及预约，请到「我的预约」核实是否已提交'
        )
      }
      // 规范允许 CRLF，统一成 \n 再切帧
      buffer += decoder.decode(value, { stream: true })
      buffer = buffer.replace(/\r\n/g, '\n')

      const chunks = buffer.split('\n\n')
      buffer = chunks.pop() || ''
      for (const chunk of chunks) {
        // 一帧里的多行 data 按 SSE 规范拼接
        const raw = chunk
          .split('\n')
          .filter((line) => line.startsWith('data:'))
          .map((line) => line.slice(5).trim())
          .join('')
        if (!raw) continue
        let event
        try {
          event = JSON.parse(raw)
        } catch {
          continue // 坏帧跳过，别让一条脏数据中断整条流
        }
        onEvent(event)
        // error 已由页面回调提示，不再把它误报为断流。
        if (event.type === 'done' || event.type === 'error') return
      }
    }
  } finally {
    // 收到结束事件、读取失败或取消时均释放读取器。
    try {
      await reader.cancel()
    } catch {
      // 流已经因取消/出错关闭时 cancel 可能再拒绝一次，不要盖掉原始错误
    }
    reader.releaseLock()
  }
}

/**
 * 等下一块数据，但超过 idleMs 没有任何数据就当作卡死。
 * 取消时 read() 会以 AbortError 拒绝，由调用方处理。
 */
function readWithTimeout(reader, idleMs) {
  let timer
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(
      () => reject(new Error('长时间没有收到响应，请稍后重试')),
      idleMs
    )
  })
  return Promise.race([reader.read(), timeout]).finally(() => clearTimeout(timer))
}
