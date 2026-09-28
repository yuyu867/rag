<template>
  <div :class="['message', role]">
    <div class="avatar">
      <el-avatar v-if="role === 'user'" :size="36" icon="UserFilled" />
      <el-avatar v-else :size="36" style="background-color: #67c23a">
        <span style="font-size:14px;color:#fff">营</span>
      </el-avatar>
    </div>
    <div class="content">
      <template v-for="(seg, i) in segments" :key="i">
        <div v-if="seg.type === 'table'" class="nutri-cards">
          <div v-for="(row, ri) in seg.rows" :key="ri" class="nutri-card">
            <div class="nutri-card-title">{{ row[0] }}</div>
            <div class="nutri-card-body">
              <div
                v-for="(h, hi) in seg.headers"
                :key="hi"
                v-show="hi > 0"
                class="nutri-item"
              >
                <span class="nutri-label">{{ h }}</span>
                <span class="nutri-value">{{ row[hi] ?? '—' }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text" v-html="renderText(seg.content)"></div>
      </template>
      <img v-if="imageUrl" :src="imageUrl" class="uploaded-image" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'

const props = defineProps<{
  role: 'user' | 'assistant'
  content: string
  imageUrl?: string
}>()

const md = new MarkdownIt({ breaks: true, linkify: true })

type Segment =
  | { type: 'text'; content: string }
  | { type: 'table'; headers: string[]; rows: string[][] }

function parseTable(buf: string[]): { headers: string[]; rows: string[][] } {
  const rows = buf
    .map((l) => l.trim())
    .filter((l) => l.startsWith('|') && l.endsWith('|'))
    .map((l) => l.slice(1, -1).split('|').map((c) => c.trim()))
  if (rows.length < 2) return { headers: [], rows: [] }
  const isSep = (r: string[]) =>
    r.every((c) => c === '' || /^:?-{2,}:?$/.test(c))
  const filtered = rows.filter((r) => !isSep(r))
  const headers = filtered[0] ?? []
  const data = filtered
    .slice(1)
    .filter((r) => r.length > 1 && r.some((c) => c !== ''))
    .map((r) => {
      while (r.length < headers.length) r.push('')
      return r
    })
  return { headers, rows: data }
}

/** 把消息内容拆成「普通文本 / Markdown 表格」两段，表格用于渲染成营养卡片。 */
function splitTables(content: string): Segment[] {
  const lines = content.split('\n')
  const segments: Segment[] = []
  let textBuf: string[] = []
  let tableBuf: string[] = []

  const flushText = () => {
    if (textBuf.length) {
      segments.push({ type: 'text', content: textBuf.join('\n') })
      textBuf = []
    }
  }
  const flushTable = () => {
    if (!tableBuf.length) return
    const { headers, rows } = parseTable(tableBuf)
    if (rows.length) {
      segments.push({ type: 'table', headers, rows })
    } else {
      textBuf.push(...tableBuf) // 不是有效表格，按普通文本处理
    }
    tableBuf = []
  }

  for (const line of lines) {
    if (line.trim().startsWith('|')) {
      flushText()
      tableBuf.push(line)
    } else {
      flushTable()
      textBuf.push(line)
    }
  }
  flushTable()
  flushText()
  return segments
}

const segments = computed<Segment[]>(() => {
  if (props.role !== 'assistant') {
    return [{ type: 'text', content: props.content }]
  }
  return splitTables(props.content)
})

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function renderText(content: string): string {
  return props.role === 'assistant' ? md.render(content) : escapeHtml(content)
}
</script>

<style scoped>
.message { display: flex; gap: 10px; margin-bottom: 20px; }
.message.user { flex-direction: row-reverse; }
.avatar { flex-shrink: 0; }
.content { max-width: 75%; min-width: 0; }
.text { padding: 10px 14px; border-radius: 12px; line-height: 1.6; }
.user .text { background: #409eff; color: #fff; }
.assistant .text { background: #f5f5f5; color: #333; }
.assistant .text :deep(p) { margin: 4px 0; }
.assistant .text :deep(ul), .assistant .text :deep(ol) { padding-left: 18px; }
.assistant .text :deep(table) { border-collapse: collapse; margin: 8px 0; }
.assistant .text :deep(td), .assistant .text :deep(th) {
  border: 1px solid #e0e0e0;
  padding: 6px 10px;
  font-size: 13px;
}

/* ===== 营养数据卡片 ===== */
.nutri-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: 12px;
  margin: 10px 0;
}
.nutri-card {
  background: #fff;
  border: 1px solid #e4e9e4;
  border-left: 4px solid #67c23a;
  border-radius: 10px;
  padding: 12px 14px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
}
.nutri-card-title {
  font-size: 15px;
  font-weight: bold;
  color: #2f3b31;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px dashed #e4e9e4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.nutri-card-body {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 14px;
}
.nutri-item {
  display: flex;
  flex-direction: column;
  min-width: 70px;
}
.nutri-label {
  font-size: 11px;
  color: #909399;
}
.nutri-value {
  font-size: 16px;
  font-weight: bold;
  color: #3a8c3f;
}
.uploaded-image { max-width: 200px; border-radius: 8px; margin-top: 6px; }

@media (max-width: 768px) {
  .content { max-width: 88%; }
  .nutri-cards { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); }
}
</style>
