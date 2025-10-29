<template>
  <v-container fluid class="py-4">
    <v-row class="mb-3" align="center" no-gutters>
  <v-col cols="12" md="8">
    <v-card rounded="xl" class="pa-3 d-flex align-center flex-wrap" elevation="2" style="gap:8px;">
      <!-- Mode -->
      <v-btn-toggle v-model="mode" rounded="xl" density="comfortable" divided>
        <v-btn value="project" prepend-icon="mdi-briefcase-outline">Project</v-btn>
        <v-btn value="entity" prepend-icon="mdi-domain">Legal entity</v-btn>
        <v-btn value="interlinkage" prepend-icon="mdi-vector-polyline">Interlinkage</v-btn>
      </v-btn-toggle>

      <!-- Focus selector (async) -->
      <v-select
        v-model="focusId"
        :items="selectItems"
        :loading="selectLoading"
        :label="selectLabel"
        density="comfortable"
        variant="solo"
        class="flex-grow-1"
        clearable
        item-title="text"
        item-value="value"
      >
        <template #append-item>
          <v-divider />
          <div class="px-3 py-2">
            <v-btn
              block
              variant="text"
              prepend-icon="mdi-download"
              :disabled="!hasMoreSelect"
              @click.stop="loadMoreSelect"
            >
              {{ hasMoreSelect ? 'Load more' : 'No more results' }}
            </v-btn>
          </div>
        </template>
      </v-select>


      <v-btn color="primary" prepend-icon="mdi-crosshairs-gps" :loading="loading" @click="applyFocus">Focus</v-btn>
      <v-btn variant="text" prepend-icon="mdi-fit-to-page-outline" @click="fitToContent">Fit</v-btn>
    </v-card>
  </v-col>

  <v-col cols="12" md="4">
    <v-card rounded="xl" class="pa-3" elevation="2">
      <!-- Contextual toggles -->
      <template v-if="mode==='project'">
        <div class="d-flex align-center" style="gap:12px; flex-wrap: wrap;">
          <v-switch v-model="ctx.project.showEntities" label="Legal parties" hide-details density="compact"/>
          <v-switch v-model="ctx.project.showInterdeps" label="Interdependencies" hide-details density="compact"/>
        </div>
      </template>

      <template v-else-if="mode==='entity'">
        <div class="d-flex align-center" style="gap:12px; flex-wrap: wrap;">
          <v-switch v-model="ctx.entity.showProjects" label="Projects" hide-details density="compact"/>
          <v-switch v-model="ctx.entity.showInterdeps" label="Interdependencies" hide-details density="compact"/>
        </div>
        <div class="d-flex align-center mt-2" style="gap:8px; flex-wrap: wrap;">
          <v-chip-group v-model="ctx.entity.role" mandatory filter>
            <v-chip value="all" label>All roles</v-chip>
            <v-chip value="sponsor" label>Sponsor</v-chip>
            <v-chip value="counterparty" label>Counterparty</v-chip>
            <v-chip value="both" label>Both</v-chip>
          </v-chip-group>
        </div>
      </template>

      <template v-else-if="mode==='interlinkage'">
        <div class="d-flex align-center" style="gap:12px; flex-wrap: wrap;">
          <v-switch v-model="ctx.interlinkage.showInterdeps" label="Interdependencies" hide-details density="compact"/>
        </div>
      </template>
    </v-card>
  </v-col>
