<template>
  <div>
    <div class="d-flex align-center mb-3" style="gap: 8px;">
      <v-text-field
        v-model="q"
        label="Search"
        clearable
        density="compact"
        hide-details
        variant="outlined"
        style="margin-bottom: 0;"
        @keyup.enter="load"
        @click:clear="clearSearch"
      />

      <v-btn
        color="primary"
        style="padding: 0.6rem;"
        prepend-icon="mdi-plus"
        @click="openCreate"
      >
        New {{ title }}
      </v-btn>
    </div>

    <v-data-table-server
      :headers="headers"
      :items="items"
      :items-length="total"
      :page="page"
      :items-per-page="pageSize"
      :loading="loading"
      class="mb-4"
      @update:page="p => { page = p; load() }"
      @update:items-per-page="ps => { pageSize = ps; page = 1; load() }"
    >
      <template #item.actions="{ item }">
        <div class="d-flex flex-row align-center justify-center ga-1">
          <v-btn size="small" variant="text" color="primary" icon="mdi-pencil" @click="openEdit(item)" />
          <v-btn size="small" variant="text" color="error" icon="mdi-delete" @click="remove(item)" />
        </div>
      </template>
    </v-data-table-server>

    <!-- One dialog reused for create + edit -->
    <v-dialog v-model="dialog" max-width="520">
      <v-card>
        <v-card-title class="text-h6">{{ editId ? 'Edit' : 'Create' }} {{ title }}</v-card-title>
        <v-card-text>
          <v-form ref="formRef" @submit.prevent="save">
            <div class="d-flex flex-column ga-3">
              <component
                v-for="f in fields"
                :key="f.key"
                :is="fieldComponent(f)"
                v-model="model[f.key]"
                v-bind="fieldProps(f)"
                density="compact"
              />
            </div>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dialog=false">Cancel</v-btn>
          <v-btn color="primary" @click="save">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, inject } from 'vue'
import { useApi } from '@/composables/useApi'
import { VTextField, VTextarea } from 'vuetify/components'


/**
 * Props:
 * - title: display name (e.g., "Currency")
 * - resource: API resource base (e.g., "currencies")
 * - columns: [{ key, title, width? }]
 * - fields: form schema [{ key, label, type, required, hint, maxlength }]
 * - defaultSort: "id:asc" or "code:asc" etc.
 */
const props = defineProps({
  title: { type: String, required: true },
  resource: { type: String, required: true },
  columns: { type: Array, required: true },
  fields: { type: Array, required: true },
  defaultSort: { type: String, default: 'id:asc' },
})

const { resource: resFn, notify } = useApi()
const api = resFn(props.resource)

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const q = ref('')
const sort = ref(props.defaultSort)

const headers = computed(() => [
  ...props.columns.map(c => ({ key: c.key, title: c.title, width: c.width || undefined })),
  { key: 'actions', title: 'Actions', sortable: false, width: 110 },
])

// dialog/form
const dialog = ref(false)
const editId = ref(null)
const model = ref({})
const formRef = ref(null)

function resetModel() {
  const m = {}
  for (const f of props.fields) m[f.key] = f.default ?? null
  model.value = m
}

function openCreate() {
  editId.value = null
  resetModel()
  dialog.value = true
}

function openEdit(row) {
  editId.value = row.id
  // shallow copy; ensure keys exist
  const m = {}
  for (const f of props.fields) m[f.key] = row[f.key] ?? null
  model.value = m
  dialog.value = true
}

async function save() {
  try {
    const payload = { ...model.value }
    if (editId.value) {
      await api.update(editId.value, payload, 'Updated')
    } else {
      await api.create(payload, 'Created')
    }
    dialog.value = false
    await load()
  } catch (e) {
    notify?.error(e?.message || 'Save failed')
  }
}

async function remove(row) {
  try {
    await api.remove(row.id, true, 'Deleted')
    await load()
  } catch (e) {
    notify?.error(e?.message || 'Delete failed')
  }
}

const loading = ref(false)

function clearSearch() {
  q.value = ''
  page.value = 1
  load()
}

async function load() {
  const params = {
    page: page.value,
    page_size: pageSize.value,
    sort: sort.value,
  }
  if (q.value) {
    const keys = props.columns.slice(0, 2).map(c => c.key)
    for (const k of keys) params[k] = q.value
  }
  try {
    loading.value = true
    const res = await api.list(params)
    items.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    notify?.error(e?.message || 'Load failed')
  } finally {
    loading.value = false
  }
}

// helpers for form field rendering
function fieldComponent(f) {
  if (f.type === 'textarea') return VTextarea
  // number/date also use text-field with type attr
  return VTextField
}

function fieldProps(f) {
  const base = {
    label: f.label,
    required: !!f.required,
    hint: f.hint,
    persistentHint: !!f.hint,
    clearable: true,
    density: 'comfortable',
  }
  if (f.type === 'number') return { ...base, type: 'number' }
  if (f.type === 'date')   return { ...base, type: 'date' }
  if (f.maxlength)         return { ...base, counter: true, maxlength: f.maxlength }
  return base
}

// auto-reload when tab props change (e.g., switching tabs reuses component)
watch(() => [props.resource, props.columns, props.fields], () => {
  page.value = 1
  resetModel()
  load()
}, { immediate: true })
</script>
