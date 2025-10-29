<template>
  <v-container fluid>
    <v-card>
      <v-tabs v-model="tab" bg-color="primary" color="white" grow>
        <v-tab value="facilities" prepend-icon="mdi-office-building">Facilities</v-tab>
        <v-tab value="instruments" prepend-icon="mdi-finance">Instruments</v-tab>
      </v-tabs>

      <v-window v-model="tab">
        <!-- ================= FACILITIES ================ -->
        <v-window-item value="facilities">
          <v-card flat>
            <v-card-title class="d-flex align-center">
              <div class="text-h6">Facilities</div>
              <v-spacer  />
              <div class="d-flex align-center" style="gap: 8px;">
                <v-text-field
                  v-model="fac.q"
                  label="Search reference"
                  clearable
                  density="compact"
                  hide-details
                  variant="outlined"
                  style="min-width: 280px; margin-bottom: 0;"
                  @keyup.enter="facDoSearch"
                  @click:clear="facClearSearch"
                />
                <v-btn color="primary" prepend-icon="mdi-plus" @click="facOpenCreate">New Facility</v-btn>
              </div>
            </v-card-title>

            <v-data-table-server
              :headers="fac.headers"
              :items="fac.items"
              :items-length="fac.total"
              :loading="fac.loading"
              :page="fac.page"
              :items-per-page="fac.pageSize"
              class="mb-2"
              @update:page="p => { fac.page = p; facLoad() }"
              @update:items-per-page="ps => { fac.pageSize = ps; fac.page = 1; facLoad() }"
            >
              <template #item.facility_type="{ item }">
                {{ facTypeLabel(item.facility_type_id) }}
              </template>
              <template #item.currency="{ item }">
                {{ currencyLabel(item.currency_id) }}
              </template>
              <template #item.actions="{ item }">
                <div class="d-flex flex-row align-center justify-center" style="gap:6px;">
                  <v-btn size="small" variant="text" icon="mdi-pencil" @click="facOpenEdit(item)" />
                  <v-btn size="small" variant="text" color="error" icon="mdi-delete" @click="facRemove(item)" />
                </div>
              </template>
            </v-data-table-server>
          </v-card>

          <!-- Facility Dialog -->
          <v-dialog v-model="fac.dialog" max-width="720">
            <v-card>
              <v-card-title class="text-h6">{{ fac.editId ? 'Edit' : 'Create' }} Facility</v-card-title>
              <v-card-text>
                <v-form @submit.prevent="facSave">
                  <div class="d-grid" style="grid-template-columns: repeat(12, 1fr); gap: 12px;">
                    <div class="col-span-6 d-flex flex-column ga-3">
                      <v-select
                        v-model="fac.model.facility_type_id"
                        :items="facTypes"
                        item-title="label"
                        item-value="id"
                        label="Facility Type*"
                        density="compact"
                        clearable
                        required
                      />
                      <v-text-field
                        v-model="fac.model.reference"
                        label="Reference*"
                        density="compact"
                        required
                      />
                      <div class="d-flex ga-2">
                        <v-text-field
                          v-model="fac.model.limit_amount"
                          type="number"
                          label="Limit Amount*"
                          density="compact"
                          required
                        />
                        <v-select
                          v-model="fac.model.currency_id"
                          :items="currencies"
                          item-title="code"
                          item-value="id"
                          label="Currency*"
                          density="compact"
                          clearable
                          required
                        />
                      </div>
                      <v-text-field
                        v-model="fac.model.maturity_date"
                        type="date"
                        label="Maturity Date"
                        density="compact"
                      />
                    </div>
                  </div>
                </v-form>
              </v-card-text>
              <v-card-actions>
                <v-spacer />
                <v-btn variant="text" @click="fac.dialog = false">Cancel</v-btn>
                <v-btn color="primary" @click="facSave">Save</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
        </v-window-item>

        <!-- ================= INSTRUMENTS ================ -->
        <v-window-item value="instruments">
          <v-card flat>
            <v-card-title class="d-flex align-center">
              <div class="text-h6">Instruments</div>
              <v-spacer />
              <div class="d-flex align-center" style="gap: 8px;">
                <v-text-field
                  v-model="ins.q"
                  label="Search reference/desc"
                  clearable
                  density="compact"
                  hide-details
                  variant="outlined"
                  style="min-width: 280px; margin-bottom: 0;"
                  @keyup.enter="insDoSearch"
                  @click:clear="insClearSearch"
                />
                <v-btn color="primary" prepend-icon="mdi-plus" @click="insOpenCreate">New Instrument</v-btn>
              </div>
            </v-card-title>

            <v-data-table-server
              :headers="ins.headers"
              :items="ins.items"
              :items-length="ins.total"
              :loading="ins.loading"
              :page="ins.page"
              :items-per-page="ins.pageSize"
              class="mb-2"
              @update:page="p => { ins.page = p; insLoad() }"
              @update:items-per-page="ps => { ins.pageSize = ps; ins.page = 1; insLoad() }"
            >
              <template #item.instrument_type="{ item }">
                {{ insTypeLabel(item.instrument_type_id) }}
              </template>
              <template #item.actions="{ item }">
                <div class="d-flex flex-row align-center justify-center" style="gap:6px;">
                  <v-btn size="small" variant="text" icon="mdi-pencil" @click="insOpenEdit(item)" />
                  <v-btn size="small" variant="text" color="error" icon="mdi-delete" @click="insRemove(item)" />
                </div>
              </template>
            </v-data-table-server>
          </v-card>

          <!-- Instrument Dialog -->
          <v-dialog v-model="ins.dialog" max-width="720">
            <v-card>
              <v-card-title class="text-h6">{{ ins.editId ? 'Edit' : 'Create' }} Instrument</v-card-title>
              <v-card-text>
                <v-form @submit.prevent="insSave">
                  <div class="d-grid" style="grid-template-columns: repeat(12, 1fr); gap: 12px;">
                    <div class="col-span-6 d-flex flex-column ga-3">
                      <v-select
                        v-model="ins.model.instrument_type_id"
                        :items="insTypes"
                        item-title="label"
                        item-value="id"
                        label="Instrument Type*"
                        density="compact"
                        clearable
                        required
                      />
                      <v-text-field
                        v-model="ins.model.reference"
                        label="Reference"
                        density="compact"
                      />
                      <v-textarea
                        v-model="ins.model.description"
                        label="Description"
                        auto-grow
                        rows="3"
                        density="compact"
                      />
                    </div>
                  </div>
                </v-form>
              </v-card-text>
              <v-card-actions>
                <v-spacer />
                <v-btn variant="text" @click="ins.dialog = false">Cancel</v-btn>
                <v-btn color="primary" @click="insSave">Save</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
        </v-window-item>
      </v-window>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'

