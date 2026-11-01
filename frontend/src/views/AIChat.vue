<template>
  <div>
    <el-card>
      <template #header>
        <div style="font-size: 16px; font-weight: bold">
          <span>AI智能助手</span>
        </div>
      </template>

      <div
        ref="listRef"
        style="
          height: 480px;
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
    </el-card>
  </div>
</template>

<script setup>
import { chatStream } from '@/api/ai'
import { ref, reactive, onBeforeUnmount } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify' // 过滤危险的 HTML，防止 XSS 攻击
import { ElMessage } from 'element-plus'

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

const messages = ref([
  {
    role: 'assistant',
    content: GREETING,
    html: parseMarkdown(GREETING),
    steps: []
  }
])
const input = ref('')
const loading = ref(false)
const listRef = ref()
let controller = null

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

onBeforeUnmount(() => {
  controller?.abort()
})

const handleSend = async () => {
  const text = input.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text, html: parseMarkdown(text) })
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
  messages.value.push(assistant)
  scrollToBottom()

  const history = messages.value
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
        } else if (evt.type === 'tool_end') {
          const label = evt.label || evt.name || '工具'
          // ok 为 false 表示工具内部已失败（如预约冲突），
          // 模型随后还会解释原因，过程区先如实标出来
          const ok = evt.ok !== false
          assistant.status = ok ? `${label}完成` : `${label}失败`
          assistant.steps.push({ text: `${ok ? '完成' : '失败'}：${label}`, ok })
        } else if (evt.type === 'token') {
          assistant.content += evt.content || '' // 打字机：追加，不是覆盖
          assistant.status = '' // 开始出字后清掉「正在…」，避免叠在一起
        } else if (evt.type === 'done') {
          assistant.status = ''
          assistant.streaming = false
          // 注意：不要在这里再 append 一整段正文，否则会双份
        } else if (evt.type === 'error') {
          assistant.status = ''
          if (!assistant.content) {
            assistant.content = evt.message || '请求失败'
          }
          if (assistant.reserveTouched) {
            assistant.content += `\n\n（${RESERVE_HINT}）`
          }
          ElMessage.error(evt.message || '请求失败')
        }
        scrollToBottom()
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
    scrollToBottom()
  }
}
</script>