</v-row>


    <v-row>
      <v-col cols="12" md="9">
        <v-card rounded="xl" elevation="3" class="graph-wrapper">
          <div ref="paperEl" class="graph-paper"></div>
          <div ref="navigatorEl" class="graph-navigator"></div>
        </v-card>
      </v-col>

      <v-col cols="12" md="3">
        <v-card rounded="xl" elevation="3" class="pa-0">
          <v-toolbar density="comfortable" color="blue-grey-lighten-5">
            <v-toolbar-title class="text-subtitle-1 font-weight-bold">Details</v-toolbar-title>
            <v-spacer/>
            <v-btn icon="mdi-close" variant="text" @click="selected = null"/>
          </v-toolbar>

          <div v-if="!selected" class="pa-4 text-medium-emphasis">
            <div class="d-flex align-center mb-2"><v-icon class="mr-1">mdi-information-outline</v-icon> Select a node or a link.</div>
            <legend-block/>
          </div>

          <div v-else class="pa-4">
            <template v-if="selected.kind === 'entity'">
              <div class="text-h6 mb-2">{{ selected.data.name }}</div>
              <v-chip class="mr-1 mb-2" label>RMPM {{ selected.data.rmpm_type }} — {{ selected.data.rmpm_code }}</v-chip>
              <v-list density="compact">
                <v-list-item title="Country" :subtitle="selected.data.country?.name || '—'"/>
                <v-list-item title="Sector" :subtitle="selected.data.sector?.label || '—'"/>
                <v-list-item title="Flags" :subtitle="entityFlags(selected.data)"/>
              </v-list>
              <v-divider class="my-3"/>
              <v-btn block variant="tonal" prepend-icon="mdi-crosshairs" @click="focusEntity(selected.data.id)">Focus this entity</v-btn>
            </template>

            <template v-else-if="selected.kind === 'project'">
              <div class="text-h6 mb-2">{{ selected.data.name }}</div>
              <v-chip class="mr-1 mb-2" label>Code: {{ selected.data.code || '—' }}</v-chip>
              <v-list density="compact">
                <v-list-item title="Country" :subtitle="selected.data.country?.name || '—'"/>
                <v-list-item title="Sector" :subtitle="selected.data.sector?.label || '—'"/>
                <v-list-item title="Business line" :subtitle="selected.data.business_line || '—'"/>
              </v-list>
                <v-divider class="my-3"/>
                <v-btn block variant="tonal" prepend-icon="mdi-crosshairs" @click="focusProject(selected.data.id)">Focus this project</v-btn>
            </template>

            <template v-else-if="selected.kind === 'interlinkage'">
              <div class="text-h6 mb-1">Interlinkage #{{ selected.data.id }}</div>
              <div class="text-caption mb-2">Status: <strong>{{ selected.data.status }}</strong></div>
              <v-list density="compact">
                <v-list-item title="Deal date" :subtitle="fmtDate(selected.data.deal_date)"/>
                <v-list-item title="Notional" :subtitle="fmtAmount(selected.data.notional_amount, selected.data.currency?.code)"/>
                <v-list-item title="Purpose" :subtitle="selected.data.purpose || '—'"/>
              </v-list>
              <v-divider class="my-3"/>
              <v-btn block variant="tonal" prepend-icon="mdi-crosshairs" @click="focusInterlinkage(selected.data.id)">Focus this interlinkage</v-btn>
            </template>

            <template v-else-if="selected.kind === 'interdep'">
              <div class="text-h6 mb-1">Interdependence</div>
              <v-chip class="mr-1 mb-2" label>{{ selected.data.type }}</v-chip>
              <v-chip class="mr-1 mb-2" :color="levelColor(selected.data.level)" label>{{ selected.data.level }}</v-chip>
              <v-list density="compact">
                <v-list-item title="Effective" :subtitle="fmtDate(selected.data.effective_date)"/>
                <v-list-item title="Expiry" :subtitle="fmtDate(selected.data.expiry_date)"/>
                <v-list-item title="Identifier" :subtitle="selected.data.interdependence_identifier"/>
              </v-list>
            </template>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, watch, reactive } from 'vue'
import { useRouter } from 'vue-router'
import * as joint from 'jointjs'
import 'jointjs/dist/joint.css'
// Optional: for auto-layout. Install dagre: npm i dagre
import dagre from 'dagre'

import { useApi } from '@/composables/useApi'

const router = useRouter()
const { resource, notify } = useApi()

const mode = ref('project') // 'project' | 'entity' | 'interlinkage'
const focusId = ref(null)
const focusItems = ref([])
const searchQuery = ref('')
const searchLoading = ref(false)

// --- Paged select state (no search) ---
const selectItems = ref([])
const selectLoading = ref(false)
const selectPage = ref(1)
const selectPageSize = 25         // tune as you like
const selectTotal = ref(0)

const selectLabel = computed(() => {
  if (mode.value === 'project') return 'Select a project'
  if (mode.value === 'entity') return 'Select a legal entity'
  return 'Select an interlinkage'
})
const hasMoreSelect = computed(() => selectItems.value.length < selectTotal.value)

function parseListResponse(resp) {
  const r = resp?.data ?? resp
  // items
  const items = Array.isArray(r) ? r
    : Array.isArray(r?.items) ? r.items
    : Array.isArray(r?.results) ? r.results
    : Array.isArray(r?.data) ? r.data
    : []
  // paging meta (optional)
  const total = Number(r?.total ?? items.length)
  const page  = Number(r?.page ?? selectPage.value)
  const pageSize = Number(r?.page_size ?? selectPageSize)
  return { items, total, page, pageSize }
}

function mapOption(kind, row) {
  if (kind === 'project') return { text: `${row.name}${row.code ? ` (${row.code})` : ''}`, value: row.id }
  if (kind === 'entity')  return { text: `${row.name}${row.country?.name ? ` — ${row.country.name}` : ''}`, value: row.id }
  if (kind === 'interlinkage') return { text: `Interlinkage #${row.id}${row.status ? ` — ${row.status}` : ''}`, value: row.id }
  return { text: String(row?.id ?? ''), value: row?.id }
}

async function getManyById(api, ids) {
  if (!ids?.length) return []
  const rows = await Promise.all(ids.map(async (id) => {
    try { const r = await api.get(id); return r?.data ?? r } catch (_) { return null }
  }))
  return rows.filter(Boolean)
}

function onlyIds(rows, ids) {
  const set = new Set(ids)
  return (rows || []).filter(r => set.has(r?.id))
}

