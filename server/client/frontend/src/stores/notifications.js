import { defineStore } from 'pinia'

let seq = 1

export const useNotifications = defineStore('notifications', {
  state: () => ({
    snacks: [],
    progress: { active: false },
  }),
  actions: {
    pushSnack(snack) {
      const s = { id: seq++, timeout: 3500, ...snack }
      this.snacks.push(s)
      return s.id
    },
    removeSnack(id) {
      this.snacks = this.snacks.filter(s => s.id !== id)
    },
    showProgress(p = {}) {
      this.progress = { active: true, indeterminate: true, ...p }
    },
    updateProgress(patch) {
      this.progress = { ...this.progress, ...patch }
    },
    hideProgress() {
      if (this.progress.onCancel) this.progress.onCancel = undefined
      this.progress = { active: false }
    },
  },
})
