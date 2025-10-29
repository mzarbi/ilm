<template>
  <v-container fluid>
    <v-card>
      <v-card-title class="d-flex align-center">
        <div class="text-h6">Legal Entities</div>
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
        <v-btn color="primary" class="ml-2" prepend-icon="mdi-plus" @click="openCreate">New Entity</v-btn>
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
            <span class="text-caption text-medium-emphasis">{{ item.rmpm_type }} / {{ item.rmpm_code }}</span>
          </div>
        </template>

        <template #item.country="{ item }">
          <span>{{ countryLabel(item.country_id) }}</span>
        </template>

        <template #item.sector="{ item }">
          <span>{{ sectorLabel(item.sector_id) }}</span>
        </template>

        <template #item.flags="{ item }">
          <v-chip size="small" color="error" v-if="item.is_sanctioned" variant="flat">Sanctioned</v-chip>
          <v-chip size="small" color="warning" v-if="item.is_pep" class="ml-1" variant="flat">PEP</v-chip>
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
    <v-dialog v-model="dialog" max-width="1280">
      <v-card>
        <v-card-title class="text-h6">{{ editId ? 'Edit' : 'Create' }} Legal Entity</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="save">
            <div class="d-grid" style="grid-template-columns: repeat(12, 1fr); gap: 12px;">
              <!-- Left column -->
              <div class="col-span-6 d-flex flex-column ga-3">
                <v-text-field v-model="model.name" label="Name*" required density="compact" />
                <v-textarea v-model="model.description" label="Description" rows="3" auto-grow density="compact" />
                <v-text-field v-model="model.lei_code" label="LEI Code" density="compact" />
                <div class="d-flex ga-2">
                  <v-text-field v-model="model.rmpm_type" label="RMPM Type*" required style="max-width: 200px;" density="compact"  />
                  <v-text-field v-model="model.rmpm_code" label="RMPM Code*" required density="compact"  />
                </div>
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
                <div class="d-flex ga-4">
                  <v-switch v-model="model.is_sanctioned" inset color="error" label="Sanctioned" />
                  <v-switch v-model="model.is_pep" inset color="warning" label="PEP" />
                </div>
                <v-select
                  v-model="model.aml_risk"
                  :items="amlOptions"
                  label="AML Risk"
                  clearable
                  density="compact"
                />
              </div>

              <!-- Right column: identifiers -->
              <div class="col-span-6">
                <identifiers-editor v-model="model.identifiers" />
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
import IdentifiersEditor from '@/components/IdentifiersEditor.vue'

const { resource, notify } = useApi()
const api = resource('legal-entities')
const idApi = resource('entity-identifiers') // child resource (assumed available)

// table state
const headers = [
  { key: 'name', title: 'Name' },
  { key: 'country', title: 'Country' },
  { key: 'sector', title: 'Sector' },
  { key: 'flags', title: 'Flags', sortable: false, width: 140 },
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
  rmpm_code: '', rmpm_type: '', name: '', description: '',
  lei_code: '', country_id: null, sector_id: null,
  is_sanctioned: false, is_pep: false, aml_risk: 'medium',
  identifiers: [],
})

const amlOptions = ['low', 'medium', 'high', 'very_high']

// referentials for selects
const countries = ref([])
const sectors = ref([])

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
  if (q.value) { params.name = q.value; params.rmpm_code = q.value }
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
    rmpm_code: '', rmpm_type: '', name: '', description: '',
    lei_code: '', country_id: null, sector_id: null,
    is_sanctioned: false, is_pep: false, aml_risk: 'medium',
    identifiers: [],
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
    rmpm_code: row.rmpm_code,
    rmpm_type: row.rmpm_type,
    name: row.name,
    description: row.description || '',
    lei_code: row.lei_code || '',
    country_id: row.country_id || null,
    sector_id: row.sector_id || null,
    is_sanctioned: !!row.is_sanctioned,
    is_pep: !!row.is_pep,
    aml_risk: row.aml_risk || 'medium',
    // fetch identifiers separately if backend doesn’t include them on entity GET
    identifiers: Array.isArray(row.identifiers) ? row.identifiers : [],
  }
  dialog.value = true
}

async function save() {
  const payload = { ...model.value }
  // remove identifiers from main payload if backend doesn’t accept nested
  const identifiers = payload.identifiers || []
  delete payload.identifiers

  try {
    let entity
    if (editId.value) {
      entity = await api.update(editId.value, payload, 'Entity updated')
    } else {
      entity = await api.create(payload, 'Entity created')
      editId.value = entity.id
    }

    // Sync identifiers via child resource if available
    // strategy: delete all + recreate (simple); or diff if you prefer
    try {
      // try to list existing identifiers (if endpoint exists)
      const existing = await idApi.list({ entity_id: editId.value, page:1, page_size:1000 })
      const ex = existing.items || []
      await Promise.all(ex.map(r => idApi.remove(r.id, false))) // hard delete
    } catch {
      // if endpoint not available, just skip syncing
    }

    await Promise.all(
      (identifiers || [])
        .filter(r => r.scheme && r.value)
        .map(r => idApi.create({ entity_id: editId.value, scheme: r.scheme, value: r.value }))
    )

    dialog.value = false
    await load()
  } catch (e) {
    notify?.error(e?.message || 'Save failed')
  }
}

async function remove(row) {
  try {
    await api.remove(row.id, true, 'Entity deleted')
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