async function fetchManyByIds(api, ids) {
  if (!ids?.length) return []
  // try list with common patterns first
  const tryParams = [
    { ids: ids.join(',') },
    { id__in: ids.join(',') },
    { id: ids },                 // some backends accept repeated params
  ]
  for (const p of tryParams) {
    try {
      const r = toItems(await api.list(p))
      if (Array.isArray(r) && r.length) return r
    } catch (_) { /* ignore and fall back */ }
  }
  // fallback: GET each id
  const rows = await Promise.all(ids.map(async (id) => {
    try { const r = await api.get(id); return r?.data ?? r }
    catch (_) { return null }
  }))
  return rows.filter(Boolean)
}

async function loadSelectPage({ reset = false } = {}) {
  selectLoading.value = true
  try {
    if (reset) {
      selectPage.value = 1
      selectItems.value = []
      selectTotal.value = 0
    }

    // choose API by mode
    const params = { page: selectPage.value, page_size: selectPageSize }
    const resp = mode.value === 'project'
      ? await prjApi.list(params)
      : mode.value === 'entity'
      ? await leApi.list(params)
      : await ilApi.list(params)

    const { items, total } = parseListResponse(resp)
    const mapped = items.map(r => mapOption(mode.value, r))

    selectItems.value = reset ? mapped : selectItems.value.concat(mapped)
    selectTotal.value = total
  } catch (e) {
    console.error('loadSelectPage error', e)
    notify.error('Failed to load options')
  } finally {
    selectLoading.value = false
  }
}

function loadMoreSelect() {
  if (!hasMoreSelect.value) return
  selectPage.value += 1
  loadSelectPage({ reset: false })
}


const filters = reactive({ level: null, type: null })

const ctx = reactive({
  project: { showEntities: true, showInterdeps: true },
  entity:  { showProjects: true, showInterdeps: true, role: 'all' }, // all | sponsor | counterparty | both
  interlinkage: { showInterdeps: true }
})

const focusLabel = computed(() => {
  if (mode.value === 'project') return 'Find a project'
  if (mode.value === 'entity') return 'Find a legal entity'
  return 'Find an interlinkage'
})

// Reuse your resource() factory; support backend query params
async function searchApi(kind, q) {
  if (!q || q.length < 2) return []
  if (kind === 'project')  return toItems(await prjApi.list({ q, limit: 10 }))
  if (kind === 'entity')   return toItems(await leApi.list({ q, limit: 10 }))
  if (kind === 'interlinkage') return toItems(await ilApi.list({ q, limit: 10 }))
  return []
}

function mapToItems(kind, rows) {
  if (kind === 'project') return rows.map(r => ({ text: `${r.name} ${r.code ? `(${r.code})` : ''}`, value: r.id }))
  if (kind === 'entity')  return rows.map(r => ({ text: `${r.name} — ${r.country?.name ?? ''}`.trim(), value: r.id }))
  if (kind === 'interlinkage') return rows.map(r => ({ text: `Interlinkage #${r.id} — ${r.status ?? ''}`.trim(), value: r.id }))
  return []
}

const onSearch = async (q) => {
  searchQuery.value = q ?? ''
  if (searchQuery.value.length < 2) { focusItems.value = []; return }
  try {
    searchLoading.value = true
    const rows = await searchApi(mode.value, searchQuery.value)
    focusItems.value = mapToItems(mode.value, rows)
  } catch (e) {
    console.error('search error', e)
    focusItems.value = []
  } finally {
    searchLoading.value = false
  }
}

// --- Focus jumpers from Details ---
function focusProject(id) { mode.value = 'project'; focusId.value = id; applyFocus() }
function focusEntity(id) { mode.value = 'entity'; focusId.value = id; applyFocus() }
function focusInterlinkage(id) { mode.value = 'interlinkage'; focusId.value = id; applyFocus() }

// --- Fetch only what's needed for the selected focus ---
function buildInterdepParams({ interlinkageIds = null, interlinkageId = null } = {}) {
  const p = {}
  if (interlinkageId) p.interlinkage_id = interlinkageId
  if (interlinkageIds && interlinkageIds.length) p.interlinkage_ids = interlinkageIds.join(',')

  // Only add when selected (avoid undefined/null/"")
  if (filters.level) p.level = filters.level
  if (filters.type)  p.type  = filters.type

  return p
}

