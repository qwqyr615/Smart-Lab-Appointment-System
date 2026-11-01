<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span style="font-size: 16px; font-weight: bold">AI智能助手</span>
          <el-button size="small" @click="handleNewConversation">
            <el-icon style="margin-right: 4px"><Plus /></el-icon>
            新建对话
          </el-button>
        </div>
      </template>

      <div style="display: flex; height: 560px; gap: 12px">
        <!-- 会话列表：按最近更新时间倒序 -->
        <div
          style="
            width: 180px;
            flex-shrink: 0;
            overflow-y: auto;
            border-right: 1px solid #eee;
            padding-right: 8px;
          "
        >
          <div
            v-for="conv in sortedConversations"
            :key="conv.id"
            class="conv-item"
            :class="{ 'conv-item--active': conv.id === activeId }"
            @click="switchConversation(conv.id)"
          >
            <span class="conv-item__title">{{ conv.title || '新对话' }}</span>
            <el-icon class="conv-item__delete" @click.stop="handleRemoveConversation(conv.id)">
              <Delete />
            </el-icon>
          </div>
        </div>

        <!-- 对话区 -->
        <div style="flex: 1; min-width: 0; display: flex; flex-direction: column">
          <div
            ref="listRef"
            style="
              flex: 1;
              overflow-y: auto;
              padding: 8px 4px;
              background-color: #fafafa;
              border-radius: 6px;
            "
          >
            <div
              v-for="(item, index) in messages"
              :key="index"
              :style="{
                display: 'flex',
                justifyContent: item.role === 'user' ? 'flex-end' : 'flex-start',
                marginBottom: '12px'
              }"
            >
              <div
                :style="{
                  maxWidth: '70%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  backgroundColor: item.role === 'user' ? '#409eff' : '#fff',
                  color: item.role === 'user' ? '#fff' : '#333',
                  lineHeight: '1.6',
                  boxShadow: '0 1px 2px rgba(0, 0, 0, 0.06)'
                }"
              >
                <div
                  v-if="item.role === 'assistant' && item.status"
                  style="margin-bottom: 6px; font-size: 12px; color: #909399"
                >
                  {{ item.status }}
                </div>

                <div
                  v-if="item.role === 'assistant' && item.steps?.length"
                  style="margin-bottom: 8px; font-size: 12px; color: #909399; line-height: 1.5"
                >
                  <div
                    v-for="(step, i) in item.steps"
                    :key="i"
                    :style="step.ok === false ? 'color: #f56c6c' : ''"
                  >
                    · {{ step.text }}
                  </div>
                </div>

                <!-- 流式期间先按纯文本显示，结束后再统一渲染 Markdown，避免每个 token 全量重解析 -->
                <div v-if="item.streaming" style="white-space: pre-wrap">{{ item.content }}</div>
                <div v-else v-html="item.html"></div>
              </div>
            </div>
          </div>

          <div style="margin-top: 12px; display: flex; gap: 8px; align-items: flex-end">
            <el-input
              ref="inputRef"
              v-model="input"
              type="textarea"
              :rows="2"
              placeholder="问问实验室怎么预约、开放时间..."
              @keydown.enter.exact.prevent="handleSend"
              @keydown.enter.shift.stop
            ></el-input>
            <el-button
              :type="loading ? 'danger' : 'primary'"
              @click="loading ? stopStream() : handleSend()"
            >
              {{ loading ? '停止' : '发送' }}
            </el-button>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { chatStream } from '@/api/ai'
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify' // 过滤危险的 HTML，防止 XSS 攻击
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import { useUser } from '@/utils/user'
import {
  MAX_CONVERSATIONS,
  createConversation,
  deriveTitle,
  loadChatCache,
  saveChatCache,
  toStorageMessages
} from '@/utils/chatCache'

