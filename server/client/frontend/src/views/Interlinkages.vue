<template>
  <v-container fluid>
    <v-card>
      <v-tabs v-model="tab" bg-color="primary" color="white" grow>
        <v-tab value="viz" prepend-icon="mdi-chart-timeline-variant">Viz</v-tab>
        <v-tab value="list" prepend-icon="mdi-graph-outline">Interlinkages</v-tab>
      </v-tabs>

      <v-window v-model="tab">
        <!-- ==================== VIZ (placeholder) ==================== -->
        <v-window-item value="viz">
          <v-card flat>
            <v-card-text class="text-medium-emphasis">
              <!-- keep empty for now -->
              <div class="py-10 text-center">
                <v-icon size="56" class="mb-3">mdi-chart-timeline-variant</v-icon>
                <div class="text-h6">Visualization coming soon</div>
                <div>Add graphs / network view here later.</div>
              </div>
            </v-card-text>
          </v-card>
        </v-window-item>

        <!-- ==================== LIST / CRUD ==================== -->
        <v-window-item value="list">
          <v-card flat>
            <v-card-title class="d-flex align-center">
              <div class="text-h6">Interlinkages</div>
              <v-spacer />
              <div class="d-flex align-center" style="gap: 8px;">
                <v-text-field
                  v-model="q"
                  label="Search by project / sponsor / counterparty"
                  clearable
                  density="compact"
                  hide-details
                  variant="outlined"
                  style="min-width: 360px; margin-bottom: 0;"
                  @keyup.enter="doSearch"
                  @click:clear="clearSearch"
                />
                <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreate">New Interlinkage</v-btn>
              </div>
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
              <template #item.sponsor="{ item }">
                {{ leLabel(item.sponsor_id) }}
              </template>
              <template #item.counterparty="{ item }">
                {{ leLabel(item.counterparty_id) }}
              </template>
              <template #item.project="{ item }">
                {{ projectLabel(item.project_id) }}
              </template>
              <template #item.currency="{ item }">
                {{ currencyLabel(item.currency_id) }}
              </template>
              <template #item.notional_amount="{ item }">
                <span v-if="item.notional_amount != null">{{ formatAmount(item.notional_amount) }}</span>
              </template>
              <template #item.actions="{ item }">
                <div class="d-flex flex-row align-center justify-center" style="gap:6px;">
                <v-btn
                    size="small"
                    variant="text"
                    icon="mdi-open-in-new"
                    :to="{ name: 'interlinkage-detail', params: { id: item.id } }"
                  />
                  <v-btn size="small" variant="text" icon="mdi-pencil" @click="openEdit(item)" />
                  <v-btn size="small" variant="text" color="error" icon="mdi-delete" @click="remove(item)" />
                </div>
              </template>
            </v-data-table-server>
          </v-card>

          <!-- Create/Edit Dialog -->
          <v-dialog v-model="dialog" max-width="1280">
            <v-card>
              <v-card-title class="text-h6">{{ editId ? 'Edit' : 'Create' }} Interlinkage</v-card-title>
              <v-card-text>
                <v-form @submit.prevent="save">
                  <div class="d-grid" style="grid-template-columns: repeat(12, 1fr); gap: 12px;">

                    <!-- LEFT -->
                    <div class="col-span-6 d-flex flex-column ga-3">
                      <div class="d-flex ga-2">
                        <v-select
                          v-model="model.sponsor_id"
                          :items="legalEntities"
                          :item-title="leItemTitle"
                          item-value="id"
                          label="Sponsor*"
                          density="compact"
                          clearable
                          required
                        />
                        <v-select
                          v-model="model.counterparty_id"
                          :items="legalEntities"
                          :item-title="leItemTitle"
                          item-value="id"
                          label="Counterparty*"
                          density="compact"
                          clearable
                          required
                        />
                      </div>

                      <v-select
                        v-model="model.booking_entity_id"
                        :items="legalEntities"
                        :item-title="leItemTitle"
                        item-value="id"
                        label="Booking Entity"
                        density="compact"
                        clearable
                      />

                      <v-select
                        v-model="model.project_id"
                        :items="projects"
                        item-title="name"
                        item-value="id"
                        label="Project*"
                        density="compact"
                        clearable
                        required
                      />

                      <div class="d-flex ga-2">
                        <v-select
                          v-model="model.pra_activity_id"
                          :items="praActivities"
                          item-title="label"
                          item-value="id"
                          label="PRA Activity"
                          density="compact"
                          clearable
                        />
                        <v-select
                          v-model="model.counterparty_type_id"
                          :items="counterpartyTypes"
                          item-title="label"
                          item-value="id"
                          label="Counterparty Type"
                          density="compact"
                          clearable
                        />
                      </div>

                      <div class="d-flex ga-2">
                        <v-select
                          v-model="model.facility_id"
                          :items="facilities"
                          item-title="reference"
                          item-value="id"
                          label="Facility"
                          density="compact"
                          clearable
                        />
                        <v-select
                          v-model="model.instrument_id"
                          :items="instruments"
                          item-title="reference"
                          item-value="id"
                          label="Instrument"
                          density="compact"
                          clearable
                        />
                      </div>
                    </div>

                    <!-- RIGHT -->
                    <div class="col-span-6 d-flex flex-column ga-3">
                      <div class="d-flex ga-2">
                        <v-text-field v-model="model.deal_date" type="date" label="Deal Date" density="compact" />
                        <v-text-field v-model="model.effective_date" type="date" label="Effective Date" density="compact" />
                        <v-text-field v-model="model.maturity_date" type="date" label="Maturity Date" density="compact" />
                      </div>

                      <div class="d-flex ga-2">
                        <v-text-field
                          v-model="model.notional_amount"
                          type="number"
                          label="Notional Amount"
                          density="compact"
                        />
                        <v-select
                          v-model="model.currency_id"
                          :items="currencies"
                          item-title="code"
                          item-value="id"
                          label="Currency"
                          density="compact"
                          clearable
                        />
                      </div>

                      <div class="d-flex ga-2">
                        <v-select
                          v-model="model.status"
                          :items="statusOptions"
                          label="Status*"
                          density="compact"
                          required
                        />
                        <v-text-field
                          v-model="model.purpose"
                          label="Purpose"
                          density="compact"
                        />
                      </div>

                      <v-textarea
                        v-model="model.remarks"
                        label="Remarks"
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
                <v-btn variant="text" @click="dialog=false">Cancel</v-btn>
                <v-btn color="primary" @click="save">Save</v-btn>
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