const tab = ref('facilities')

const { resource, notify } = useApi()
// APIs
const facApi = resource('facilities')
const insApi = resource('instruments')
const facTypeApi = resource('facility-types')
const insTypeApi = resource('instrument-types')
const curApi = resource('currencies')

// referentials
const facTypes = ref([])
const insTypes = ref([])
const currencies = ref([])

function facTypeLabel(id) {
  const o = facTypes.value.find(x => x.id === id)
  return o ? o.label : ''
}
function insTypeLabel(id) {
  const o = insTypes.value.find(x => x.id === id)
  return o ? o.label : ''
}
function currencyLabel(id) {
  const o = currencies.value.find(x => x.id === id)
  return o ? o.code : ''
}

// ---------- Facilities state & CRUD ----------
const fac = ref({
  headers: [
    { key: 'reference', title: 'Reference' },
    { key: 'facility_type', title: 'Type' },
    { key: 'limit_amount', title: 'Limit' },
    { key: 'currency', title: 'Currency' },
    { key: 'maturity_date', title: 'Maturity' },
    { key: 'actions', title: 'Actions', sortable: false, width: 110 },
  ],
  items: [],
  total: 0,
  page: 1,
  pageSize: 10,
  q: '',
  loading: false,
  dialog: false,
  editId: null,
  model: {
    facility_type_id: null,
    reference: '',
    limit_amount: '',
    currency_id: null,
    maturity_date: '',
  },
})

function facResetModel() {
  fac.value.model = {
    facility_type_id: null,
    reference: '',
    limit_amount: '',
    currency_id: null,
    maturity_date: '',
  }
}
function facDoSearch() { fac.value.page = 1; facLoad() }
function facClearSearch() { fac.value.q = ''; fac.value.page = 1; facLoad() }