// 将 markdown 字符串转换为安全的 HTML 字符串
function parseMarkdown(text) {
  if (!text) return ''
  marked.setOptions({ breaks: true }) // 把 \n 转换成 <br>
  // 使用 marked 解析，然后用 DOMPurify 清理
  const rawHtml = marked.parse(text)
  return DOMPurify.sanitize(rawHtml)
}

const GREETING =
  '你好，我是实验室预约助手。可以问规则和开放实验室，也可以说「帮我预约明天下午的实验室」，确认后我会帮你提交。'

// 工具跑在线程池里，中断/出错时预约可能已经落库，提示用户去核对
const RESERVE_HINT = '预约提交可能已经生效，请到「我的预约」核实'

// 流式过程中每 500ms 落盘一次：刷新最多丢半秒的字
const PERSIST_INTERVAL = 500

const { userInfo } = useUser()
// 缓存按用户隔离，换账号登录不会串对话
const userId = computed(() => userInfo.value?.id ?? 'anon')

const conversations = ref([]) // 列表快照（含已落盘的消息）
const activeId = ref('')
const messages = ref([]) // 当前会话的"活"消息，带 html / streaming
const input = ref('')
const loading = ref(false)
const listRef = ref()
const inputRef = ref()
let controller = null

const sortedConversations = computed(() =>
  [...conversations.value].sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0))
)

const findConversation = (id) => conversations.value.find((conv) => conv.id === id)

function greetingMessage() {
  return { role: 'assistant', content: GREETING, html: parseMarkdown(GREETING), steps: [] }
}

// 缓存里只有 role/content/steps，渲染用的字段在这里补齐
function hydrate(rawMessages) {
  const list = Array.isArray(rawMessages) ? rawMessages : []
  const hydrated = list
    .filter((item) => item && (item.role === 'user' || item.role === 'assistant'))
    .map((item) => {
      const content = item.content || ''
      return {
        role: item.role,
        content,
        html: parseMarkdown(content),
        status: '',
        steps: Array.isArray(item.steps) ? item.steps.map((s) => ({ text: s.text, ok: s.ok })) : [],
        streaming: false
      }
    })
  return hydrated.length ? hydrated : [greetingMessage()]
}

// 每个 token 都会触发滚动，用 rAF 合并成每帧一次
let scrollScheduled = false
const scrollToBottom = () => {
  if (scrollScheduled) return
  scrollScheduled = true
  requestAnimationFrame(() => {
    scrollScheduled = false
    const elem = listRef.value
    if (elem) elem.scrollTop = elem.scrollHeight
  })
}

const stopStream = () => {
  controller?.abort()
}

/* ---------------- 持久化 ---------------- */

let persistTimer = null
let quotaWarned = false

function clearPersistTimer() {
  if (persistTimer) {
    clearTimeout(persistTimer)
    persistTimer = null
  }
}

/**
 * 立即写盘。convId / msgs 必须是调用方捕获的那一份，
 * 流式过程中切走会话时也能写回它自己的位置。
 */
function persistNow(convId = activeId.value, msgs = messages.value) {
  clearPersistTimer()
  const conv = findConversation(convId)
  if (!conv) return // 会话已被删除

  conv.messages = toStorageMessages(msgs)
  if (!conv.title) {
    const title = deriveTitle(conv.messages, '')
    if (title) conv.title = title
  }
  conv.updatedAt = Date.now()

  const ok = saveChatCache(userId.value, {
    activeId: activeId.value,
    conversations: conversations.value
  })
  if (!ok && !quotaWarned) {
    quotaWarned = true
    ElMessage.warning('本地对话缓存已满，较早的对话可能无法继续保存')
  }
}

// 尾随节流：流式期间不用每个 token 都写 localStorage
function schedulePersist(convId, msgs) {
  if (persistTimer) return
  persistTimer = setTimeout(() => {
    persistTimer = null
    persistNow(convId, msgs)
  }, PERSIST_INTERVAL)
}

// 刷新页面不会触发组件卸载，只能在 beforeunload 里补最后一次
const handleBeforeUnload = () => persistNow(activeId.value, messages.value)

/* ---------------- 会话切换 ---------------- */

