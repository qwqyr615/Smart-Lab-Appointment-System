// AI 对话缓存：按用户把多会话存进 localStorage
// 只负责读写和结构校验，不掺任何渲染逻辑（html 由页面重建）

const KEY_PREFIX = 'ai_chat_cache_'
const VERSION = 1
// 会话条数上限：超出后淘汰最久没更新的，避免 localStorage 被撑满
export const MAX_CONVERSATIONS = 20
const TITLE_MAX = 20
const ROLES = ['user', 'assistant']

function storageKey(userId) {
  return `${KEY_PREFIX}${userId ?? 'anon'}`
}

// ok 是三态：true 成功、false 失败、缺省表示还没结果，不能一律当成功
function normalizeSteps(steps) {
  if (!Array.isArray(steps)) return []
  return steps
    .filter((step) => step && typeof step.text === 'string')
    .map((step) => {
      const item = { text: step.text }
      if (step.ok === false) item.ok = false
      else if (step.ok === true) item.ok = true
      return item
    })
}

/**
 * 把页面上的消息压成可落盘的形状：丢掉 html / streaming / status 这些临时字段，
 * 也丢掉流式中断留下的空助手壳，否则刷新后会多出一条空白气泡。
 */
export function toStorageMessages(messages) {
  if (!Array.isArray(messages)) return []
  return messages
    .filter((item) => item && ROLES.includes(item.role) && typeof item.content === 'string')
    .filter((item) => item.role === 'user' || item.content.trim())
    .map((item) => ({
      role: item.role,
      content: item.content,
      steps: normalizeSteps(item.steps)
    }))
}

// 会话标题取第一个提问，没有就返回 fallback（让调用方决定是否显示「新对话」）
export function deriveTitle(messages, fallback = '新对话') {
  if (!Array.isArray(messages)) return fallback
  const first = messages.find((item) => item.role === 'user' && item.content?.trim())
  if (!first) return fallback
  const text = first.content.replace(/\s+/g, ' ').trim()
  return text.length > TITLE_MAX ? `${text.slice(0, TITLE_MAX)}…` : text
}

export function createConversation(greeting) {
  const now = Date.now()
  return {
    // 时间戳 + 随机串：同一毫秒连续新建也不会撞 id
    id: `c_${now}_${Math.random().toString(36).slice(2, 6)}`,
    title: '',
    createdAt: now,
    updatedAt: now,
    messages: greeting ? [{ role: 'assistant', content: greeting, steps: [] }] : []
  }
}

// 读回来的数据一律当不可信：手工改过 localStorage 也不能让页面崩
function normalizeConversation(item) {
  if (!item || typeof item.id !== 'string' || !item.id) return null
  if (!Array.isArray(item.messages)) return null

  const messages = item.messages
    .filter((msg) => msg && ROLES.includes(msg.role) && typeof msg.content === 'string')
    .filter((msg) => msg.role === 'user' || msg.content.trim())
    .map((msg) => ({
      role: msg.role,
      content: msg.content,
      steps: normalizeSteps(msg.steps)
    }))
  if (!messages.length) return null

  const createdAt = Number(item.createdAt) || Date.now()
  return {
    id: item.id,
    title: typeof item.title === 'string' ? item.title : '',
    createdAt,
    updatedAt: Number(item.updatedAt) || createdAt,
    messages
  }
}

export function loadChatCache(userId) {
  const empty = { version: VERSION, activeId: '', conversations: [] }
  let raw = null
  try {
    raw = localStorage.getItem(storageKey(userId))
  } catch {
    return empty
  }
  if (!raw) return empty

  let data = null
  try {
    data = JSON.parse(raw)
  } catch {
    return empty
  }
  // 结构版本变了就整体丢弃，不做逐版本迁移
  if (!data || data.version !== VERSION || !Array.isArray(data.conversations)) return empty

  const conversations = []
  for (const item of data.conversations) {
    const conv = normalizeConversation(item)
    if (!conv) continue
    // 从没问过问题的会话没有恢复价值，但当前正在编辑的那条要留着
    const hasUserMessage = conv.messages.some((msg) => msg.role === 'user')
    if (!hasUserMessage && conv.id !== data.activeId) continue
    conversations.push(conv)
    if (conversations.length >= MAX_CONVERSATIONS) break
  }
  if (!conversations.length) return empty

  const activeId = conversations.some((conv) => conv.id === data.activeId)
    ? data.activeId
    : conversations[0].id
  return { version: VERSION, activeId, conversations }
}

/**
 * 写盘。配额不足时从最久没更新的非当前会话开始淘汰后重试，
 * 返回 false 表示彻底存不下了，由调用方提示一次。
 */
export function saveChatCache(userId, state) {
  const key = storageKey(userId)
  let attempt = [...(state.conversations || [])]
    .sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0))
    .slice(0, MAX_CONVERSATIONS)

  for (;;) {
    try {
      const payload = {
        version: VERSION,
        activeId: state.activeId,
        conversations: attempt
      }
      localStorage.setItem(key, JSON.stringify(payload))
      return true
    } catch {
      // 每轮至少删一条，循环一定收敛
      let oldestIndex = -1
      for (let i = 0; i < attempt.length; i++) {
        if (attempt[i].id === state.activeId) continue
        if (oldestIndex === -1 || (attempt[i].updatedAt || 0) < (attempt[oldestIndex].updatedAt || 0)) {
          oldestIndex = i
        }
      }
      if (oldestIndex === -1) return false
      attempt = attempt.filter((_, i) => i !== oldestIndex)
    }
  }
}