async function facLoad() {
  const params = { page: fac.value.page, page_size: fac.value.pageSize, sort: 'reference:asc' }
  if (fac.value.q) params.reference = fac.value.q
  try {
    fac.value.loading = true
    const res = await facApi.list(params)
    fac.value.items = res.items || []
    fac.value.total = res.total || 0
  } catch (e) {
    notify?.error(e?.message || 'Failed loading facilities')
  } finally {
    fac.value.loading = false
  }
}
function facOpenCreate() {
  fac.value.editId = null
  facResetModel()
  fac.value.dialog = true
}
function facOpenEdit(row) {
  fac.value.editId = row.id
  fac.value.model = {
    facility_type_id: row.facility_type_id || null,
    reference: row.reference || '',
    limit_amount: row.limit_amount != null ? String(row.limit_amount) : '',
    currency_id: row.currency_id || null,
    maturity_date: row.maturity_date || '',
  }
  fac.value.dialog = true
}
async function facSave() {
  const p = { ...fac.value.model }
  if (!p.facility_type_id || !p.reference || !p.limit_amount || !p.currency_id) {
    notify?.error('Please fill required fields')
    return
  }
  // convert numeric
  if (typeof p.limit_amount === 'string') p.limit_amount = Number(p.limit_amount)
  try {
    if (fac.value.editId) {
      await facApi.update(fac.value.editId, p, 'Facility updated')
    } else {
      await facApi.create(p, 'Facility created')
    }
    fac.value.dialog = false
    await facLoad()
  } catch (e) {
    const msg = String(e?.message || '')
    if (msg.toLowerCase().includes('unique') && msg.includes('facilities.reference')) {
      notify?.error('Reference must be unique')
    } else {
      notify?.error('Save failed')
    }
  }
}
async function facRemove(row) {
  try {
    await facApi.remove(row.id, true, 'Facility deleted')
    await facLoad()
  } catch (e) {
    notify?.error(e?.message || 'Delete failed')
  }
}

// ---------- Instruments state & CRUD ----------
const ins = ref({
  headers: [
    { key: 'reference', title: 'Reference' },
    { key: 'instrument_type', title: 'Type' },
    { key: 'description', title: 'Description' },
    { key: 'actions', title: 'Actions', sortable: false, width: 110 },
  ],
  items: [],
  total: 0,
  page: 1,
  pageSize: 10,
  q: '',
  loading: false,
  dialog: false,
  editId: null,
  model: {
    instrument_type_id: null,
    reference: '',
    description: '',
  },
})

function insResetModel() {
  ins.value.model = {
    instrument_type_id: null,
    reference: '',
    description: '',
  }
}
function insDoSearch() { ins.value.page = 1; insLoad() }
function insClearSearch() { ins.value.q = ''; ins.value.page = 1; insLoad() }

async function insLoad() {
  const params = { page: ins.value.page, page_size: ins.value.pageSize, sort: 'reference:asc' }
  if (ins.value.q) { params.reference = ins.value.q; params.description = ins.value.q }
  try {
    ins.value.loading = true
    const res = await insApi.list(params)
    ins.value.items = res.items || []
    ins.value.total = res.total || 0
  } catch (e) {
    notify?.error(e?.message || 'Failed loading instruments')
  } finally {
    ins.value.loading = false
  }
}
function insOpenCreate() {
  ins.value.editId = null
  insResetModel()
  ins.value.dialog = true
}
function insOpenEdit(row) {
  ins.value.editId = row.id
  ins.value.model = {
    instrument_type_id: row.instrument_type_id || null,
    reference: row.reference || '',
    description: row.description || '',
  }
  ins.value.dialog = true
}
async function insSave() {
  const p = { ...ins.value.model }
  if (!p.instrument_type_id) {
    notify?.error('Instrument Type is required')
    return
  }
  try {
    if (ins.value.editId) {
      await insApi.update(ins.value.editId, p, 'Instrument updated')
    } else {
      await insApi.create(p, 'Instrument created')
    }
    ins.value.dialog = false
    await insLoad()
  } catch (e) {
    const msg = String(e?.message || '')
    if (msg.toLowerCase().includes('unique') && msg.includes('instruments.reference')) {
      notify?.error('Reference must be unique')
    } else {
      notify?.error('Save failed')
    }
  }
}
async function insRemove(row) {
  try {
    await insApi.remove(row.id, true, 'Instrument deleted')
    await insLoad()
  } catch (e) {
    notify?.error(e?.message || 'Delete failed')
  }
}

// ---------- bootstrap ----------
async function loadRefs() {
  try {
    const [ft, it, cur] = await Promise.all([
      facTypeApi.list({ page:1, page_size:1000, sort:'label:asc' }),
      insTypeApi.list({ page:1, page_size:1000, sort:'label:asc' }),
      curApi.list({ page:1, page_size:1000, sort:'code:asc' }),
    ])
    facTypes.value = ft.items || []
    insTypes.value = it.items || []
    currencies.value = cur.items || []
  } catch (e) {
    notify?.error('Failed loading referentials')
  }
}

loadRefs()
facLoad()
insLoad()
</script>

<style scoped>
.d-grid { display: grid; }
.col-span-6 { grid-column: span 12; }
@media (max-width: 960px) {
  .col-span-6 { grid-column: span 12; }
}
</style>
