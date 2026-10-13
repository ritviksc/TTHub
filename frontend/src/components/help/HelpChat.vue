<script setup>
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'
import { streamHelp } from '@/apis.js'
import { auth } from '@/stores/auth.js'
import { MAX_QUESTION, chatHistory, helpError, messageTime, stripCitations } from '@/utils/help.js'
import MarkdownResponse from '@/components/MarkdownResponse.vue'
import logoMark from '@/assets/logo-mark.png'

const emit = defineEmits(['open'])

// Give up if nothing arrives for this long (matches the backend's LLM timeout).
const IDLE_TIMEOUT_MS = 200000
const ROLE_LABELS = { super_admin: 'Super Admin', branch_manager: 'Branch Manager', instructor: 'Kaimahi' }

// Messages: { id, role: 'user' | 'assistant', content, time, status, sources, omit }.
// status (assistant): 'waiting' → 'streaming' → 'done' | 'stopped' | 'error'.
// omit keeps unfinished turns out of the history sent with the next question.
const messages = ref([])
const draft = ref('')
const busy = ref(false)
const log = ref(null)
const input = ref(null)
const atBottom = ref(true)
const copiedId = ref(null)
let controller = null
let nextId = 1

const firstName = computed(() => auth.user?.first_name?.trim())
const roleLabel = computed(() => ROLE_LABELS[auth.user?.role] ?? 'staff member')
const nearLimit = computed(() => draft.value.length > MAX_QUESTION - 100)

onBeforeUnmount(() => controller?.abort())

/* ---- scrolling: follow the answer unless the reader has scrolled up ---- */
function onScroll() {
  const el = log.value
  atBottom.value = !el || el.scrollHeight - el.scrollTop - el.clientHeight < 48
}
async function follow(force = false) {
  await nextTick()
  if (log.value && (force || atBottom.value)) {
    log.value.scrollTo({ top: log.value.scrollHeight, behavior: force ? 'smooth' : 'auto' })
    atBottom.value = true
  }
}

