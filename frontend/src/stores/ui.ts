import { reactive } from 'vue'

/** 全局 UI 状态（不持久化）：侧边栏在移动端作为抽屉的开关。 */
export const uiStore = reactive({
  sidebarOpen: false,
  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen
  },
  openSidebar() {
    this.sidebarOpen = true
  },
  closeSidebar() {
    this.sidebarOpen = false
  },
})
