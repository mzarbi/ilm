<template>
  <div class="d-flex flex-column ga-3">
    <div class="d-flex align-center justify-space-between">
      <div class="text-subtitle-2">Identifiers</div>
      <v-btn size="small" color="primary" prepend-icon="mdi-plus" @click="add">Add</v-btn>
    </div>

    <v-table density="comfortable">
      <thead>
        <tr>
          <th style="width: 200px">Scheme</th>
          <th>Value</th>
          <th style="width: 64px">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, i) in local" :key="row._key">
          <td>
            <!-- Combobox: editable + dropdown -->
            <v-combobox
              v-model="row.scheme"
              :items="schemes"
              label="Scheme"
              clearable
              density="compact"
              hide-details
              variant="outlined"
              @blur="emitChange"
              @keydown.enter="emitChange"
            />
          </td>
          <td>
            <v-text-field
              v-model="row.value"
              placeholder="Identifier value"
              density="compact"
              hide-details
              @blur="emitChange"
              @keydown.enter="emitChange"
            />
          </td>
          <td class="text-center">
            <v-btn icon="mdi-delete" size="small" variant="text" color="error" @click="remove(i)" />
          </td>
        </tr>

        <tr v-if="!local.length">
          <td colspan="3" class="text-medium-emphasis text-center py-6">No identifiers</td>
        </tr>
      </tbody>
    </v-table>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  schemes: {
    type: Array,
    default: () => ['LEI', 'BIC', 'SIREN', 'VAT', 'GIIN', 'INTERNAL', 'OTHER'],
  },
})
const emit = defineEmits(['update:modelValue'])

const local = ref([])

function uid() { return Math.random().toString(36).slice(2) }

function normalize(arr) {
  return (arr || []).map(r => ({
    id: r.id ?? null,
    scheme: r.scheme ?? '',
    value: r.value ?? '',
    _key: r._key || uid(),
  }))
}
function toPayload(arr) {
  return arr.map(({ _key, ...r }) => r)
}

watch(() => props.modelValue, (v) => {
  local.value = normalize(v)
}, { immediate: true })

function emitChange() {
  emit('update:modelValue', toPayload(local.value))
}

function add() {
  local.value.push({ id: null, scheme: '', value: '', _key: uid() })
  emitChange()
}

function remove(i) {
  local.value.splice(i, 1)
  emitChange()
}
</script>