function activate(conv) {
  activeId.value = conv.id
  messages.value = hydrate(conv.messages)
  nextTick(scrollToBottom)
}

function switchConversation(id) {
  if (id === activeId.value) return
  const target = findConversation(id)
  if (!target) return
  // 先停掉正在跑的流，再把半截回答落盘，最后才切
  if (loading.value) controller?.abort()
  persistNow(activeId.value, messages.value)
  activate(target)
}

// 只保留最近的若干条，优先淘汰最久没更新且不是当前会话的
function pruneConversations(keepId) {
  if (conversations.value.length <= MAX_CONVERSATIONS) return
  const keep = findConversation(keepId)
  const rest = conversations.value
    .filter((conv) => conv.id !== keepId)
    .sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0))
  conversations.value = [keep, ...rest].slice(0, MAX_CONVERSATIONS).filter(Boolean)
}

function handleNewConversation() {
  // 当前会话还没聊过就别再开一条，否则列表里全是「新对话」
  if (!messages.value.some((item) => item.role === 'user')) {
    ElMessage.info('当前已经是新对话了')
    nextTick(() => inputRef.value?.focus())
    return
  }
  if (loading.value) controller?.abort()
  persistNow(activeId.value, messages.value)

  const conv = createConversation(GREETING)
  conversations.value = [conv, ...conversations.value]
  pruneConversations(conv.id)
  activate(conv)
  // 立刻记下 activeId，刷新后还能回到这条新对话
  persistNow(conv.id, messages.value)
  nextTick(() => inputRef.value?.focus())
}