const { resource, notify } = useApi()
const api  = resource('interlinkages')

// referential apis
const leApi   = resource('legal-entities')
const prjApi  = resource('projects')
const praApi  = resource('pra-activities')
const cptApi  = resource('counterparty-types')
const facApi  = resource('facilities')
const insApi  = resource('instruments')
const curApi  = resource('currencies')

// tabs
const tab = ref('list')

// table state
const headers = [
  { key: 'project', title: 'Project' },
  { key: 'sponsor', title: 'Sponsor' },
  { key: 'counterparty', title: 'Counterparty' },
  { key: 'deal_date', title: 'Deal Date' },
  { key: 'notional_amount', title: 'Notional' },
  { key: 'currency', title: 'CCY' },
  { key: 'status', title: 'Status' },
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
const statusOptions = ['draft','validated','archived','deleted']

const model = ref({
  sponsor_id: null,
  counterparty_id: null,
  booking_entity_id: null,
  project_id: null,
  pra_activity_id: null,
  counterparty_type_id: null,
  facility_id: null,
  instrument_id: null,
  deal_date: '',
  effective_date: '',
  maturity_date: '',
  notional_amount: '',
  currency_id: null,
  status: 'draft',
  purpose: '',
  remarks: '',
})

// referential data
const legalEntities = ref([])
const projects      = ref([])
const praActivities = ref([])
const counterpartyTypes = ref([])
const facilities    = ref([])
const instruments   = ref([])
const currencies    = ref([])

function leItemTitle(le) {
  if (!le) return ''
  const code = le.rmpm_code ? ` [${le.rmpm_code}]` : ''
  return `${le.name}${code}`
}

function leLabel(id) {
  const o = legalEntities.value.find(x => x.id === id)
  return o ? leItemTitle(o) : ''
}
function projectLabel(id) {
  const o = projects.value.find(x => x.id === id)
  return o ? o.name : ''
}
function currencyLabel(id) {
  const o = currencies.value.find(x => x.id === id)
  return o ? o.code : ''
}

function formatAmount(a) {
  const num = typeof a === 'string' ? Number(a) : a
  if (Number.isFinite(num)) return num.toLocaleString(undefined, { maximumFractionDigits: 2 })
  return a
}

async function loadRefs() {
  try {
    const [les, prj, pra, cpt, fac, ins, cur] = await Promise.all([
      leApi.list({ page:1, page_size:1000, sort:'name:asc' }),
      prjApi.list({ page:1, page_size:1000, sort:'name:asc' }),
      praApi.list({ page:1, page_size:1000, sort:'label:asc' }),
      cptApi.list({ page:1, page_size:1000, sort:'label:asc' }),
      facApi.list({ page:1, page_size:1000, sort:'reference:asc' }),
      insApi.list({ page:1, page_size:1000, sort:'reference:asc' }),
      curApi.list({ page:1, page_size:1000, sort:'code:asc' }),
    ])
    legalEntities.value   = les.items || []
    projects.value        = prj.items || []
    praActivities.value   = pra.items || []
    counterpartyTypes.value = cpt.items || []
    facilities.value      = fac.items || []
    instruments.value     = ins.items || []
    currencies.value      = cur.items || []
  } catch (e) {
    notify?.error('Failed loading referentials')
  }
}

function doSearch() { page.value = 1; load() }
function clearSearch() { q.value=''; page.value=1; load() }

async function load() {
  const params = { page: page.value, page_size: pageSize.value, sort: 'deal_date:desc' }
  // naive search support: try name matches via project & LE name/code if backend supports filters
  if (q.value) {
    params.project = q.value
    params.sponsor = q.value
    params.counterparty = q.value
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

function resetModel() {
  model.value = {
    sponsor_id: null,
    counterparty_id: null,
    booking_entity_id: null,
    project_id: null,
    pra_activity_id: null,
    counterparty_type_id: null,
    facility_id: null,
    instrument_id: null,
    deal_date: '',
    effective_date: '',
    maturity_date: '',
    notional_amount: '',
    currency_id: null,
    status: 'draft',
    purpose: '',
    remarks: '',
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
    sponsor_id: row.sponsor_id || null,
    counterparty_id: row.counterparty_id || null,
    booking_entity_id: row.booking_entity_id || null,
    project_id: row.project_id || null,
    pra_activity_id: row.pra_activity_id || null,
    counterparty_type_id: row.counterparty_type_id || null,
    facility_id: row.facility_id || null,
    instrument_id: row.instrument_id || null,
    deal_date: row.deal_date || '',
    effective_date: row.effective_date || '',
    maturity_date: row.maturity_date || '',
    notional_amount: row.notional_amount != null ? String(row.notional_amount) : '',
    currency_id: row.currency_id || null,
    status: row.status || 'draft',
    purpose: row.purpose || '',
    remarks: row.remarks || '',
  }
  dialog.value = true
}

async function save() {
  const p = { ...model.value }
  // ensure numeric type for notional if present
  if (p.notional_amount === '') delete p.notional_amount
  else if (typeof p.notional_amount === 'string') p.notional_amount = Number(p.notional_amount)

  // basic requireds
  if (!p.sponsor_id || !p.counterparty_id || !p.project_id || !p.status) {
    notify?.error('Sponsor, Counterparty, Project and Status are required')
    return
  }

  try {
    if (editId.value) {
      await api.update(editId.value, p, 'Interlinkage updated')
    } else {
      await api.create(p, 'Interlinkage created')
    }
    dialog.value = false
    await load()
  } catch (e) {
    const msg = String(e?.message || '')
    // friendly message for natural-key unique
    if (msg.toLowerCase().includes('unique') && msg.includes('uq_interlinkage_natural')) {
      notify?.error('An interlinkage with same Sponsor / Project / Counterparty / Deal Date already exists')
    } else {
      notify?.error('Save failed')
    }
  }
}

async function remove(row) {
  try {
    await api.remove(row.id, true, 'Interlinkage deleted')
    await load()
  } catch (e) {
    notify?.error(e?.message || 'Delete failed')
  }
}

// bootstrap
loadRefs()
load()
</script>

<style scoped>
.d-grid { display: grid; }
.col-span-6 { grid-column: span 6; }
@media (max-width: 1200px) {
  .col-span-6 { grid-column: span 12; }
}
</style>