async function fetchContext() {
  // Clear caches to the *focused subset*
  cache.entities = {}
  cache.projects = {}
  cache.interlinkages = {}
  cache.interdeps = {}

  if (!focusId.value) return

  if (mode.value === 'project') {
    // 1) Project
    const prj = await prjApi.get(focusId.value)
    const project = prj?.data ?? prj
    cache.projects[project.id] = project

    // 2) Interlinkages for this project
    const ils = toItems(await ilApi.list({ project_id: project.id }))
    ils.forEach(i => (cache.interlinkages[i.id] = i))

    // 3) Legal parties for those interlinkages (only if toggled)
    if (ctx.project.showEntities && ils.length) {
      const entityIds = Array.from(new Set(
        ils.flatMap(i => [i.sponsor_id, i.counterparty_id]).filter(Boolean)
      ))
      // Fan-out GET by id (no chance to “fetch all”)
      const ents = await getManyById(leApi, entityIds)
      ents.forEach(e => (cache.entities[e.id] = e))
    }

    // 4) Interdependencies (toggle + filter widgets reuse your existing filters)
    if (ctx.project.showInterdeps && ils.length) {
      const ilIds = ils.map(i => i.id)
      let deps = []
      try {
        // Try server-side list, but FILTER RESULT locally to IL set
        const r = toItems(await depApi.list(buildInterdepParams({ interlinkageIds: ilIds })))
        deps = r.filter(d => ilIds.includes(d?.interlinkage_id))
      } catch (_) { deps = [] }

      // If still empty, fan-out per IL
      if (!deps.length) {
        deps = (await Promise.all(ilIds.map(async (id) => {
          try {
            const rr = toItems(await depApi.list(buildInterdepParams({ interlinkageId: id })))
            return rr.filter(d => d?.interlinkage_id === id)
          } catch (_) { return [] }
        }))).flat()
      }
      deps.forEach(d => (cache.interdeps[d.id] = d))

    }
  }

  else if (mode.value === 'entity') {
    // 1) Entity
    const ent = await leApi.get(focusId.value)
    const entity = ent?.data ?? ent
    cache.entities[entity.id] = entity

    // 2) Interlinkages where entity is sponsor / counterparty (respect role filter)
    let ils = []
    if (ctx.entity.role === 'all' || ctx.entity.role === 'sponsor' || ctx.entity.role === 'both') {
      ils = ils.concat(toItems(await ilApi.list({ sponsor_id: entity.id })))
    }
    if (ctx.entity.role === 'all' || ctx.entity.role === 'counterparty' || ctx.entity.role === 'both') {
      ils = ils.concat(toItems(await ilApi.list({ counterparty_id: entity.id })))
    }
    // If 'both', keep only where same entity is both sides
    if (ctx.entity.role === 'both') {
      ils = ils.filter(i => i.sponsor_id === entity.id && i.counterparty_id === entity.id)
    }
    // Dedup
    const byId = new Map(ils.map(i => [i.id, i]))
    ils = Array.from(byId.values())
    ils.forEach(i => (cache.interlinkages[i.id] = i))

    // 3) Projects (toggle)
    if (ctx.entity.showProjects && ils.length) {
      const prjIds = Array.from(new Set(ils.map(i => i.project_id).filter(Boolean)))
      const prjs = await getManyById(prjApi, prjIds)
      prjs.forEach(p => (cache.projects[p.id] = p))
    }

    // 4) Interdependencies (toggle + filters)
    if (ctx.entity.showInterdeps && ils.length) {

      const ilIds = ils.map(i => i.id)
      let deps = []
      try {
        const r = toItems(await depApi.list(buildInterdepParams({ interlinkageIds: ilIds })))
        deps = r.filter(d => ilIds.includes(d?.interlinkage_id))
      } catch (_) { deps = [] }

      if (!deps.length) {
        deps = (await Promise.all(ilIds.map(async (id) => {
          try {
            const rr = toItems(await depApi.list(buildInterdepParams({ interlinkageId: id })))
            return rr.filter(d => d?.interlinkage_id === id)
          } catch (_) { return [] }
        }))).flat()
      }
      deps.forEach(d => (cache.interdeps[d.id] = d))
    }
  }

  else if (mode.value === 'interlinkage') {
    // 1) Interlinkage
    const il = await ilApi.get(focusId.value)
    const inter = il?.data ?? il
    cache.interlinkages[inter.id] = inter

    // 2) Project + entities
    if (inter.project_id) {
      const prj = await prjApi.get(inter.project_id)
      const project = prj?.data ?? prj
      cache.projects[project.id] = project
    }
    if (inter.sponsor_id) {
      const sp = await leApi.get(inter.sponsor_id)
      const sponsor = sp?.data ?? sp
      cache.entities[sponsor.id] = sponsor
    }
    if (inter.counterparty_id) {
      const cp = await leApi.get(inter.counterparty_id)
      const cpty = cp?.data ?? cp
      cache.entities[cpty.id] = cpty
    }

    // 3) Interdependencies (toggle + filters)
    if (ctx.interlinkage.showInterdeps) {
      const deps = toItems(await depApi.list(
        buildInterdepParams({ interlinkageId: inter.id })
      ))
      deps.forEach(d => (cache.interdeps[d.id] = d))
    }
  }
}