async function handleRemoveConversation(id) {
  const conv = findConversation(id)
  if (!conv) return
  try {
    await ElMessageBox.confirm(`确定删除「${conv.title || '新对话'}」吗？`, '删除对话', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
  } catch {
    return // 用户取消
  }

  const isActive = id === activeId.value
  const index = conversations.value.findIndex((item) => item.id === id)
  if (isActive && loading.value) controller?.abort()

  conversations.value = conversations.value.filter((item) => item.id !== id)

  if (isActive) {
    // 删的是当前会话：落到相邻一条，全删光了就补一条空的
    const next = conversations.value[index] || conversations.value[index - 1]
    if (next) {
      activate(next)
    } else {
      const fresh = createConversation(GREETING)
      conversations.value = [fresh]
      activate(fresh)
    }
  }

  clearPersistTimer()
  persistNow(activeId.value, messages.value)
}

/* ---------------- 发送 ---------------- */

const handleSend = async () => {
  const text = input.value.trim()
  if (!text || loading.value) return

  // 捕获当前会话：流式过程中即使被切走，也写回它自己的位置
  const convId = activeId.value
  const ownMessages = messages.value

  ownMessages.push({ role: 'user', content: text, html: parseMarkdown(text) })
  input.value = ''
  loading.value = true

  // 必须用 reactive：普通对象 push 后再改字段，视图可能不更新
  const assistant = reactive({
    role: 'assistant',
    content: '', // 正文：靠 token 一点点拼
    html: '', // 结束后才生成的 Markdown，history 不带它
    status: '正在思考…', // 当前状态文案
    steps: [], // 过程流水，不进下次 history
    streaming: true, // true 时按纯文本渲染
    reserveTouched: false // 提交预约的工具有没有跑过，中断时用来提示核对
  })
  ownMessages.push(assistant)
  scrollToBottom()
  // 提问先落盘：此时刷新，问题不会丢
  persistNow(convId, ownMessages)

  const history = ownMessages
    .filter((item) => item.role === 'user' || item.role === 'assistant')
    .slice(0, -1) // 去掉刚插入的空助手，避免把空 content 送回去
    // 只保留 role/content；status、steps、html 丢掉
    .map(({ role, content }) => ({ role, content }))

  controller = new AbortController()
  try {
    // 第二个参数是回调：每解析出一条 SSE 事件就进一次
    await chatStream(
      { messages: history },
      (evt) => {
        if (evt.type === 'status') {
          assistant.status = evt.message || '正在思考…'
        } else if (evt.type === 'tool_start') {
          const label = evt.label || evt.name || '工具'
          assistant.status = `正在${label}…`
          assistant.steps.push({ text: `开始：${label}` })
          if (evt.name === 'create_lab_reservation') {
            assistant.reserveTouched = true
          }
          schedulePersist(convId, ownMessages)
        } else if (evt.type === 'tool_end') {
          const label = evt.label || evt.name || '工具'
          // ok 为 false 表示工具内部已失败（如预约冲突），
          // 模型随后还会解释原因，过程区先如实标出来
          const ok = evt.ok !== false
          assistant.status = ok ? `${label}完成` : `${label}失败`
          assistant.steps.push({ text: `${ok ? '完成' : '失败'}：${label}`, ok })
          schedulePersist(convId, ownMessages)
        } else if (evt.type === 'token') {
          assistant.content += evt.content || '' // 打字机：追加，不是覆盖
          assistant.status = '' // 开始出字后清掉「正在…」，避免叠在一起
          schedulePersist(convId, ownMessages)
        } else if (evt.type === 'done') {
          assistant.status = ''
          assistant.streaming = false
          // 注意：不要在这里再 append 一整段正文，否则会双份
          persistNow(convId, ownMessages)
        } else if (evt.type === 'error') {
          assistant.status = ''
          if (!assistant.content) {
            assistant.content = evt.message || '请求失败'
          }
          if (assistant.reserveTouched) {
            assistant.content += `\n\n（${RESERVE_HINT}）`
          }
          ElMessage.error(evt.message || '请求失败')
          persistNow(convId, ownMessages)
        }
        // 会话已经切走的话，别去滚动画面上另一条对话
        if (activeId.value === convId) scrollToBottom()
      },
      { signal: controller.signal }
    )
  } catch (err) {
    assistant.status = ''
    if (err.name === 'AbortError') {
      // 用户主动停止：保留已经生成的部分，不当成错误弹窗
      if (!assistant.content) assistant.content = '已停止生成'
      if (assistant.reserveTouched) {
        assistant.content += `\n\n（${RESERVE_HINT}）`
      }
    } else {
      if (!assistant.content) {
        assistant.content = err.message || '网络异常'
      }
      ElMessage.error(err.message || '网络异常')
    }
  } finally {
    loading.value = false
    controller = null
    assistant.status = ''
    assistant.streaming = false
    assistant.html = parseMarkdown(assistant.content)
    if (activeId.value === convId) scrollToBottom()
    // 收尾一定再落一次盘，把 status/steps 的最终状态写实
    persistNow(convId, ownMessages)
  }
}

/* ---------------- 生命周期 ---------------- */

onMounted(() => {
  const cache = loadChatCache(userId.value)
  conversations.value = cache.conversations

  if (!conversations.value.length) {
    const conv = createConversation(GREETING)
    conversations.value = [conv]
    activate(conv)
  } else {
    activate(findConversation(cache.activeId) || conversations.value[0])
  }

  window.addEventListener('beforeunload', handleBeforeUnload)
})

onBeforeUnmount(() => {
  controller?.abort()
  window.removeEventListener('beforeunload', handleBeforeUnload)
  // 切页也要留档：缓存正是为了回来还在
  persistNow(activeId.value, messages.value)
})
</script>

<style scoped>
.conv-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 10px;
  margin-bottom: 4px;
  border-radius: 6px;
  font-size: 13px;
  color: #606266;
  cursor: pointer;
  transition: background-color 0.2s;
}

.conv-item:hover {
  background-color: #f5f7fa;
}

.conv-item--active {
  background-color: #ecf5ff;
  color: #409eff;
  font-weight: 600;
}

.conv-item__title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-item__delete {
  flex-shrink: 0;
  visibility: hidden;
}

.conv-item:hover .conv-item__delete {
  visibility: visible;
}
</style>
