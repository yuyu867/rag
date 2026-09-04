<template>
  <div :class="['message', role]">
    <div class="avatar">
      <el-avatar v-if="role === 'user'" :size="36" icon="UserFilled" />
      <el-avatar v-else :size="36" style="background-color: #67c23a">
        <span style="font-size:14px;color:#fff">营</span>
      </el-avatar>
    </div>
    <div class="content">
      <div class="text" v-html="renderedContent"></div>
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

const md = new MarkdownIt({ breaks: true })

const renderedContent = computed(() => {
  if (props.role === 'assistant') {
    return md.render(props.content)
  }
  return props.content
})
</script>

<style scoped>
.message { display: flex; gap: 10px; margin-bottom: 20px; }
.message.user { flex-direction: row-reverse; }
.avatar { flex-shrink: 0; }
.content { max-width: 75%; }
.text { padding: 10px 14px; border-radius: 12px; line-height: 1.6; }
.user .text { background: #409eff; color: #fff; }
.assistant .text { background: #f5f5f5; color: #333; }
.assistant .text :deep(p) { margin: 4px 0; }
.assistant .text :deep(ul) { padding-left: 18px; }
.uploaded-image { max-width: 200px; border-radius: 8px; margin-top: 6px; }
</style>