// Build graph only from small focused caches
function buildGraphForContext() {
  graph.clear()

  const nodeMap = new Map()

  // Projects
  Object.values(cache.projects).forEach(p => nodeMap.set(`project:${p.id}`, makeProjectCell(p)))
  // Entities
  Object.values(cache.entities).forEach(e => nodeMap.set(`entity:${e.id}`, makeEntityCell(e)))
  // Interlinkages
  Object.values(cache.interlinkages).forEach(il => {
    const ilCell = makeInterlinkageCell(il)
    nodeMap.set(`il:${il.id}`, ilCell)

    const sponsorNode = nodeMap.get(`entity:${il.sponsor_id}`)
    const cptyNode    = nodeMap.get(`entity:${il.counterparty_id}`)
    const prjNode     = nodeMap.get(`project:${il.project_id}`)

    if (sponsorNode) makeLink(sponsorNode, ilCell, { stroke: '#2E7D32', width: 2, label: 'sponsor' })
    if (cptyNode)    makeLink(cptyNode, ilCell,    { stroke: '#B71C1C', width: 2, label: 'counterparty' })
    if (prjNode)     makeLink(ilCell, prjNode,     { stroke: '#0D47A1', width: 2, label: 'project' })
  })

  // Interdeps as nodes (respect existing filters)
  Object.values(cache.interdeps).forEach(dep => {
    if (filters.level && dep.level !== filters.level) return
    if (filters.type && dep.type !== filters.type) return

    const ilNode = nodeMap.get(`il:${dep.interlinkage_id}`)
    if (!ilNode) return

    const depNode = makeInterdepCell(dep)
    nodeMap.set(`dep:${dep.id}`, depNode)

    makeLink(ilNode, depNode, { stroke: '#6A1B9A', width: 2, label: dep.type || 'interdep', typeTag: 'interdep-link-il', data: dep })

    const il = cache.interlinkages[dep.interlinkage_id]
    const prjTargetId = dep.project_id || il?.project_id
    const prjNode = prjTargetId ? nodeMap.get(`project:${prjTargetId}`) : null
    if (prjNode) makeLink(depNode, prjNode, { dashed: true, stroke: '#6A1B9A', label: 'project', typeTag: 'interdep-link-project', data: dep })

    const sponsorNode = il ? nodeMap.get(`entity:${il.sponsor_id}`) : null
    const cptyNode    = il ? nodeMap.get(`entity:${il.counterparty_id}`) : null
    if (sponsorNode) makeLink(depNode, sponsorNode, { dashed: true, stroke: '#6A1B9A', label: 'sponsor', typeTag: 'interdep-link-entity', data: dep })
    if (cptyNode)    makeLink(depNode, cptyNode,    { dashed: true, stroke: '#6A1B9A', label: 'counterparty', typeTag: 'interdep-link-entity', data: dep })
  })

  applyLayeredLayout()
}

// Apply focus
async function applyFocus() {
  if (!focusId.value) { notify.warn('Pick something to focus on'); return }
  loading.value = true
  try {
    await fetchContext()
    buildGraphForContext()
    selected.value = null
    fitToContent()
  } catch (e) {
    console.error('focus error', e)
    notify.error('Failed to load focus graph')
  } finally {
    loading.value = false
  }
}
watch([
  mode,
  () => ctx.project.showEntities, () => ctx.project.showInterdeps,
  () => ctx.entity.showProjects,  () => ctx.entity.showInterdeps, () => ctx.entity.role,
  () => ctx.interlinkage.showInterdeps,
  () => filters.level, () => filters.type
], () => { if (focusId.value) applyFocus() })

// APIs
const leApi  = resource('legal-entities')
const prjApi = resource('projects')
const ilApi  = resource('interlinkages')
const depApi = resource('interdependences')

// UI state
const paperEl = ref(null)
const navigatorEl = ref(null)
const loading = ref(false)
const selected = ref(null)

const search = reactive({ q: '' })
const layers = reactive({ entities: true, projects: true, interlinkages: true, interdeps: false })

const levelItems = ['low','medium','high','critical']
const typeItems = [
  'ownership','credit','guarantee','management','technical','juridical','legal','contractual','equity','funding','governance','strategic','other'
]

// JointJS surfaces
let graph, paper, scroller, navigator

// Local caches (id -> row)
const cache = reactive({
  entities: {},
  projects: {},
  interlinkages: {},
  interdeps: {}
})

function fmtDate(d) {
  if (!d) return '—'
  try {
    const dt = typeof d === 'string' ? new Date(d) : d
    return dt.toISOString().slice(0,10)
  } catch { return String(d) }
}
function fmtAmount(x, ccy) {
  if (x == null) return '—'
  return new Intl.NumberFormat(undefined, { style: 'currency', currency: ccy || 'EUR', maximumFractionDigits: 2 }).format(Number(x))
}
function levelColor(level) {
  const map = { low: 'grey', medium: 'amber', high: 'orange', critical: 'red' }
  return map[level] || 'grey'
}
function entityFlags(e) {
  const flags = []
  if (e.is_sanctioned) flags.push('Sanctioned')
  if (e.is_pep) flags.push('PEP')
  if (e.aml_risk) flags.push(`AML: ${e.aml_risk}`)
  return flags.join(' · ') || '—'
}

function openInterlinkage(id) {
  router.push({ name: 'interlinkages', params: { id } })
}

