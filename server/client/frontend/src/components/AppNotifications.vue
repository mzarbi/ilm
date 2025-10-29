<template>
  <!-- Snack queue -->
  <div class="snacks">
    <v-snackbar
      v-for="s in snacks"
      :key="s.id"
      v-model="visible[s.id]"
      :color="s.color"
      :timeout="s.timeout"
      location="bottom"
      rounded="lg"
      elevation="8"
      @update:modelValue="v => { if (!v) remove(s.id) }"
    >
      {{ s.message }}
      <template #actions>
        <v-btn variant="text" @click="remove(s.id)">Close</v-btn>
      </template>
    </v-snackbar>
  </div>

  <!-- Progress dialog -->
  <v-dialog v-model="progress.active" persistent max-width="480">
    <v-card>
      <v-card-title class="text-h6">{{ progress.title || 'Working…' }}</v-card-title>
      <v-card-text>
        <div class="mb-3">{{ progress.message || 'Please wait' }}</div>
        <v-progress-linear
          :indeterminate="progress.indeterminate"
          :model-value="progress.value"
          height="8"
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn v-if="progress.cancellable" variant="text" @click="onCancel">Cancel</v-btn>
        <v-btn variant="flat" color="primary" @click="close" :disabled="progress.cancellable">OK</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { reactive, watchEffect } from 'vue'
import { storeToRefs } from 'pinia'
import { useNotifications } from '@/stores/notifications'

const store = useNotifications()
const { snacks, progress } = storeToRefs(store)

const visible = reactive({})
watchEffect(() => {
  for (const s of snacks.value) visible[s.id] = true
})

function remove(id) { store.removeSnack(id) }
function close() { store.hideProgress() }
function onCancel() {
  if (progress.value.onCancel) progress.value.onCancel()
  store.hideProgress()
}
</script>

<style scoped>
.snacks {
  position: fixed;
  left: 50%;
  bottom: 16px;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 9999;
}
</style>