/* ---- composer ---- */
function grow() {
  const el = input.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 150)}px`
}
function onKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault()
    send()
  }
}

/* ---- asking ---- */
async function ask(text) {
  const history = chatHistory(messages.value)
  const question = { id: nextId++, role: 'user', content: text, time: new Date() }
  const reply = { id: nextId++, role: 'assistant', content: '', time: new Date(), status: 'waiting', sources: [] }
  messages.value.push(question, reply)
  // Work on the reactive copy so streamed text re-renders.
  const answer = messages.value[messages.value.length - 1]
  busy.value = true
  follow(true)

  controller = new AbortController()
  const ownController = controller
  let timedOut = false
  let idle
  const resetIdle = () => {
    clearTimeout(idle)
    idle = setTimeout(() => { timedOut = true; ownController.abort() }, IDLE_TIMEOUT_MS)
  }
  resetIdle()

  try {
    await streamHelp(text, history, {
      signal: ownController.signal,
      onEvent(event) {
        resetIdle()
        if (event.type === 'delta') {
          answer.status = 'streaming'
          answer.content += event.text
        } else if (event.type === 'done') {
          answer.status = 'done'
          answer.sources = event.sources ?? []
        } else if (event.type === 'error') {
          answer.status = 'error'
          answer.error = event.detail
        }
        follow()
      },
    })
    if (answer.status === 'waiting' || answer.status === 'streaming') {
      answer.status = 'error'
      answer.error = 'The answer ended unexpectedly. Please try again.'
    }
  } catch (error) {
    if (ownController.signal.aborted && !timedOut) {
      answer.status = 'stopped'
    } else {
      answer.status = 'error'
      answer.error = helpError(timedOut ? { code: 'ETIMEDOUT' } : error)
    }
  } finally {
    clearTimeout(idle)
    answer.time = new Date()
    if (answer.status !== 'done') {
      question.omit = true
      answer.omit = true
    }
    if (controller === ownController) controller = null
    busy.value = false
    follow()
  }
}

function send() {
  const text = draft.value.trim()
  if (!text || busy.value) return
  draft.value = ''
  nextTick(grow)
  ask(text)
}

function stop() {
  controller?.abort()
}

// Ask the same question again, replacing the failed attempt.
function retry(message) {
  if (busy.value) return
  const index = messages.value.indexOf(message)
  const question = messages.value[index - 1]
  messages.value.splice(index - 1, 2)
  ask(question.content)
}

function newChat() {
  controller?.abort()
  messages.value = []
  draft.value = ''
  nextTick(() => { grow(); input.value?.focus() })
}

async function copy(message) {
  try {
    await navigator.clipboard.writeText(stripCitations(message.content).trim())
    copiedId.value = message.id
    setTimeout(() => { if (copiedId.value === message.id) copiedId.value = null }, 1500)
  } catch {
    // Clipboard access can be refused; the text is still selectable.
  }
}
</script>

<template>
  <section class="help-panel chat" aria-labelledby="help-chat-title">
    <header class="panel-head chat-head">
      <img :src="logoMark" alt="" class="bot-avatar large" />
      <div class="chat-title">
        <h2 id="help-chat-title">Help assistant</h2>
        <p>Answers from the help docs only</p>
      </div>
      <button type="button" class="new-chat" :disabled="!messages.length" @click="newChat">New chat</button>
    </header>

    <div ref="log" class="panel-body chat-log" @scroll="onScroll">
      <div class="message assistant welcome">
        <img :src="logoMark" alt="" class="bot-avatar" />
        <div class="bubble">
          <p>Kia ora{{ firstName ? `, ${firstName}` : '' }}! I can answer questions about using the app as a {{ roleLabel }}.</p>
          <p>I only use the documentation on the left, so I can't see or change any records.</p>
        </div>
      </div>

      <div v-for="message in messages" :key="message.id" :class="['message', message.role, message.status]">
        <img v-if="message.role === 'assistant'" :src="logoMark" alt="" class="bot-avatar" />
        <div class="message-main">
          <div class="bubble">
            <p v-if="message.role === 'user'" class="plain">{{ message.content }}</p>
            <template v-else>
              <span v-if="message.status === 'waiting'" class="typing" role="status" aria-label="The help assistant is answering">
                <span></span><span></span><span></span>
              </span>
              <MarkdownResponse v-if="message.content"
                                :text="stripCitations(message.content, { streaming: message.status === 'streaming' })" />
              <span v-if="message.status === 'streaming'" class="caret" aria-hidden="true"></span>
              <p v-if="message.status === 'stopped'" class="note">Stopped.</p>
              <p v-if="message.status === 'error'" class="note error" role="alert">{{ message.error }}</p>
            </template>
          </div>

          <div v-if="message.role === 'assistant' && message.sources?.length" class="sources">
            <span class="sources-label">Sources</span>
            <button v-for="source in message.sources" :key="source.slug" type="button" class="source-chip"
                    @click="emit('open', source.slug)">📄 {{ source.title }}</button>
          </div>

          <div class="meta">
            <time>{{ messageTime(message.time) }}</time>
            <template v-if="message.role === 'assistant'">
              <button v-if="message.status === 'done' && message.content" type="button" class="meta-action" @click="copy(message)">
                {{ copiedId === message.id ? 'Copied' : 'Copy' }}
              </button>
              <button v-if="message.status === 'error' || message.status === 'stopped'" type="button" class="meta-action"
                      :disabled="busy" @click="retry(message)">Retry</button>
            </template>
          </div>
        </div>
      </div>
    </div>

    <button v-if="!atBottom && messages.length" type="button" class="jump" @click="follow(true)">↓ Jump to latest</button>

    <form class="panel-foot composer" @submit.prevent="send">
      <div class="input-row">
        <label for="help-question" class="visually-hidden">Your question</label>
        <textarea id="help-question" ref="input" v-model="draft" rows="1" :maxlength="MAX_QUESTION"
                  placeholder="Ask how to do something…" @input="grow" @keydown="onKeydown"></textarea>
        <button v-if="busy" type="button" class="send stop" aria-label="Stop answering" @click="stop">■</button>
        <button v-else type="submit" class="send" aria-label="Send question" :disabled="!draft.trim()">↑</button>
      </div>
      <div class="hint">
        <span>Enter to send · Shift+Enter for a new line</span>
        <span v-if="nearLimit" :class="{ over: draft.length >= MAX_QUESTION }">{{ draft.length }}/{{ MAX_QUESTION }}</span>
      </div>
    </form>
  </section>
</template>

<style scoped>
.chat { position: relative; }
.chat-head { display: flex; align-items: center; gap: 12px; padding: 14px 20px; border-bottom: 1px solid var(--border); }
.chat-title { flex: 1; min-width: 0; }
.chat-title h2 { margin: 0; font-size: var(--text-lg); }
.chat-title p { margin: 2px 0 0; color: var(--text-muted); font-size: var(--text-sm); }
.new-chat {
  background: none; border: 1px solid var(--border-strong); border-radius: var(--radius-pill);
  color: var(--text); cursor: pointer; font: inherit; font-size: var(--text-sm); padding: 5px 14px;
}
.new-chat:hover:not(:disabled) { background: var(--surface-sunken); }
.new-chat:disabled { opacity: 0.45; cursor: default; }

.bot-avatar {
  flex: 0 0 28px; width: 28px; height: 28px; border-radius: 50%; object-fit: contain;
  background: var(--ink); padding: 4px; box-sizing: border-box;
}
.bot-avatar.large { flex-basis: 38px; width: 38px; height: 38px; padding: 6px; }

.chat-log { flex: 1; min-height: 0; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 18px; }
.message { display: flex; gap: 10px; align-items: flex-start; max-width: 100%; }
.message-main { display: flex; flex-direction: column; gap: 6px; min-width: 0; max-width: calc(100% - 38px); }
.message.user { justify-content: flex-end; }
.message.user .message-main { align-items: flex-end; max-width: 85%; }
.bubble { border-radius: 16px; padding: 10px 14px; overflow-wrap: anywhere; font-size: var(--text-base); line-height: 1.55; }
.message.user .bubble { background: var(--teal); color: var(--text-on-ink); border-bottom-right-radius: 4px; }
.message.assistant .bubble { background: var(--surface-sunken); color: var(--text); border-bottom-left-radius: 4px; }
.welcome .bubble p { margin: 0; }
.welcome .bubble p + p { margin-top: 6px; color: var(--text-secondary); }
.plain { margin: 0; white-space: pre-wrap; }
.bubble :deep(.markdown-response) { color: var(--text); font-size: var(--text-base); }
.bubble :deep(.markdown-response > :first-child) { margin-top: 0; }
.bubble :deep(.markdown-response > :last-child) { margin-bottom: 0; }
.bubble :deep(.markdown-response h1),
.bubble :deep(.markdown-response h2),
.bubble :deep(.markdown-response h3) { font-size: var(--text-md); margin: 12px 0 6px; }
.note { margin: 6px 0 0; color: var(--text-muted); font-size: var(--text-sm); }
.note.error { color: var(--danger); }
.message.error .bubble { background: var(--danger-bg); }

.typing { display: inline-flex; gap: 4px; padding: 4px 0; }
.typing span { width: 7px; height: 7px; border-radius: 50%; background: var(--text-muted); animation: bounce 1.2s infinite ease-in-out; }
.typing span:nth-child(2) { animation-delay: 0.15s; }
.typing span:nth-child(3) { animation-delay: 0.3s; }
@keyframes bounce { 0%, 60%, 100% { transform: translateY(0); opacity: 0.5; } 30% { transform: translateY(-4px); opacity: 1; } }
.caret { display: inline-block; width: 7px; height: 15px; margin-left: 2px; vertical-align: text-bottom; background: var(--teal); animation: blink 1s steps(1) infinite; }
@keyframes blink { 50% { opacity: 0; } }

.sources { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.sources-label { color: var(--text-muted); font-size: var(--text-xs); text-transform: uppercase; letter-spacing: 0.04em; }
.source-chip {
  border: 1px solid var(--border-strong); border-radius: var(--radius-pill); background: var(--surface);
  color: var(--teal-dark); cursor: pointer; font: inherit; font-size: var(--text-sm); padding: 3px 10px;
}
.source-chip:hover { border-color: var(--teal); background: var(--teal-tint); }
.meta { display: flex; gap: 10px; align-items: center; color: var(--text-faint); font-size: var(--text-xs); }
.meta-action { background: none; border: none; color: var(--text-muted); cursor: pointer; font: inherit; padding: 0; }
.meta-action:hover:not(:disabled) { color: var(--teal-dark); text-decoration: underline; }

.jump {
  position: absolute; left: 50%; bottom: 112px; transform: translateX(-50%);
  background: var(--ink); color: var(--text-on-ink); border: none; border-radius: var(--radius-pill);
  box-shadow: var(--shadow-panel); cursor: pointer; font: inherit; font-size: var(--text-sm); padding: 6px 14px;
}

.composer { padding: 12px 16px 14px; border-top: 1px solid var(--border); }
.input-row {
  display: flex; align-items: flex-end; gap: 8px; border: 1px solid var(--border-strong);
  border-radius: 14px; background: var(--surface); padding: 6px 6px 6px 12px;
}
.input-row:focus-within { border-color: var(--teal); box-shadow: 0 0 0 3px var(--teal-tint); }
.input-row textarea {
  flex: 1; border: none; outline: none; resize: none; font: inherit; font-size: var(--text-base);
  line-height: 1.45; padding: 6px 0; max-height: 150px; background: transparent;
}
.send {
  flex: 0 0 34px; width: 34px; height: 34px; border-radius: 50%; border: none; cursor: pointer;
  background: var(--maroon); color: #fff; font-size: 16px; font-weight: 700;
}
.send:hover:not(:disabled) { background: var(--maroon-dark); }
.send:disabled { background: var(--border-strong); cursor: default; }
.send.stop { background: var(--ink); font-size: 12px; }
.hint { display: flex; justify-content: space-between; margin-top: 6px; color: var(--text-faint); font-size: var(--text-xs); }
.hint .over { color: var(--danger); }
.visually-hidden { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

@media (prefers-reduced-motion: reduce) {
  .typing span, .caret { animation: none; }
}
</style>