function toItems(resp) {
  // gère axios/fetch et divers formats
  const r = resp?.data ?? resp;               // axios: resp.data
  if (Array.isArray(r)) return r;             // déjà une liste
  if (Array.isArray(r?.items)) return r.items;
  if (Array.isArray(r?.results)) return r.results;
  if (Array.isArray(r?.data)) return r.data;  // certains back renvoient { data: [...] }
  return [];                                  // fallback
}

async function fetchAll() {
  loading.value = true
  try {
    const [entitiesR, projectsR, interlinkagesR, interdepsR] = await Promise.all([
      leApi.list(),
      prjApi.list(),
      ilApi.list(),
      depApi.list()
    ])

    const entities      = toItems(entitiesR)
    const projects      = toItems(projectsR)
    const interlinkages = toItems(interlinkagesR)
    const interdeps     = toItems(interdepsR)

    cache.entities = Object.fromEntries(entities.map(e => [e.id, e]))
    cache.projects = Object.fromEntries(projects.map(p => [p.id, p]))
    cache.interlinkages = Object.fromEntries(interlinkages.map(i => [i.id, i]))
    cache.interdeps = Object.fromEntries(interdeps.map(d => [d.id, d]))
  } catch (err) {
    console.error('fetchAll error:', err)
    notify.error('Failed to load data')
  } finally {
    loading.value = false
  }
}
function makeEntityCell(e) {
  const cell = new joint.shapes.standard.Rectangle()
  cell.resize(180, 60)
  cell.attr({
    body: { fill: '#E6F4EA', stroke: '#1B5E20', rx: 12, ry: 12 },
    label: { text: e.name, fontSize: 12, fontWeight: 600, fill: '#1B5E20', lineHeight: 1.3 }
  })
  cell.set('typeTag', 'entity')
  cell.set('data', e)
  cell.addTo(graph)
  return cell
}

function makeProjectCell(p) {
  const cell = new joint.shapes.standard.Rectangle()
  cell.resize(200, 60)
  cell.attr({
    body: { fill: '#E3F2FD', stroke: '#0D47A1', rx: 12, ry: 12 },
    label: { text: p.name, fontSize: 12, fontWeight: 600, fill: '#0D47A1', lineHeight: 1.3 }
  })
  cell.set('typeTag', 'project')
  cell.set('data', p)
  cell.addTo(graph)
  return cell
}

function makeInterlinkageCell(il) {
  const rh = new joint.shapes.standard.Polygon()
  rh.resize(140, 80)
  rh.attr({
    body: {
      refPoints: '0,10 10,0 20,10 10,20', fill: '#FFF3E0', stroke: '#E65100'
    },
    label: { text: `IL #${il.id}\n${il.status}`, fontSize: 11, fill: '#BF360C' }
  })
  rh.set('typeTag', 'interlinkage')
  rh.set('data', il)
  rh.addTo(graph)
  return rh
}

// New: explicit Interdependence node (purple ellipse)
function makeInterdepCell(dep) {
  const node = new joint.shapes.standard.Ellipse()
  node.resize(140, 60)
  node.attr({
    body: { fill: '#F3E5F5', stroke: '#6A1B9A' },
    label: { text: `${dep.type || 'interdep'}\n${dep.level || ''}`.trim(), fontSize: 11, fontWeight: 600, fill: '#4A148C' }
  })
  node.set('typeTag', 'interdepNode')
  node.set('data', dep)
  node.addTo(graph)
  return node
}

function makeLink(source, target, opts = {}) {
  const link = new joint.shapes.standard.Link()
  link.source(source)
  link.target(target)
  link.attr({ line: { stroke: opts.stroke || '#607D8B', strokeWidth: opts.width || 1.5, targetMarker: { type: 'classic', stroke: opts.stroke || '#607D8B', fill: opts.stroke || '#607D8B' } } })
  if (opts.dashed) link.attr('line/strokeDasharray', '4 2')
  if (opts.label) link.appendLabel({ attrs: { text: { text: opts.label, fontSize: 11 } }, position: .5 })
  link.set('typeTag', opts.typeTag || 'link')
  link.set('data', opts.data || null)
  link.addTo(graph)
  return link
}

// Old dagre layout kept for reference; not used by default
function applyLayout() {
  const g = new dagre.graphlib.Graph()
  g.setGraph({ rankdir: 'LR', nodesep: 80, ranksep: 140 })
  g.setDefaultEdgeLabel(() => ({}))
  const cells = graph.getElements()
  cells.forEach((c) => g.setNode(c.id, { width: c.size().width, height: c.size().height }))
  graph.getLinks().forEach((l) => g.setEdge(l.get('source').id, l.get('target').id))
  dagre.layout(g)
  cells.forEach((c) => { const n = g.node(c.id); if (n) c.position(n.x - c.width/2, n.y - c.height/2) })
  fitToContent()
}

