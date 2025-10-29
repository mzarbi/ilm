<template>
  <v-container fluid>
    <v-card>
      <v-card-title class="d-flex align-center">
        <div class="text-h6">Projects</div>
        <v-spacer />
        <v-text-field
          v-model="q"
          label="Search name / code"
          clearable
          density="compact"
          hide-details
          variant="outlined"
          style="max-width: 280px; margin-bottom: 0;"
          @keyup.enter="doSearch"
          @click:clear="clearSearch"
        />
        <v-btn color="primary" class="ml-2" prepend-icon="mdi-plus" @click="openCreate">New Project</v-btn>
      </v-card-title>

      <v-data-table-server
        :headers="headers"
        :items="items"
        :items-length="total"
        :loading="loading"
        :page="page"
        :items-per-page="pageSize"
        class="mb-2"
        @update:page="p => { page = p; load() }"
        @update:items-per-page="ps => { pageSize = ps; page = 1; load() }"
      >
        <template #item.name="{ item }">
          <div class="d-flex flex-column">
            <span class="font-weight-medium">{{ item.name }}</span>
            <span class="text-caption text-medium-emphasis">{{ item.code }}</span>
          </div>
        </template>

        <template #item.country="{ item }">
          <span>{{ countryLabel(item.country_id) }}</span>
        </template>

        <template #item.sector="{ item }">
          <span>{{ sectorLabel(item.sector_id) }}</span>
        </template>

        <template #item.actions="{ item }">
          <div class="d-flex flex-row align-center justify-center" style="gap:6px;">
            <v-btn size="small" variant="text" icon="mdi-pencil" @click="openEdit(item)" />
            <v-btn size="small" variant="text" color="error" icon="mdi-delete" @click="remove(item)" />
          </div>
        </template>
      </v-data-table-server>
    </v-card>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="dialog" max-width="880">
      <v-card>
        <v-card-title class="text-h6">{{ editId ? 'Edit' : 'Create' }} Project</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="save">
            <div class="d-grid" style="grid-template-columns: repeat(12, 1fr); gap: 12px;">
              <div class="d-flex flex-column ga-3" style="grid-column: span 12;">
                <div class="d-flex ga-2">
                  <v-text-field v-model="model.code" label="Code" density="compact" />
                  <v-text-field v-model="model.name" label="Name*" required density="compact" />
                </div>
                <v-textarea v-model="model.description" label="Description" rows="3" auto-grow density="compact" />
                <div class="d-flex ga-2">
                  <v-select
                    v-model="model.country_id"
                    :items="countries"
                    item-title="name"
                    item-value="id"
                    label="Country"
                    clearable
                    density="compact"
                  />
                  <v-select
                    v-model="model.sector_id"
                    :items="sectors"
                    item-title="label"
                    item-value="id"
                    label="Sector"
                    clearable
                    density="compact"
                  />
                </div>
                <div class="d-flex ga-2">
                  <v-select
                    v-model="model.region"
                    :items="regions"
                    label="Region"
                    clearable
                    density="compact"
                  />
                  <v-text-field v-model="model.business_line" label="Business line" density="compact" />
                </div>
                <v-textarea v-model="model.portfolio" label="Portfolio" density="compact" />
              </div>
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
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'

const { resource, notify } = useApi()
const api = resource('projects')

// server-table state
const headers = [
  { key: 'name', title: 'Name' },
  { key: 'country', title: 'Country' },
  { key: 'sector', title: 'Sector' },
  { key: 'region', title: 'Region' },
  { key: 'business_line', title: 'Business line' },
  { key: 'portfolio', title: 'Portfolio' },
  { key: 'actions', title: 'Actions', sortable: false, width: 110 },
]
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const q = ref('')

// dialog/form
const dialog = ref(false)
const editId = ref(null)
const model = ref({
  code: '', name: '', description: '',
  sector_id: null, country_id: null,
  region: 'EMEA', business_line: '', portfolio: '',
})

// referentials
const countries = ref([])
const sectors = ref([])
const regions = ref([
  'EMEA', 'APAC', 'AMER', 'OTHER', 'MULTI-TENANT'
])

function countryLabel(id) {
  const c = countries.value.find(x => x.id === id)
  return c ? c.name : ''
}
function sectorLabel(id) {
  const s = sectors.value.find(x => x.id === id)
  return s ? s.label : ''
}

async function loadRefs() {
  try {
    const [c, s] = await Promise.all([
      resource('countries').list({ page:1, page_size:1000, sort:'name:asc' }),
      resource('sectors').list({ page:1, page_size:1000, sort:'label:asc' }),
    ])
    countries.value = c.items || []
    sectors.value = s.items || []
  } catch (e) {
    notify?.error('Failed loading referentials')
  }
}

function doSearch() { page.value = 1; load() }
function clearSearch() { q.value=''; page.value=1; load() }

async function load() {
  const params = { page: page.value, page_size: pageSize.value, sort: 'name:asc' }
  if (q.value) { params.name = q.value; params.code = q.value }
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

function resetModel() {
  model.value = {
    code: '', name: '', description: '',
    sector_id: null, country_id: null,
    region: 'EMEA', business_line: '', portfolio: '',
  }
}

function openCreate() {
  editId.value = null
  resetModel()
  dialog.value = true
}

function openEdit(row) {
  editId.value = row.id
  model.value = {
    code: row.code || '',
    name: row.name || '',
    description: row.description || '',
    sector_id: row.sector_id || null,
    country_id: row.country_id || null,
    region: row.region || 'EMEA',
    business_line: row.business_line || '',
    portfolio: row.portfolio || '',
  }
  dialog.value = true
}

async function save() {
  try {
    const payload = { ...model.value }
    if (!payload.name) { notify?.error('Name is required'); return }
    let project
    if (editId.value) {
      project = await api.update(editId.value, payload, 'Project updated')
    } else {
      project = await api.create(payload, 'Project created')
      editId.value = project.id
    }
    dialog.value = false
    await load()
  } catch (e) {
    // handle unique constraints nicely
    const msg = String(e?.message || '')
    if (msg.toLowerCase().includes('unique') && msg.includes('projects.name')) {
      notify?.error('Name must be unique')
    } else if (msg.toLowerCase().includes('unique') && msg.includes('projects.code')) {
      notify?.error('Code must be unique')
    } else {
      notify?.error('Save failed')
    }
  }
}

async function remove(row) {
  try {
    await api.remove(row.id, true, 'Project deleted')
    await load()
  } catch (e) {
    notify?.error(e?.message || 'Delete failed')
  }
}

loadRefs()
load()
</script>

<style scoped>
.d-grid { display: grid; }
.col-span-6 { grid-column: span 6; }
@media (max-width: 960px) {
  .col-span-6 { grid-column: span 12; }
}
</style>
