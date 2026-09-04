<template>
  <div class="image-upload">
    <input ref="fileInput" type="file" accept="image/*" @change="handleFile" style="display:none" />
    <el-button :icon="PictureFilled" circle @click="fileInput?.click()" title="上传食物图片" />
    <div v-if="preview" class="preview">
      <img :src="preview" />
      <el-button :icon="Close" circle size="small" @click="clearImage" class="remove-btn" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { PictureFilled, Close } from '@element-plus/icons-vue'

const emit = defineEmits<{ (e: 'image', base64: string): void; (e: 'clear'): void }>()

const fileInput = ref<HTMLInputElement>()
const preview = ref<string>()

async function handleFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => {
    const base64 = (ev.target?.result as string).split(',')[1]
    preview.value = ev.target?.result as string
    emit('image', base64)
  }
  reader.readAsDataURL(file)
}

function clearImage() {
  preview.value = undefined
  emit('clear')
}
</script>

<style scoped>
.image-upload { display: flex; align-items: center; gap: 8px; }
.preview { position: relative; display: inline-block; }
.preview img { max-height: 80px; border-radius: 8px; }
.remove-btn { position: absolute; top: -8px; right: -8px; }
</style>