// New: deterministic 4-column layered layout
// Columns: 0=Entities | 1=Interlinkages | 2=Interdeps | 3=Projects
function applyLayeredLayout() {
  const PAD_X = 260, PAD_Y = 110, ORIGIN_X = 80, ORIGIN_Y = 60
  const els = graph.getElements()
  const entities = els.filter(e => e.get('typeTag') === 'entity')
  const interls  = els.filter(e => e.get('typeTag') === 'interlinkage')
  const deps     = els.filter(e => e.get('typeTag') === 'interdepNode')
  const projects = els.filter(e => e.get('typeTag') === 'project')

  const ilById = new Map(interls.map(il => [il.id, il]))

  // Group by interlinkage for stable rows
  const groups = []
  interls.forEach(il => {
    const data = il.get('data') || {}
    const sponsor = entities.find(e => e.get('data')?.id === data.sponsor_id)
    const cpty    = entities.find(e => e.get('data')?.id === data.counterparty_id)
    const prj     = projects.find(p => p.get('data')?.id === data.project_id)
    const childrenDeps = deps.filter(d => d.get('data')?.interlinkage_id === data.id)
    groups.push({ sponsor, cpty, il, deps: childrenDeps, prj })
  })

  let row = 0
  const placed = new Set()
  function place(cell, col, r) {
    if (!cell) return
    const { width, height } = cell.size()
    const x = ORIGIN_X + col * PAD_X
    const y = ORIGIN_Y + r * PAD_Y
    cell.position(x - width/2, y - height/2)
    placed.add(cell.id)
  }

  groups.forEach(g => {
    const r = row++
    place(g.sponsor, 0, r)
    place(g.cpty,    0, r + 0.5)
    place(g.il,      1, r)
    // Stack all interdep nodes for this IL on sub-rows
    let k = 0
    g.deps.forEach(d => { place(d, 2, r + k * 0.4); k += 1 })
    place(g.prj,     3, r)
  })

  // Place remaining loose nodes (if any)
  let r0 = Math.ceil(row + 1)
  entities.forEach(e => { if (!placed.has(e.id)) place(e, 0, r0++ ) })
  projects.forEach(p => { if (!placed.has(p.id)) place(p, 3, r0++ ) })
  deps.forEach(d => { if (!placed.has(d.id)) place(d, 2, r0++ ) })

  fitToContent()
}


function buildGraph() {
  graph.clear()

  // Build layers
  const nodeMap = new Map()

  // 1) Projects
  if (layers.projects) {
    Object.values(cache.projects).forEach(p => {
      const cell = makeProjectCell(p)
      nodeMap.set(`project:${p.id}`, cell)
    })
  }

  // 2) Entities
  if (layers.entities) {
    Object.values(cache.entities).forEach(e => {
      const cell = makeEntityCell(e)
      nodeMap.set(`entity:${e.id}`, cell)
    })
  }

  // 3) Interlinkages (diamond) + edges to sponsor/cpty/project
  if (layers.interlinkages) {
    Object.values(cache.interlinkages).forEach(il => {
      const ilCell = makeInterlinkageCell(il)
      nodeMap.set(`il:${il.id}`, ilCell)

      const sponsorNode = nodeMap.get(`entity:${il.sponsor_id}`)
      const cptyNode    = nodeMap.get(`entity:${il.counterparty_id}`)
      const prjNode     = nodeMap.get(`project:${il.project_id}`)

      if (sponsorNode) makeLink(sponsorNode, ilCell, { stroke: '#2E7D32', width: 2, label: 'sponsor' })
      if (cptyNode)    makeLink(cptyNode, ilCell,    { stroke: '#B71C1C', width: 2, label: 'counterparty' })
      if (prjNode)     makeLink(ilCell, prjNode,     { stroke: '#0D47A1', width: 2, label: 'project' })
    })
  }

  // 4) Interdependencies as SEPARATE NODES
if (layers.interdeps) {
  Object.values(cache.interdeps).forEach(dep => {
    if (filters.level && dep.level !== filters.level) return
    if (filters.type && dep.type !== filters.type) return

    const ilNode = nodeMap.get(`il:${dep.interlinkage_id}`)
    if (!ilNode) return

    // Create an interdep node
    const depNode = makeInterdepCell(dep)
    nodeMap.set(`dep:${dep.id}`, depNode)

    // Solid link: Interlinkage -> Interdep
    makeLink(ilNode, depNode, { stroke: '#6A1B9A', width: 2, label: dep.type || 'interdep', typeTag: 'interdep-link-il', data: dep })

    // Dashed links out of interdep: to project and to involved entities (if any)
    const il = cache.interlinkages[dep.interlinkage_id]

    // to Project (dep.project_id if set, otherwise IL.project)
    const prjTargetId = dep.project_id || il?.project_id
    const prjNode = prjTargetId ? nodeMap.get(`project:${prjTargetId}`) : null
    if (prjNode) {
      makeLink(depNode, prjNode, { dashed: true, stroke: '#6A1B9A', label: 'project', typeTag: 'interdep-link-project', data: dep })
    }

    // to Entities: sponsor & counterparty (via IL)
    const sponsorNode = il ? nodeMap.get(`entity:${il.sponsor_id}`) : null
    const cptyNode    = il ? nodeMap.get(`entity:${il.counterparty_id}`) : null
    if (sponsorNode) makeLink(depNode, sponsorNode, { dashed: true, stroke: '#6A1B9A', label: 'sponsor', typeTag: 'interdep-link-entity', data: dep })
    if (cptyNode)    makeLink(depNode, cptyNode,    { dashed: true, stroke: '#6A1B9A', label: 'counterparty', typeTag: 'interdep-link-entity', data: dep })
  })
}

applyLayeredLayout()
}

async function reload() {
  await fetchAll()
  buildGraph()
}

function initPaper() {
  // Idempotent: nettoie l'ancien paper si ré-init (HMR/onglet/vue keep-alive)
  if (paper) {
    try { paper.remove() } catch (_) {}
    paper = null
  }
  if (paperEl.value) paperEl.value.innerHTML = ''

  graph = new joint.dia.Graph()

  const hasPlus = !!(joint.ui && joint.ui.PaperScroller)

  if (hasPlus) {
    // JointJS+ : Paper sans el direct, monté via PaperScroller
    paper = new joint.dia.Paper({
      model: graph,
      width: '100%',
      height: 700,
      gridSize: 10,
      drawGrid: true,
      background: { color: '#FAFAFA' },
      interactive: { linkMove: false }
    })
    scroller = new joint.ui.PaperScroller({ paper, autoResizePaper: true })
    paperEl.value.appendChild(scroller.el)
    scroller.render().center()

    if (navigatorEl?.value && joint.ui.Navigator) {
      navigator = new joint.ui.Navigator({
        paperScroller: scroller, width: 240, height: 140, padding: 10, zoomOptions: { max: 1 }
      })
      navigatorEl.value.innerHTML = ''
      navigatorEl.value.appendChild(navigator.el)
      navigator.render()
    }
  } else {
    // OPEN-SOURCE : on **monte directement** le Paper dans le conteneur
    paper = new joint.dia.Paper({
      el: paperEl.value,            // <— ceci suffit, PAS de appendChild
      model: graph,
      width: '100%',
      height: 700,
      gridSize: 10,
      drawGrid: true,
      background: { color: '#FAFAFA' },
      interactive: { linkMove: false }
    })

    // Pan/zoom basique
    let isPanning = false, panStart = { x: 0, y: 0 }, origin = { x: 0, y: 0 }
    paper.on('blank:pointerdown', (evt, x, y) => {
      isPanning = true
      panStart = { x, y }
      origin = paper.options.origin || { x: 0, y: 0 }
    })
    paper.on('cell:pointerup blank:pointerup', () => (isPanning = false))
    paper.on('blank:pointermove', (evt, x, y) => {
      if (!isPanning) return
      const dx = x - panStart.x
      const dy = y - panStart.y
      paper.setOrigin(origin.x + dx, origin.y + dy)
    })
    paper.el.addEventListener('wheel', (e) => {
      e.preventDefault()
      const cur = paper.scale().sx
      const next = e.deltaY < 0 ? Math.min(cur * 1.1, 2) : Math.max(cur / 1.1, 0.2)
      paper.scale(next, next)
    })
  }

  // Sélection (commun)
  paper.on('element:pointerdown', (view) => {
    selected.value = { kind: view.model.get('typeTag'), data: view.model.get('data') }
  })
  paper.on('link:pointerdown', (view) => {
    const tag = view.model.get('typeTag')
    selected.value = { kind: tag === 'interdep' || tag === 'interdepNode' ? 'interdep' : 'link', data: view.model.get('data') }
  })
}

function fitToContent() {
  if (scroller?.zoomToFit) {
    scroller.zoomToFit({ padding: 30, minScale: 0.2, maxScale: 2 })
    return
  }
  if (!paper) return
  if (typeof paper.scaleContentToFit === 'function') {
    paper.scaleContentToFit({ padding: 30 })
    return
  }
  const bbox = graph.getBBox(graph.getElements())
  if (!bbox || !isFinite(bbox.width) || !isFinite(bbox.height)) return
  const el = paper.el
  const vw = el.clientWidth || 1000
  const vh = el.clientHeight || 700
  const sx = (vw - 60) / bbox.width
  const sy = (vh - 60) / bbox.height
  const scale = Math.max(0.2, Math.min(2, Math.min(sx, sy)))
  paper.scale(scale, scale)
  const ox = (vw / scale - bbox.width) / 2 - bbox.x
  const oy = (vh / scale - bbox.height) / 2 - bbox.y
  paper.setOrigin(ox, oy)
}

watch(mode, () => {
  focusId.value = null
  loadSelectPage({ reset: true })
})

onMounted(() => {
  initPaper()
  loadSelectPage({ reset: true })
})

</script>

<style scoped>
.graph-wrapper { position: relative; overflow: hidden; }
.graph-paper { width: 100%; height: 700px; }
.graph-navigator { position: absolute; right: 16px; bottom: 16px; background: #fff; border-radius: 12px; box-shadow: 0 6px 16px rgba(0,0,0,0.15); overflow: hidden; }
</style>
