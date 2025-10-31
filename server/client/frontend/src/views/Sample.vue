<template>
  <v-container fluid class="py-4">
    <v-row class="mb-3" align="center" no-gutters>
      <v-col cols="12" md="12">
        <v-card rounded="xl" class="pa-3 d-flex align-center flex-wrap" elevation="2" style="gap:8px;">
          <!-- Mode -->
          <v-btn-toggle v-model="mode" rounded="xl" density="comfortable" divided>
            <v-btn value="project" prepend-icon="mdi-briefcase-outline">Project</v-btn>
            <v-btn value="entity" prepend-icon="mdi-domain">Legal entity</v-btn>
            <v-btn value="interlinkage" prepend-icon="mdi-vector-polyline">Interlinkage</v-btn>
          </v-btn-toggle>

          <!-- Focus selector (paged, no search) -->
          <v-select
            v-model="focusId"
            :items="selectItems"
            :loading="selectLoading"
            :label="selectLabel"
            clearable
            item-title="text"
            item-value="value"
            density="comfortable"
            variant="solo"
            class="flex-grow-1 inline-select"
            hide-details
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

          <v-btn color="primary" prepend-icon="mdi-crosshairs-gps" :loading="loading" @click="applyFocus">Load</v-btn>
          <v-btn variant="text" prepend-icon="mdi-fit-to-page-outline" @click="fitToContent">Fit</v-btn>
          <v-btn variant="text" prepend-icon="mdi-image" @click="downloadGraphPng">PNG</v-btn>
          <v-btn variant="text" prepend-icon="mdi-vector-square" @click="downloadGraphSvg">SVG</v-btn>

        </v-card>
      </v-col>

      <v-col cols="12" md="4" v-if="1==0">
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
          <!-- ======= Graph placeholder (no external libs) ======= -->
          <div ref="paperEl" class="graph-paper"></div>

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
            <div class="d-flex align-center mb-2">
              <v-icon class="mr-1">mdi-information-outline</v-icon> Select a node or a link.
            </div>
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

        <v-card rounded="xl" elevation="3" class="pa-0 mt-4">
          <v-toolbar density="comfortable" color="blue-grey-lighten-5">
            <v-toolbar-title class="text-subtitle-1 font-weight-bold">Analysis</v-toolbar-title>
            <v-spacer/>
            <v-select
              density="comfortable"
              variant="solo"
              class="flex-grow-1 inline-select"
              hide-details

              v-model="analysisKey"
              :items="analysisOptions"
              :disabled="!focusId || analysisOptions.length===0"
              item-title="text"
              item-value="value"
              :label="!focusId ? 'Pick a focus first' : ''"
            />
            <v-btn
              icon="mdi-help-circle-outline"
              variant="text"
              :disabled="analysisOptions.length===0"
              @click="helpOpen = true"
            />
          </v-toolbar>

          <div class="pa-4">
            <template v-if="!focusId">
              <div class="text-medium-emphasis d-flex align-center">
                <v-icon class="mr-2">mdi-information-outline</v-icon>
                Pick a Project / Legal entity / Interlinkage first.
              </div>
            </template>

            <template v-else-if="!analysisKey">
              <div class="text-medium-emphasis d-flex align-center">
                <v-icon class="mr-2">mdi-chart-bell-curve</v-icon>
                Choose an analysis case from the selector.
              </div>
            </template>

            <template v-else>
              <div class="d-flex align-center mb-2" style="gap:8px;">
                <div class="text-subtitle-1 font-weight-bold">{{ selectedAnalysis?.title }}</div>
                <v-chip density="comfortable" label color="blue-grey-lighten-4" class="ml-1">
                  POV: {{ povLabel }}
                </v-chip>
              </div>
              <div class="text-body-2 mb-3">{{ selectedAnalysis?.short }}</div>

              <!-- Optional inputs per analysis (stub, adapt later) -->
              <div v-if="selectedAnalysis">
                <template v-if="selectedAnalysis.key === 'project_concentration_by_dependency'">
                  <div class="d-flex align-center flex-wrap" style="gap:8px;">
                    <v-select
                      v-model="analysisParams.groupBy"
                      :items="[
                        { title:'Identifier', value:'identifier' },
                        { title:'Type', value:'type' },
                        { title:'Identifier + Type', value:'id_type' },
                        { title:'Type + Level', value:'type_level' }
                      ]"
                      label="Group by"
                      density="comfortable"
                      style="min-width: 200px"
                      hide-details
                    />
                    <v-text-field
                      v-model.number="analysisParams.minCluster"
                      type="number"
                      min="2"
                      label="Min cluster size"
                      density="comfortable"
                      style="max-width: 180px"
                      hide-details
                    />
                    <v-select
                      v-model="analysisParams.levels"
                      :items="['low','medium','high','critical']"
                      label="Level filter (optional)"
                      multiple chips clearable
                      density="comfortable"
                      style="min-width: 260px"
                      hide-details
                    />
                  </div>
                </template>

                <!-- Keep generic dateRange for other cases -->
                <div v-else-if="selectedAnalysis?.needs?.dateRange" class="d-flex align-center flex-wrap" style="gap:8px;">
                  <v-text-field v-model="analysisParams.from" label="From (YYYY-MM-DD)" density="comfortable" style="max-width: 180px;" hide-details />
                  <v-text-field v-model="analysisParams.to" label="To (YYYY-MM-DD)" density="comfortable" style="max-width: 180px;" hide-details />
                </div>
              </div>

              <div class="d-flex align-center mt-3" style="gap:8px;">
                <v-btn color="primary" prepend-icon="mdi-play" :loading="analysisLoading" @click="runAnalysis">
                  Run
                </v-btn>
                <v-btn variant="text" prepend-icon="mdi-text-box-search-outline" @click="helpOpen = true">
                  Learn more
                </v-btn>
              </div>

              <!-- Result placeholder -->
              <div class="mt-4">
                <div v-if="analysisResult" class="text-body-2">
                  <div class="text-medium-emphasis mb-1">Result</div>
                  <pre class="analysis-pre">{{ JSON.stringify(analysisResult, null, 2) }}</pre>
                </div>
                <div v-else class="text-medium-emphasis">
                  The output will appear here after running the analysis.
                </div>
              </div>
            </template>
          </div>
        </v-card>

        <!-- Help dialog -->
        <v-dialog v-model="helpOpen" max-width="780">
  <v-card>
    <v-card-title class="d-flex align-center">
      <v-icon class="mr-2">mdi-help-circle-outline</v-icon>
      Analysis catalog — {{ povLabel }}
      <v-spacer/>
      <v-btn icon="mdi-close" variant="text" @click="helpOpen=false"/>
    </v-card-title>
    <v-divider/>
    <v-card-text style="max-height: 70vh; overflow:auto;">
      <div v-if="analysisOptions.length===0" class="text-medium-emphasis">
        No analysis cases available for this POV.
      </div>
      <div v-else class="d-flex flex-column" style="gap:16px;">
        <div v-for="opt in analysisOptions" :key="opt.value" class="help-block">
          <div class="text-subtitle-2 font-weight-bold">{{ opt.text }}</div>
          <div class="text-caption mb-2">POV: {{ opt.pov.join(', ') }}</div>
          <div class="text-body-2">{{ opt.long }}</div>
        </div>
      </div>
    </v-card-text>
    <v-divider/>
    <v-card-actions>
      <v-spacer/>
      <v-btn color="primary" variant="tonal" @click="helpOpen=false">Close</v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
      </v-col>
    </v-row>
  </v-container>

  <ConcentrationOnSharedDependencies

    v-model:open="concentrationOnSharedDependenciesAnalysisDialogOpen"
    :title="concentrationOnSharedDependenciesAnalysisDialogTitle"
    :payload="concentrationOnSharedDependenciesAnalysisDialogPayload"
    :context="concentrationOnSharedDependenciesAnalysisDialogContext"
  />

  <ExpiryMonitoring
    v-model:open="expiryMonitoringDialogOpen"
    :title="expiryMonitoringDialogTitle"
    :payload="expiryMonitoringDialogPayload"
    :context="expiryMonitoringDialogContext"
  />
</template>

<script setup>
import ConcentrationOnSharedDependencies from '@/views/ConcentrationOnSharedDependencies.vue'
import ExpiryMonitoring from '@/views/ExpiryMonitoring.vue'

import { ref, computed, onMounted, watch, reactive, defineComponent } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'
import GraphPlaceholder from './GraphPlaceholder.vue'
import { useFocusBundle } from '@/composables/useFocusBundle'
import * as joint from 'jointjs'
import 'jointjs/dist/joint.css'
import dagre from 'dagre'
import { AdaptiveCardModel } from '@/graph/adaptive-card';
import { shapesNS } from '@/graph/adaptive-card'
const { dia } = joint;

const { fetchFocusBundle } = useFocusBundle()

/*************** ANALYSIS ***********************/

const concentrationOnSharedDependenciesAnalysisDialogOpen = ref(false)
const concentrationOnSharedDependenciesAnalysisDialogTitle = ref('Analysis')
const concentrationOnSharedDependenciesAnalysisDialogPayload = ref(null)

const expiryMonitoringDialogOpen = ref(false)
const expiryMonitoringDialogTitle = ref('Expiry monitoring')
const expiryMonitoringDialogPayload = ref(null)

// Context used by the dialog to resolve labels (you already build these in cache/refCache)
const expiryMonitoringDialogContext = ref({
  interlinkages: {},  // by id (optional here)
  entities: {},       // by id
  currencies: {},     // by id
})

function iso(d) {
  // Accepts Date | string | null ; returns 'YYYY-MM-DD'
  if (!d) return null
  const dt = (d instanceof Date) ? d : new Date(d)
  const y = dt.getFullYear()
  const m = String(dt.getMonth() + 1).padStart(2, '0')
  const day = String(dt.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

async function runExpiryMonitoring(payload) {
  return await postJSON('/api/analysis/expiry-monitoring', payload)
}


const concentrationOnSharedDependenciesAnalysisDialogContext = ref({
  interlinkages: {},  // by id
  entities: {},       // by id
  currencies: {},     // by id
})

async function postJSON(url, payload) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return await res.json()
}
async function runConcentrationOnSharedDeps(payload) {
  return await postJSON('/api/analysis/concentration/shared-dependencies', payload)
}

const ANALYSIS_CASES = [
  // -------- Project-centric --------
  {
    key: 'project_dashboard',
    pov: ['project'],
    title: 'Project interconnection dashboard',
    short: 'All interlinkages & interdependences tied to this project, with type/level distribution.',
    long: 'Build a full view of the selected project: list interlinkages, entities involved, and all interdependences. Show counts by type/level, identify critical dependencies, and spotlight expiries within N days.',
  },
  {
    key: 'project_concentration_by_dependency',
    pov: ['project','interlinkage'],
    title: 'Concentration on shared dependencies',
    short: 'Find clusters of deals relying on the same dependency (e.g., vendor, guarantee).',
    long: 'Group interlinkages within the project by interdependence_identifier/type. Aggregate exposure (EAD/RWA) to reveal single points of failure and correlated risk.',
  },
  {
    key: 'project_expiry_monitoring',
    pov: ['project','interlinkage'],
    title: 'Expiry monitoring',
    short: 'Upcoming expiry of guarantees/contractual/technical interdependences.',
    long: 'Filter dependencies by expiry within a look-ahead window to surface renewal actions and owners.',
    needs: { dateRange: true }
  },

  // -------- Entity-centric --------
  {
    key: 'entity_connected_clients',
    pov: ['entity','interlinkage'],
    title: 'Group of connected clients',
    short: 'Aggregate exposures across entities linked by ownership/guarantee/control.',
    long: 'Form regulatory “connected client” groups using interdependences. Sum EAD/RWA across the group and compare to internal/regulatory thresholds.',
  },
  {
    key: 'entity_guarantee_network',
    pov: ['entity','interlinkage'],
    title: 'Cross-guarantee network',
    short: 'Detect meshes/loops in guarantees and rank entities by systemic impact.',
    long: 'Filter type=guarantee; compute cycles and centrality to identify structural weaknesses or circular support patterns.',
  },
  {
    key: 'entity_sanction_propagation',
    pov: ['entity'],
    title: 'Sanction/PEP propagation',
    short: 'Trace indirect exposure from sanctioned/PEP entities via dependency paths.',
    long: 'Starting from a flagged entity, traverse ownership/governance links to discover indirect exposure. Rank by cumulative EAD affected.',
  },

  // -------- Interlinkage-centric --------
  {
    key: 'il_risk_profile',
    pov: ['interlinkage'],
    title: 'Deal risk profile (edge-aware)',
    short: 'List active interdependences (type/level/dates) with risk notes for this deal.',
    long: 'Snapshot the deal’s dependency surface: guarantees, ownership, contractual, and technical edges. Show materiality (level) and effective/expiry windows.',
  },
  {
    key: 'il_contagion',
    pov: ['interlinkage','entity'],
    title: 'Contagion from this deal',
    short: 'If this deal is impacted, which others are at risk via shared dependencies?',
    long: 'For every interdependence on this deal, find other interlinkages sharing the same dependency identifier or type. Summarize impacted count and exposures.',
  },
  {
    key: 'il_vs_exposure_trend',
    pov: ['interlinkage'],
    title: 'Exposure trend vs dependency level',
    short: 'Overlay EAD/MTM time series with dependency materiality.',
    long: 'Correlate changes in EAD/MTM with presence of high/critical dependencies over time to detect sensitivity.',
    needs: { dateRange: true }
  },

  // -------- Multi-POV utilities --------
  {
    key: 'concentration_heatmap',
    pov: ['project','entity','interlinkage'],
    title: 'Concentration heatmap',
    short: 'Counts & EAD by dependency type×level, sector, and country.',
    long: 'Aggregate dependency counts and exposures to build heatmaps for portfolio slices: type×level, sector×country. Great as a starting KPI board.',
  },
  {
    key: 'operational_resilience_register',
    pov: ['project','entity','interlinkage'],
    title: 'Operational resilience register',
    short: 'Inventory of critical dependencies with owners and renewal actions.',
    long: 'Keep an actionable list of active critical interdependences (level=critical), assign owners, and drive renewals or mitigations.',
  },
]

/* ---------- Reactive state for Analysis ---------- */
const helpOpen = ref(false)
const analysisKey = ref(null)
const analysisLoading = ref(false)
const analysisResult = ref(null)
const analysisParams = reactive({ from: null, to: null })

analysisParams.groupBy   = analysisParams.groupBy   ?? 'identifier'
analysisParams.minCluster= analysisParams.minCluster?? 2
analysisParams.levels    = analysisParams.levels    ?? []

/* Filter catalog by current POV (mode) */
const analysisOptions = computed(() => {
  const pov = mode.value // 'project' | 'entity' | 'interlinkage'
  return ANALYSIS_CASES
    .filter(c => c.pov.includes(pov))
    .map(c => ({
      text: c.title,
      value: c.key,
      pov: c.pov,
      long: c.long,
      short: c.short,
    }))
})

const selectedAnalysis = computed(() => ANALYSIS_CASES.find(c => c.key === analysisKey.value) || null)
const povLabel = computed(() => {
  if (mode.value === 'project') return 'Project'
  if (mode.value === 'entity') return 'Legal entity'
  return 'Interlinkage'
})

/* Run hook (stub calling your existing focus bundle / specific endpoints later) */
async function runAnalysis() {
  if (!selectedAnalysis.value || !focusId.value) {
    notify.warn('Pick a focus and an analysis first.')
    return
  }
  analysisLoading.value = true
  analysisResult.value = null
  try {
    const caseKey = selectedAnalysis.value.key

    if (caseKey === 'project_expiry_monitoring') {
      // Defaults if user did not set the optional date range
      const today = new Date()
      const defaultFrom = iso(today)
      const defaultTo = iso(new Date(today.getFullYear(), today.getMonth(), today.getDate() + 90))

      const payload = {
        pov_kind: mode.value,                // 'project' | 'interlinkage' also supported
        pov_id: Number(focusId.value),
        from: iso(analysisParams.from) || defaultFrom,
        to:   iso(analysisParams.to)   || defaultTo,
        // Optional: filter by dependency types/levels if you add UI fields later:
        // dep_types: ['guarantee','contractual','technical'],
        // levels: ['low','medium','high','critical']
      }

      const data = await runExpiryMonitoring(payload)
      analysisResult.value = data // keep raw JSON in the right pane if you like

      // Provide context maps so the dialog can show nice labels/colors
      expiryMonitoringDialogTitle.value = `Expiry monitoring — ${povLabel.value}`
      expiryMonitoringDialogPayload.value = data
      expiryMonitoringDialogContext.value = {
        entities: { ...cache.entities },           // by id
        currencies: { ...refCache.currenciesById } // by id
        // interlinkages can be added if you plan to resolve more fields
      }
      expiryMonitoringDialogOpen.value = true

      const n = data?.items?.length ?? 0
      notify.success(`Expiry monitoring: ${n} item${n === 1 ? '' : 's'} found.`)
      return
    }
    if (caseKey === 'project_concentration_by_dependency') {
      const payload = {
        pov_kind: mode.value,                      // 'project' | 'entity' | 'interlinkage'
        pov_id: Number(focusId.value),
        group_by: analysisParams.groupBy || 'identifier',
        min_cluster: Number(analysisParams.minCluster || 2),
        levels: Array.isArray(analysisParams.levels) ? analysisParams.levels : [],
        measure: 'none',                           // 'ead'|'rwa'|'mtm'|'pnl' when you want scoring
        exposures_mode: 'latest'
      }

      const data = await runConcentrationOnSharedDeps(payload)
      analysisResult.value = data                   // keep if you want to show raw JSON somewhere

      // 👉 Show in the dialog (separate JointJS paper)
      concentrationOnSharedDependenciesAnalysisDialogTitle.value = 'Concentration on shared dependencies'
      concentrationOnSharedDependenciesAnalysisDialogPayload.value = data
      concentrationOnSharedDependenciesAnalysisDialogContext.value = {
        interlinkages: { ...cache.interlinkages },
        entities: { ...cache.entities },
        currencies: { ...refCache.currenciesById }
      }
      concentrationOnSharedDependenciesAnalysisDialogOpen.value = true

      const n = data?.clusters?.length ?? 0
      notify.success(`Concentration: ${n} cluster${n === 1 ? '' : 's'} found.`)
      return
    }

    // other cases unchanged / stub
    analysisResult.value = {
      ok: true,
      message: 'Analysis executed (stub). Plug backend here.',
      pov: mode.value,
      focusId: Number(focusId.value),
      case: caseKey,
      params: { ...analysisParams }
    }
  } catch (e) {
    console.error('runAnalysis error', e)
    notify.error('Analysis failed')
  } finally {
    analysisLoading.value = false
  }
}



/*************** GRAPH ***********************/
const paperEl = ref(null)
let paper

const filters = reactive({ level: null, type: null })
//var graph = reactive({ nodes: [], links: [] })
let graph = null
const selected = ref(null)
const focusId = ref(null)
const loading = ref(false)


// Track analysis overlay cells by a tag
const OVERLAY_TAG = 'analysis:concentration'
function clearAnalysisOverlay(tag = OVERLAY_TAG) {
  if (!graph) return
  const cells = graph.getCells()
  const toRemove = cells.filter(c => c.get?.('overlayTag') === tag)
  if (toRemove.length) graph.removeCells(toRemove)
}

// A compact “cluster bubble” node
function makeClusterBubble(node, { tag = OVERLAY_TAG } = {}) {
  const r = new joint.shapes.standard.Circle()
  const size = Math.max(40, Math.min(Number(node.size_hint || 60), 120))
  r.resize(size, size)
  r.attr({
    body: { fill: '#FFF8E1', stroke: '#FF6F00' },
    label: {
      text: String(node.label ?? 'Cluster'),
      fontSize: 11,
      fontWeight: 600,
      fill: '#E65100',
      wrap: { text: true, width: size - 10 }
    }
  })
  r.set('typeTag', 'cluster')
  r.set('overlayTag', tag)
  r.set('data', { id: node.id, il_count: node.il_count })
  r.addTo(graph)
  return r
}

// Draw overlay from backend plan: { nodes:[], links:[] }
function drawOverlayFromPlan(overlay, { tag = OVERLAY_TAG } = {}) {
  if (!overlay) return
  const nodeMap = new Map()

  // Reuse existing IL nodes; create cluster bubbles
  overlay.nodes?.forEach(n => {
    if (String(n.kind) === 'cluster') {
      const cell = makeClusterBubble(n, { tag })
      nodeMap.set(n.id, cell)
    } else {
      // other kinds can be added later
    }
  })

  // Build links (IL -> cluster). IL nodes already exist in graph.
  overlay.links?.forEach(l => {
    const srcId = String(l.from || '')
    const tgtId = String(l.to || '')
    let srcCell = null
    let tgtCell = null

    // If source is an IL reference ("il:<id>"), reuse the existing IL cell
    if (srcId.startsWith('il:')) {
      const ilRawId = srcId.slice(3)
      srcCell = graph.getCell(`interlinkage-${ilRawId}`) // your IL cell id format
    } else {
      srcCell = nodeMap.get(srcId)
    }

    // Target is usually "cluster:<key>"
    tgtCell = nodeMap.get(tgtId)

    if (srcCell && tgtCell) {
      const link = new joint.shapes.standard.Link()
      link.source(srcCell)
      link.target(tgtCell)
      link.attr({
        line: {
          stroke: '#FF6F00',
          strokeWidth: 1.8,
          strokeDasharray: '5 3',
          targetMarker: { type: 'classic', stroke: '#FF6F00', fill: '#FF6F00' }
        }
      })
      if (l.label) link.appendLabel({ position: 0.5, attrs: { text: { text: String(l.label), fontSize: 10 } } })
      link.set('typeTag', 'analysis-link')
      link.set('overlayTag', tag)
      link.set('data', l)
      link.addTo(graph)
    }
  })
}

function downloadGraphSvg() {
  if (!paper) return
  const svgEl = paper.svg || paper.el.querySelector('svg')
  if (!svgEl) { notify.error('SVG not found'); return }

  const { x, y, w, h } = getExportBBox()

  const cloned = svgEl.cloneNode(true)
  cloned.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  cloned.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink')
  cloned.setAttribute('viewBox', `${x} ${y} ${w} ${h}`)
  cloned.removeAttribute('width')
  cloned.removeAttribute('height')
  cloned.style.overflow = 'visible' // prevent clip

  const serializer = new XMLSerializer()
  const svgText = serializer.serializeToString(cloned)
  const blob = new Blob([svgText], { type: 'image/svg+xml;charset=utf-8' })
  const url = URL.createObjectURL(blob)

  const a = document.createElement('a')
  const ts = new Date().toISOString().replace(/[:.]/g, '-')
  a.href = url
  a.download = `graph-${ts}.svg`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
  notify.success('SVG exported.')
}



async function downloadGraphPng() {
  try {
    if (!paper || !graph) return
    const cells = graph.getCells?.() || []
    if (!cells.length) { notify.warn('Nothing to export'); return }

    const { x, y, w, h } = getExportBBox()

    const svgEl = paper.svg || paper.el.querySelector('svg')
    if (!svgEl) { notify.error('SVG not found on paper'); return }

    const cloned = svgEl.cloneNode(true)

    // Remove taint sources (keep your existing logic)
    ;[...cloned.querySelectorAll('image')].forEach(n => n.remove())
    const foreigns = [...cloned.querySelectorAll('foreignObject')]
    if (foreigns.length) {
      // Optional placeholder approach; or simply remove:
      foreigns.forEach(fo => fo.remove())
    }

    // Crop & make sure overflow doesn’t clip
    cloned.setAttribute('width', String(w))
    cloned.setAttribute('height', String(h))
    cloned.setAttribute('viewBox', `${x} ${y} ${w} ${h}`)
    cloned.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
    cloned.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink')
    cloned.style.overflow = 'visible'

    const serializer = new XMLSerializer()
    const svgText = serializer.serializeToString(cloned)
    const svgBlob = new Blob([svgText], { type: 'image/svg+xml;charset=utf-8' })
    const svgUrl = URL.createObjectURL(svgBlob)

    const dpr = Math.min(window.devicePixelRatio || 1, 3)
    const canvas = document.createElement('canvas')
    canvas.width = Math.max(1, Math.floor(w * dpr))
    canvas.height = Math.max(1, Math.floor(h * dpr))
    const ctx = canvas.getContext('2d', { alpha: true })

    ctx.fillStyle = '#FAFAFA'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    await new Promise((resolve, reject) => {
      const img = new Image()
      img.onload = () => { ctx.drawImage(img, 0, 0, canvas.width, canvas.height); URL.revokeObjectURL(svgUrl); resolve() }
      img.onerror = (e) => reject(e)
      img.src = svgUrl
    })

    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/png', 0.95))
    if (!blob) { notify.error('Failed to render PNG'); return }

    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    const ts = new Date().toISOString().replace(/[:.]/g, '-')
    a.href = url
    a.download = `graph-${ts}.png`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
    notify.success('PNG exported (safe mode).')
  } catch (err) {
    console.error('downloadGraphPng error', err)
    notify.error('PNG export failed')
  }
}

function getExportBBox() {
  // Prefer JointJS computed bbox that includes links & markers
  let bb
  if (paper && typeof paper.getContentBBox === 'function') {
    // useModelGeometry:false => visual bounds (includes stroke width)
    bb = paper.getContentBBox({ useModelGeometry: false })
  } else {
    // Fallback: bbox of all cells (can miss markers); we’ll inflate more
    const cells = graph?.getCells?.() || []
    bb = graph.getBBox(cells)
  }

  // Inflate generously to avoid clipping arrowheads / shadows
  const pad = 40 // px
  const x = Math.floor(bb.x - pad)
  const y = Math.floor(bb.y - pad)
  // Round up +2px to avoid fractional truncation on right/bottom edges
  const w = Math.ceil(bb.width + pad * 2) + 2
  const h = Math.ceil(bb.height + pad * 2) + 2

  return { x, y, w, h }
}

function initPaper() {
  if (paper) { try { paper.remove() } catch(_){} paper = null }
  if (paperEl.value) paperEl.value.innerHTML = ''

  graph = new joint.dia.Graph({}, { cellNamespace: shapesNS })

  paper = new joint.dia.Paper({
    el: paperEl.value,
    model: graph,
    width: '100%',
    height: 700,
    gridSize: 10,
    drawGrid: true,
    background: { color: '#FAFAFA' },
    interactive: { linkMove: false },
    cellViewNamespace: shapesNS
  })

  // basic pan/zoom
  let isPanning = false, panStart = { x:0, y:0 }, origin = { x:0, y:0 }
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

  // selection → your existing details panel
  paper.on('element:pointerdown', (view) => {
    selected.value = { kind: view.model.get('typeTag'), data: view.model.get('data') }
  })
  paper.on('link:pointerdown', (view) => {
    const tag = view.model.get('typeTag')
    selected.value = { kind: tag === 'interdep' || tag === 'interdepNode' ? 'interdep' : 'link', data: view.model.get('data') }
  })


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

const refCache = reactive({
  countriesById: {},
  sectorsById: {},
  currenciesById: {},
  praById: {},
  cptyTypesById: {},
  entitiesById: {},   // transient, per-bundle
  projectsById: {}    // transient, per-bundle
})

function projectCardTemplate(p) {
  const safe = (v) => (v == null || v === '' ? '—' : String(v))

  const country = p.country?.name || p.country_name || p.country || '—'
  const sector  = p.sector?.label || p.sector_label || p.sector || '—'
  const region  = p.region || '—'

  return {
    type: 'AdaptiveCard',
    $schema: 'http://adaptivecards.io/schemas/adaptive-card.json',
    version: '1.5',
    body: [
      // ===== Header (darker bar) with single chevron behavior (handled via 2 images that toggle each other)
      {
        type: 'Container',
        style: 'emphasis',            // darker than default; improves contrast
        bleed: true,
        items: [
          {
            type: 'ColumnSet',
            columns: [
              {
                type: 'Column',
                width: 'stretch',
                items: [
                  {
                    type: 'TextBlock',
                    text: safe(p.name || 'Project'),
                    weight: 'Bolder',
                    size: 'Medium',
                    wrap: true,
                    maxLines: 2
                  },
                  {
                    type: 'TextBlock',
                    spacing: 'None',
                    text: p.code ? `Code: ${p.code}` : 'Code: —',
                    color: 'Accent',
                    weight: 'Bolder',
                    size: 'Small',
                    isSubtle: true,
                    wrap: true
                  }
                ]
              },
              // Chevron icon (images) – only one visible at a time
              {
                type: 'Column',
                width: 'auto',
                verticalContentAlignment: 'Center',
                items: [
                  {
                    type: 'Image',
                    id: 'chev-down',
                    url: 'https://adaptivecards.io/content/down.png',
                    altText: 'Show details',
                    selectAction: {
                      type: 'Action.ToggleVisibility',
                      targetElements: ['proj-details','chev-down','chev-up']
                    },
                    spacing: 'None',
                    size: 'Small'
                  },
                  {
                    type: 'Image',
                    id: 'chev-up',
                    isVisible: false,
                    url: 'https://adaptivecards.io/content/up.png',
                    altText: 'Hide details',
                    selectAction: {
                      type: 'Action.ToggleVisibility',
                      targetElements: ['proj-details','chev-down','chev-up']
                    },
                    spacing: 'None',
                    size: 'Small'
                  }
                ]
              }
            ]
          }
        ]
      },

      // ===== Core attributes (slightly tinted panel)
      {
        type: 'Container',
        separator: true,
        spacing: 'Small',
        items: [
          {
            type: 'FactSet',
            facts: [
              { title: 'Region',  value: safe(region) },
              { title: 'Country', value: safe(country) },
              { title: 'Sector',  value: safe(sector) }
            ]
          }
        ]
      },

      // ===== Collapsible details (FactSet)
      {
        type: 'Container',
        id: 'proj-details',
        isVisible: false,
        separator: true,
        spacing: 'Small',
        items: [
          {
            type: 'FactSet',
            facts: [
              { title: 'Business line', value: safe(p.business_line) },
              { title: 'Portfolio',     value: safe(p.portfolio) },
              { title: 'Code',          value: safe(p.code) },
              { title: 'Description',   value: safe(p.description || 'No description.') }
            ]
          }
        ]
      }
    ]
  }
}

function makeProjectCell(p) {
  const cell = new AdaptiveCardModel({
    id: `project-${p.id}`,
    size: { width: 250, height: 78 },   // compact; adjust to taste
    template: projectCardTemplate(p)
  })
  cell.set('typeTag', 'project')
  cell.set('data', p)
  // cell.once('ac:rendered', () => cell.fitToContent?.(8))
  cell.addTo(graph)
  return cell
}

function interlinkageCardTemplate(il) {
  const safe = (v) => (v == null || v === '' ? '—' : String(v))

  const sponsor    = refCache.entitiesById[il.sponsor_id]?.name || '—'
  const counterpty = refCache.entitiesById[il.counterparty_id]?.name || '—'
  const booking    = refCache.entitiesById[il.booking_entity_id]?.name || '—'
  const project    = refCache.projectsById[il.project_id]?.name || '—'

  const praLabel   = refCache.praById[il.pra_activity_id]?.label || '—'
  const cptyType   = refCache.cptyTypesById[il.counterparty_type_id]?.label || '—'

  const ccyCode = refCache.currenciesById[il.currency_id]?.code || 'EUR'
  const notionalStr = (() => {
    try {
      return new Intl.NumberFormat(undefined, { style: 'currency', currency: ccyCode, maximumFractionDigits: 2 })
        .format(Number(il.notional_amount ?? 0))
    } catch { return `${il.notional_amount ?? '—'} ${ccyCode}` }
  })()

  return {
    type: 'AdaptiveCard',
    $schema: 'http://adaptivecards.io/schemas/adaptive-card.json',
    version: '1.5',
    body: [
      // Header bar — style driven by status, no status text
      {
        type: 'Container',
        style: statusToCardStyle(il.status),
        bleed: true,
        items: [
          {
            type: 'ColumnSet',
            columns: [
              {
                type: 'Column',
                width: 'stretch',
                items: [
                  { type: 'TextBlock', text: `Interlinkage #${il.id}`, weight: 'Bolder', size: 'Medium', wrap: true },
                  { type: 'TextBlock', text: safe(project), spacing: 'None', isSubtle: true, wrap: true }
                ]
              },
              // Chevron only
              {
                type: 'Column',
                width: 'auto',
                verticalContentAlignment: 'Center',
                items: [
                  {
                    type: 'Image',
                    id: 'il-chev-down',
                    url: 'https://adaptivecards.io/content/down.png',
                    altText: 'Show details',
                    selectAction: {
                      type: 'Action.ToggleVisibility',
                      targetElements: ['il-details','il-chev-down','il-chev-up']
                    },
                    spacing: 'None',
                    size: 'Small'
                  },
                  {
                    type: 'Image',
                    id: 'il-chev-up',
                    isVisible: false,
                    url: 'https://adaptivecards.io/content/up.png',
                    altText: 'Hide details',
                    selectAction: {
                      type: 'Action.ToggleVisibility',
                      targetElements: ['il-details','il-chev-down','il-chev-up']
                    },
                    spacing: 'None',
                    size: 'Small'
                  }
                ]
              }
            ]
          }
        ]
      },

      // Core KPIs
      {
        type: 'Container',
        separator: true,
        spacing: 'Small',
        items: [
          {
            type: 'ColumnSet',
            columns: [
              {
                type: 'Column',
                width: 'stretch',
                items: [
                  { type: 'TextBlock', text: 'Notional', isSubtle: true, size: 'Small' },
                  { type: 'TextBlock', text: notionalStr, weight: 'Bolder', size: 'Small' } // note: 'Small' (capital S)
                ]
              },
              {
                type: 'Column',
                width: 'stretch',
                items: [
                  { type: 'TextBlock', text: 'Currency', isSubtle: true, size: 'Small' },
                  { type: 'TextBlock', text: ccyCode, weight: 'Bolder', size: 'Small' }
                ]
              }
            ]
          }
        ]
      },

      // Parties (booking shown; add sponsor/cpty if you want here)
      {
        type: 'Container',
        separator: true,
        spacing: 'Small',
        items: [
          {
            type: 'FactSet',
            facts: [
              { title: 'Booking', value: safe(booking) }
            ]
          }
        ]
      },

      // Collapsible details
      {
        type: 'Container',
        id: 'il-details',
        isVisible: false,
        separator: true,
        spacing: 'Small',
        items: [
          {
            type: 'FactSet',
            facts: [
              { title: 'PRA Activity',      value: safe(praLabel) },
              { title: 'Counterparty Type', value: safe(cptyType) },
              { title: 'Purpose',           value: safe(il.purpose) },
              { title: 'Remarks',           value: safe(il.remarks) }
            ]
          }
        ]
      }
    ]
  }
}

function statusToCardStyle(status) {
  const s = String(status || '').toLowerCase()
  // tweak mapping to your workflow as needed
  if (s === 'validated' || s === 'active' || s === 'approved') return 'good'
  if (s === 'pending'   || s === 'review' || s === 'in_review') return 'warning'
  if (s === 'rejected'  || s === 'blocked' || s === 'cancelled') return 'attention'
  if (s === 'draft') return 'accent'
  return 'default'
}
function makeInterlinkageCell(il) {
  const cell = new AdaptiveCardModel({
    id: `interlinkage-${il.id}`,
    size: { width: 280, height: 92 },   // compact; expands on toggle
    template: interlinkageCardTemplate(il)
  })
  cell.set('typeTag', 'interlinkage')
  cell.set('data', il)
  // cell.once('ac:rendered', () => cell.fitToContent?.(8)) // optional auto-resize
  cell.addTo(graph)
  return cell
}


// ==== Helpers (reuse alongside statusToCardStyle) ====
function safe(v) { return (v == null || v === '') ? '—' : String(v) }

function levelToCardStyle(level) {
  const s = (level || '').toLowerCase()
  if (s === 'critical') return 'attention'
  if (s === 'high')     return 'warning'
  if (s === 'medium')   return 'accent'
  if (s === 'low')      return 'good'
  return 'default'
}

function fmtDate(d) {
  try {
    if (!d) return '—'
    // Expecting ISO (YYYY-MM-DD) from API; keep it locale-friendly but short
    return new Date(d).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: '2-digit' })
  } catch { return String(d) || '—' }
}

// ==== Adaptive Card template for Interdependence ====
function interdependenceCardTemplate(dep) {
  // Resolve project name if normalized
  const projName = dep.project?.name || refCache.projectsById[dep.project_id]?.name || dep.project_name || '—'

  return {
    type: 'AdaptiveCard',
    $schema: 'http://adaptivecards.io/schemas/adaptive-card.json',
    version: '1.5',
    body: [
      // Header bar driven by LEVEL (materiality)
      {
        type: 'Container',
        style: 'good',
        bleed: true,
        items: [
          {
            type: 'ColumnSet',
            columns: [
              {
                type: 'Column',
                width: 'stretch',
                items: [
                  {
                    type: 'TextBlock',
                    text: 'Interdependence : ' + safe(dep.type),
                    weight: 'Bolder',
                    size: 'Medium',
                    wrap: true
                  },
                  {
                    type: 'TextBlock',
                    spacing: 'None',
                    text: `Level: ${safe(dep.level)}`,
                    isSubtle: true,
                    size: 'Small',
                    wrap: true
                  }
                ]
              },
              // Chevron to toggle details
              {
                type: 'Column',
                width: 'auto',
                verticalContentAlignment: 'Center',
                items: [
                  {
                    type: 'Image',
                    id: 'dep-chev-down',
                    url: 'https://adaptivecards.io/content/down.png',
                    altText: 'Show details',
                    selectAction: {
                      type: 'Action.ToggleVisibility',
                      targetElements: ['dep-details','dep-chev-down','dep-chev-up']
                    },
                    spacing: 'None',
                    size: 'Small'
                  },
                  {
                    type: 'Image',
                    id: 'dep-chev-up',
                    isVisible: false,
                    url: 'https://adaptivecards.io/content/up.png',
                    altText: 'Hide details',
                    selectAction: {
                      type: 'Action.ToggleVisibility',
                      targetElements: ['dep-details','dep-chev-down','dep-chev-up']
                    },
                    spacing: 'None',
                    size: 'Small'
                  }
                ]
              }
            ]
          }
        ]
      },

      // Compact KPIs row
      {
        type: 'Container',
        separator: true,
        spacing: 'Small',
        items: [
          {
            type: 'ColumnSet',
            columns: [
              {
                type: 'Column',
                width: 'stretch',
                items: [
                  { type: 'TextBlock', text: 'Identifier', isSubtle: true, size: 'Small' },
                  { type: 'TextBlock', text: safe(dep.interdependence_identifier), weight: 'Bolder', size: 'Small', wrap: true }
                ]
              },
              {
                type: 'Column',
                width: 'auto',
                items: [
                  { type: 'TextBlock', text: 'Effective', isSubtle: true, size: 'Small' },
                  { type: 'TextBlock', text: fmtDate(dep.effective_date), weight: 'Bolder', size: 'Small' }
                ]
              },
              {
                type: 'Column',
                width: 'auto',
                items: [
                  { type: 'TextBlock', text: 'Expiry', isSubtle: true, size: 'Small' },
                  { type: 'TextBlock', text: fmtDate(dep.expiry_date), weight: 'Bolder', size: 'Small' }
                ]
              }
            ]
          }
        ]
      },

      // Collapsible details
      {
        type: 'Container',
        id: 'dep-details',
        isVisible: false,
        separator: true,
        spacing: 'Small',
        items: [
          {
            type: 'FactSet',
            facts: [
              { title: 'Project',         value: safe(projName) },
              { title: 'Type',            value: safe(dep.type) },
              { title: 'Level',           value: safe(dep.level) },
              { title: 'Risk assessment', value: safe(dep.risk_assessment || 'No notes.') }
            ]
          }
        ]
      }
    ]
  }
}

// ==== Cell factory (AdaptiveCardModel) ====
function makeInterdepCell(dep) {
  const cell = new AdaptiveCardModel({
    id: `interdep-${dep.id || dep.interdependence_identifier || crypto.randomUUID?.() || Math.random().toString(36).slice(2)}`,
    size: { width: 280, height: 92 }, // compact; expands when toggled
    template: interdependenceCardTemplate(dep)
  })
  cell.set('typeTag', 'interdependence')
  cell.set('data', dep)
  // Optional: auto-resize after AC render if your AdaptiveCardModel supports it
  // cell.once('ac:rendered', () => cell.fitToContent?.(8))
  cell.addTo(graph)
  return cell
}

function makeLink(source, target, opts = {}) {
  const link = new joint.shapes.standard.Link()
  link.source(source)
  link.target(target)
  link.attr({
    line: {
      stroke: opts.stroke || '#607D8B',
      strokeWidth: opts.width || 1.5,
      targetMarker: { type: 'classic', stroke: opts.stroke || '#607D8B', fill: opts.stroke || '#607D8B' }
    }
  })
  if (opts.dashed) link.attr('line/strokeDasharray', '4 2')
  if (opts.label) link.appendLabel({ attrs: { text: { text: opts.label, fontSize: 11 } }, position: .5 })
  link.set('typeTag', opts.typeTag || 'link')
  link.set('data', opts.data || null)
  link.addTo(graph)
  return link
}

function statusColor(status) {
  const s = String(status || '').toLowerCase()
  if (s === 'validated' || s === 'active') return 'Good'
  if (s === 'pending' || s === 'review')   return 'Warning'
  if (s === 'draft')                        return 'Accent'
  return 'Default'
}

function buildGraphFromBundle(bundle) {
  graph.clear()

   const countries = Array.isArray(bundle?.ref?.countries) ? bundle.ref.countries : []
  const sectors   = Array.isArray(bundle?.ref?.sectors) ? bundle.ref.sectors : []
  refCache.countriesById = Object.fromEntries(countries.map(c => [c.id, c]))
  refCache.sectorsById   = Object.fromEntries(sectors.map(s => [s.id, s]))


  const currencies = Array.isArray(bundle?.ref?.currencies) ? bundle.ref.currencies : []
  const pras       = Array.isArray(bundle?.ref?.pra_activities) ? bundle.ref.pra_activities : []
  const cptypes    = Array.isArray(bundle?.ref?.counterparty_types) ? bundle.ref.counterparty_types : []

  refCache.currenciesById = Object.fromEntries(currencies.map(c => [c.id, c]))
  refCache.praById        = Object.fromEntries(pras.map(p => [p.id, p]))
  refCache.cptyTypesById  = Object.fromEntries(cptypes.map(t => [t.id, t]))

  // transient lookups (NOT stored)
  const ents = Array.isArray(bundle.legal_entities) ? bundle.legal_entities : []
  const prjs = Array.isArray(bundle.projects) ? bundle.projects : []
  const ils  = Array.isArray(bundle.interlinkages) ? bundle.interlinkages : []
  const deps = Array.isArray(bundle.interdependences) ? bundle.interdependences : []

   for (const p of prjs) {
    if (!p.country && p.country_id) p.country = refCache.countriesById[p.country_id] || null
    if (!p.sector  && p.sector_id ) p.sector  = refCache.sectorsById[p.sector_id]   || null
  }

  const entById = new Map(ents.map(e => [e.id, e]))
  const prjById = new Map(prjs.map(p => [p.id, p]))
  const ilById  = new Map(ils.map(i => [i.id, i]))

  const nodeMap = new Map()

  // expose to template helpers
  refCache.entitiesById = Object.fromEntries(ents.map(e => [e.id, e]))
  refCache.projectsById = Object.fromEntries(prjs.map(p => [p.id, p]))

  // 1) Projects
  prjs.forEach(p => nodeMap.set(`project:${p.id}`, makeProjectCell(p)))

  // 2) Entities
  ents.forEach(e => nodeMap.set(`entity:${e.id}`, makeEntityCell(e)))

  // 3) Interlinkages + links
  ils.forEach(il => {
    const ilCell = makeInterlinkageCell(il)
    nodeMap.set(`il:${il.id}`, ilCell)

    const sponsor = nodeMap.get(`entity:${il.sponsor_id}`)
    const cpty    = nodeMap.get(`entity:${il.counterparty_id}`)
    const prj     = nodeMap.get(`project:${il.project_id}`)

    if (sponsor) makeLink(sponsor, ilCell, { stroke: '#2E7D32', width: 2, label: 'sponsor' })
    if (cpty)    makeLink(cpty, ilCell,    { stroke: '#B71C1C', width: 2, label: 'counterparty' })
    if (prj)     makeLink(ilCell, prj,     { stroke: '#0D47A1', width: 2, label: 'project' })
  })

  // 4) Interdependencies as nodes (respect UI filters)
  deps.forEach(dep => {
    if (filters.level && dep.level !== filters.level) return
    if (filters.type  && dep.type  !== filters.type)  return

    const ilNode = nodeMap.get(`il:${dep.interlinkage_id}`)
    if (!ilNode) return

    const depNode = makeInterdepCell(dep)
    nodeMap.set(`dep:${dep.id}`, depNode)

    // IL -> Interdep (solid)
    makeLink(ilNode, depNode, {
      stroke: '#6A1B9A', width: 2, label: dep.type || 'interdep',
      typeTag: 'interdep-link-il', data: dep, dashed: true
    })

    // Interdep -> Project (dashed) : prefer dep.project_id, else IL.project_id
    /*const il = ilById.get(dep.interlinkage_id)
    const targetPrjId = dep.project_id || il?.project_id
    const prjNode = targetPrjId ? nodeMap.get(`project:${targetPrjId}`) : null
    if (prjNode) {
      makeLink(depNode, prjNode, { dashed: true, stroke: '#6A1B9A', label: 'project', typeTag: 'interdep-link-project', data: dep })
    }

    // Interdep -> Entities (dashed) via IL’s sponsor/cpty
    if (il?.sponsor_id) {
      const s = nodeMap.get(`entity:${il.sponsor_id}`)
      if (s) makeLink(depNode, s, { dashed: true, stroke: '#6A1B9A', label: 'sponsor', typeTag: 'interdep-link-entity', data: dep })
    }
    if (il?.counterparty_id) {
      const c = nodeMap.get(`entity:${il.counterparty_id}`)
      if (c) makeLink(depNode, c, { dashed: true, stroke: '#6A1B9A', label: 'counterparty', typeTag: 'interdep-link-entity', data: dep })
    }*/
  })

  applyDagreLayout()
}

function applyDagreLayout() {
  const g = new dagre.graphlib.Graph()
  g.setGraph({ rankdir: 'LR', nodesep: 80, ranksep: 140 })
  g.setDefaultEdgeLabel(() => ({}))

  const elements = graph.getElements()
  const links = graph.getLinks()

  elements.forEach((el) => {
    const size = el.size()
    g.setNode(el.id, { width: size.width, height: size.height })
  })

  links.forEach((lnk) => {
    const s = lnk.get('source').id
    const t = lnk.get('target').id
    if (s && t) g.setEdge(s, t)
  })

  dagre.layout(g)

  elements.forEach((el) => {
    const n = g.node(el.id)
    if (!n) return
    const sz = el.size()
    el.position(n.x - sz.width / 2, n.y - sz.height / 2)
  })

  fitToContent()
}

function fitToContent() {
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



const router = useRouter()
const { resource, notify } = useApi()

const mode = ref('project') // 'project' | 'entity' | 'interlinkage'




const ctx = reactive({
  project: { showEntities: true, showInterdeps: true },
  entity:  { showProjects: true, showInterdeps: true, role: 'all' }, // all | sponsor | counterparty | both
  interlinkage: { showInterdeps: true }
})

/* ---------- Async select (paged) ---------- */
const selectItems = ref([])
const selectLoading = ref(false)
const selectPage = ref(1)
const selectPageSize = 25
const selectTotal = ref(0)

const selectLabel = computed(() => {
  if (mode.value === 'project') return ''
  if (mode.value === 'entity') return ''
  return ''
})
const hasMoreSelect = computed(() => selectItems.value.length < selectTotal.value)

function parseListResponse(resp) {
  const r = resp?.data ?? resp
  const items = Array.isArray(r) ? r
    : Array.isArray(r?.items) ? r.items
    : Array.isArray(r?.results) ? r.results
    : Array.isArray(r?.data) ? r.data
    : []
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

async function loadSelectPage({ reset = false } = {}) {
  selectLoading.value = true
  try {
    if (reset) {
      selectPage.value = 1
      selectItems.value = []
      selectTotal.value = 0
    }
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

/* ---------- Data APIs ---------- */
const leApi  = resource('legal-entities')
const prjApi = resource('projects')
const ilApi  = resource('interlinkages')
const depApi = resource('interdependences')

/* ---------- Local caches ---------- */
const cache = reactive({
  entities: {},
  projects: {},
  interlinkages: {},
  interdeps: {}
})

function toItems(resp) {
  const r = resp?.data ?? resp
  if (Array.isArray(r)) return r
  if (Array.isArray(r?.items)) return r.items
  if (Array.isArray(r?.results)) return r.results
  if (Array.isArray(r?.data)) return r.data
  return []
}
async function getManyById(api, ids) {
  if (!ids?.length) return []
  const rows = await Promise.all(ids.map(async (id) => {
    try { const r = await api.get(id); return r?.data ?? r } catch (_) { return null }
  }))
  return rows.filter(Boolean)
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

/* ---------- Focus flows (unchanged) ---------- */
function buildInterdepParams({ interlinkageIds = null, interlinkageId = null } = {}) {
  const p = {}
  if (interlinkageId) p.interlinkage_id = interlinkageId
  if (interlinkageIds?.length) p.interlinkage_ids = interlinkageIds.join(',')
  if (filters.level) p.level = filters.level
  if (filters.type)  p.type  = filters.type
  return p
}

async function fetchContext() {
  cache.entities = {}
  cache.projects = {}
  cache.interlinkages = {}
  cache.interdeps = {}

  if (!focusId.value) return

  if (mode.value === 'project') {
    const prj = await prjApi.get(focusId.value)
    const project = prj?.data ?? prj
    cache.projects[project.id] = project

    const ils = toItems(await ilApi.list({ project_id: project.id }))
    ils.forEach(i => (cache.interlinkages[i.id] = i))

    if (ctx.project.showEntities && ils.length) {
      const entityIds = Array.from(new Set(ils.flatMap(i => [i.sponsor_id, i.counterparty_id]).filter(Boolean)))
      const ents = await getManyById(leApi, entityIds)
      ents.forEach(e => (cache.entities[e.id] = e))
    }

    if (ctx.project.showInterdeps && ils.length) {
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

  else if (mode.value === 'entity') {
    const ent = await leApi.get(focusId.value)
    const entity = ent?.data ?? ent
    cache.entities[entity.id] = entity

    let ils = []
    if (ctx.entity.role === 'all' || ctx.entity.role === 'sponsor' || ctx.entity.role === 'both') {
      ils = ils.concat(toItems(await ilApi.list({ sponsor_id: entity.id })))
    }
    if (ctx.entity.role === 'all' || ctx.entity.role === 'counterparty' || ctx.entity.role === 'both') {
      ils = ils.concat(toItems(await ilApi.list({ counterparty_id: entity.id })))
    }
    if (ctx.entity.role === 'both') {
      ils = ils.filter(i => i.sponsor_id === entity.id && i.counterparty_id === entity.id)
    }
    const byId = new Map(ils.map(i => [i.id, i]))
    ils = Array.from(byId.values())
    ils.forEach(i => (cache.interlinkages[i.id] = i))

    if (ctx.entity.showProjects && ils.length) {
      const prjIds = Array.from(new Set(ils.map(i => i.project_id).filter(Boolean)))
      const prjs = await getManyById(prjApi, prjIds)
      prjs.forEach(p => (cache.projects[p.id] = p))
    }

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
    const il = await ilApi.get(focusId.value)
    const inter = il?.data ?? il
    cache.interlinkages[inter.id] = inter

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

    if (ctx.interlinkage.showInterdeps) {
      const deps = toItems(await depApi.list(buildInterdepParams({ interlinkageId: inter.id })))
      deps.forEach(d => (cache.interdeps[d.id] = d))
    }
  }
}

/* ---------- Graph summary for the placeholder ---------- */

function idKey(kind, id) { return `${kind}:${id}` }

function rebuildGraph() {
  const nodes = []
  const links = []
  const seen = new Set()

  // Sort into lanes
  const ents = Object.values(cache.entities || {})
  const ils  = Object.values(cache.interlinkages || {})
  const prjs = Object.values(cache.projects || {})

  // Simple vertical stacking layout
  const laneX = { entity: 120, interlinkage: 460, project: 800 }
  const vGap = 90
  const top = 60

  // Place nodes per kind
  let yEntity = top
  for (const e of ents) {
    const id = idKey('entity', e.id)
    nodes.push({ id, kind: 'entity', x: laneX.entity, y: yEntity, label: e.name, data: e })
    yEntity += vGap
    seen.add(id)
  }

  let yIL = top
  for (const i of ils) {
    const id = idKey('interlinkage', i.id)
    nodes.push({ id, kind: 'interlinkage', x: laneX.interlinkage, y: yIL, label: `IL #${i.id}`, data: i })
    yIL += vGap
    seen.add(id)
  }

  let yProject = top
  for (const p of prjs) {
    const id = idKey('project', p.id)
    nodes.push({ id, kind: 'project', x: laneX.project, y: yProject, label: p.name, data: p })
    yProject += vGap
    seen.add(id)
  }

  // Build links
  // 1) Prefer backend edges if present
  const rawEdges = Array.isArray(cache.edges) ? cache.edges : []

  if (rawEdges.length) {
    for (const e of rawEdges) {
      if (e.type === 'entity-interlinkage') {
        links.push({
          from: idKey('entity', e.entity_id),
          to:   idKey('interlinkage', e.interlinkage_id),
          meta: { role: e.role }
        })
      } else if (e.type === 'interlinkage-project') {
        links.push({
          from: idKey('interlinkage', e.interlinkage_id),
          to:   idKey('project', e.project_id),
          meta: {}
        })
      } else if (e.type === 'interdep-of') {
        // optional: interdep nodes (keep simple: attach as small stub)
        // no-op for now
      }
    }
  } else {
    // 2) Fallback: derive edges from interlinkage rows
    for (const i of ils) {
      if (i.sponsor_id) {
        links.push({ from: idKey('entity', i.sponsor_id), to: idKey('interlinkage', i.id), meta: { role: 'sponsor' } })
      }
      if (i.counterparty_id) {
        links.push({ from: idKey('entity', i.counterparty_id), to: idKey('interlinkage', i.id), meta: { role: 'counterparty' } })
      }
      if (i.project_id) {
        links.push({ from: idKey('interlinkage', i.id), to: idKey('project', i.project_id), meta: {} })
      }
    }
  }

  graph.nodes = nodes
  graph.links = links
}

const graphSummary = computed(() => {
  const ents = Object.values(cache.entities)
  const ils  = Object.values(cache.interlinkages)
  const deps = Object.values(cache.interdeps)
  const prjs = Object.values(cache.projects)

  return {
    entities: ents,
    interlinkages: ils,
    interdeps: deps,
    projects: prjs
  }
})

/* ---------- “Build & Fit” wrappers (no-op friendly) ---------- */
function buildGraphForContext() {
  // no-op for placeholder; the summary is reactive
}
function ctxSnapshot() {
  return {
    project: { ...ctx.project },
    entity:  { ...ctx.entity },
    interlinkage: { ...ctx.interlinkage },
    filters: { ...filters },
  }
}

function buildPlannedCalls() {
  const calls = []
  if (!focusId.value) return calls

  if (mode.value === 'project') {
    calls.push(
      { endpoint: 'projects.get',          method: 'GET', params: { id: focusId.value } },
      { endpoint: 'interlinkages.list',    method: 'GET', params: { project_id: focusId.value } },
    )
    if (ctx.project.showEntities) {
      calls.push({ endpoint: 'legal-entities.get', method: 'GET', params: { ids: '<<from interlinkages.sponsor_id/counterparty_id>>' } })
    }
    if (ctx.project.showInterdeps) {
      calls.push({ endpoint: 'interdependences.list', method: 'GET', params: { interlinkage_ids: '<<from interlinkages>>', ...buildInterdepParams() } })
    }
  }

  if (mode.value === 'entity') {
    const role = ctx.entity.role
    if (role === 'all' || role === 'sponsor' || role === 'both') {
      calls.push({ endpoint: 'interlinkages.list', method: 'GET', params: { sponsor_id: focusId.value } })
    }
    if (role === 'all' || role === 'counterparty' || role === 'both') {
      calls.push({ endpoint: 'interlinkages.list', method: 'GET', params: { counterparty_id: focusId.value } })
    }
    calls.unshift({ endpoint: 'legal-entities.get', method: 'GET', params: { id: focusId.value } })
    if (ctx.entity.showProjects) {
      calls.push({ endpoint: 'projects.get', method: 'GET', params: { ids: '<<from interlinkages.project_id>>' } })
    }
    if (ctx.entity.showInterdeps) {
      calls.push({ endpoint: 'interdependences.list', method: 'GET', params: { interlinkage_ids: '<<from interlinkages>>', ...buildInterdepParams() } })
    }
  }

  if (mode.value === 'interlinkage') {
    calls.push(
      { endpoint: 'interlinkages.get',     method: 'GET', params: { id: focusId.value } },
      { endpoint: 'projects.get',          method: 'GET', params: { id: '<<from interlinkage.project_id>>' } },
      { endpoint: 'legal-entities.get',    method: 'GET', params: { id: '<<from interlinkage.sponsor_id>>' } },
      { endpoint: 'legal-entities.get',    method: 'GET', params: { id: '<<from interlinkage.counterparty_id>>' } },
    )
    if (ctx.interlinkage.showInterdeps) {
      calls.push({ endpoint: 'interdependences.list', method: 'GET', params: { interlinkage_id: focusId.value, ...buildInterdepParams() } })
    }
  }

  return calls
}

/* ---------- Replace applyFocus with a "print only" version ---------- */

function toIdMap(arr) {
  if (!Array.isArray(arr)) return {}
  const map = {}
  for (const x of arr) if (x && x.id != null) map[x.id] = x
  return map
}

function pick(obj, key, fallback) {
  return obj && obj[key] != null ? obj[key] : fallback
}

async function applyFocus() {
  if (!focusId.value) { notify.warn('Pick something to focus on'); return }
  loading.value = true
  try {
    const params = {
      kind: mode.value,                 // 'project' | 'entity' | 'interlinkage'
      id: Number(focusId.value),
      include_interdeps: true,
      exposures_mode: 'latest',
      include_notes: true,
      include_attachments: true,
      include_workflow: true,
      include_analysis: true,
      // pass UI filters to API if present
      ...(filters.level ? { level: filters.level } : {}),
      ...(filters.type  ? { type:  filters.type  } : {}),
    }

    const resp   = await fetchFocusBundle(params)
    const bundle = resp && resp.data ? resp.data : resp

    buildGraphFromBundle(bundle)
    clearAnalysisOverlay()

    selected.value = null
    notify.success('Focus data loaded.')
  } catch (e) {
    console.error('focus-bundle error', e)
    notify.error('Failed to load focus data')
  } finally {
    loading.value = false
  }
}

/* ---------- Hooks to/from placeholder ---------- */
function onPickFromGraph(payload) {
  selected.value = payload
}
function onFitRequested() {
  fitToContent()
}

/* ---------- Quick jumpers ---------- */
function focusProject(id) { mode.value = 'project'; focusId.value = id; applyFocus() }
function focusEntity(id)  { mode.value = 'entity'; focusId.value = id; applyFocus() }
function focusInterlinkage(id) { mode.value = 'interlinkage'; focusId.value = id; applyFocus() }

/* ---------- Watchers ---------- */
watch([
  mode,
  () => ctx.project.showEntities, () => ctx.project.showInterdeps,
  () => ctx.entity.showProjects,  () => ctx.entity.showInterdeps, () => ctx.entity.role,
  () => ctx.interlinkage.showInterdeps,
  () => filters.level, () => filters.type,
  () => {
    analysisKey.value = null
    analysisResult.value = null
    analysisParams.from = null
    analysisParams.to = null

    clearAnalysisOverlay()
  }
], () => { if (focusId.value) applyFocus() })

watch(mode, () => {
  focusId.value = null
  loadSelectPage({ reset: true })
})

watch([mode, analysisKey], () => {
  analysisResult.value = null
  if (analysisKey.value === 'project_concentration_by_dependency') {
    analysisParams.groupBy = 'identifier'
    analysisParams.minCluster = 2
    analysisParams.levels = []
  }
})

/* ---------- Init ---------- */
onMounted(() => {
  initPaper()
  loadSelectPage({ reset: true })

})

watch([
  mode,
  () => ctx.project.showEntities, () => ctx.project.showInterdeps,
  () => ctx.entity.showProjects,  () => ctx.entity.showInterdeps, () => ctx.entity.role,
  () => ctx.interlinkage.showInterdeps,
  () => filters.level, () => filters.type
], () => { if (focusId.value) applyFocus() })

</script>
<style scoped>
/* Layout wrappers */
.graph-wrapper { position: relative; overflow: hidden; }
.graph-paper { width: 100%; min-height: 700px; }

/* Placeholder root */
.placeholder-root {
  position: relative;
  padding: 16px;
  min-height: 700px;
  background: #fafafa;
  border-radius: 12px;
}

/* Top toolbar */
.placeholder-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.stats { display: flex; gap: 8px; flex-wrap: wrap; }
.pill {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 999px;
  background: #eceff1;
  color: #455a64;
  border: 1px solid #cfd8dc;
}

/* Buttons */
.ghost-btn {
  appearance: none;
  border: 1px solid #cfd8dc;
  background: #fff;
  color: #37474f;
  padding: 6px 10px;
  border-radius: 10px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: background .15s ease, box-shadow .15s ease, transform .05s ease;
}
.ghost-btn:hover { background: #f5f7f8; box-shadow: 0 1px 6px rgba(0,0,0,.08); }
.ghost-btn:active { transform: translateY(1px); }

/* Columns grid */
.columns {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
@media (max-width: 1440px) {
  .columns { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 1100px) {
  .columns { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 700px) {
  .columns { grid-template-columns: 1fr; }
}

/* Column */
.col {
  background: #fff;
  border-radius: 14px;
  border: 1px solid #e6eaee;
  box-shadow: 0 6px 16px rgba(0,0,0,.06);
  display: flex;
  flex-direction: column;
  min-height: 220px;
}
.col-title {
  padding: 10px 12px;
  font-weight: 700;
  color: #37474f;
  border-bottom: 1px solid #eef2f5;
  background: linear-gradient(180deg, #fafcfe, #f5f7fa);
  border-top-left-radius: 14px;
  border-top-right-radius: 14px;
}

/* Stack list */
.stack {
  padding: 10px;
  display: grid;
  gap: 10px;
  max-height: 550px;
  overflow: auto;
}

/* Cards */
.card {
  border: 1px solid #e6eaee;
  border-radius: 12px;
  padding: 10px 12px;
  cursor: pointer;
  transition: box-shadow .15s ease, transform .05s ease, border-color .15s ease, background .15s ease;
  background: #fff;
}
.card:hover {
  box-shadow: 0 6px 16px rgba(0,0,0,.08);
  transform: translateY(-1px);
  border-color: #d5dbe1;
}
.card .title {
  font-weight: 700;
  font-size: 14px;
  line-height: 1.2;
  color: #263238;
}
.card .meta {
  margin-top: 4px;
  font-size: 12px;
  color: #607d8b;
}

/* Card variants */
.card.entity {
  background: #e6f4ea;
  border-color: #c8e6c9;
}
.card.entity .title { color: #1b5e20; }
.card.entity .meta { color: #2e7d32; }

.card.interlinkage {
  background: #fff3e0;
  border-color: #ffe0b2;
}
.card.interlinkage .title { color: #e65100; }
.card.interlinkage .meta { color: #bf360c; }

.card.interdep {
  background: #f3e5f5;
  border-color: #e1bee7;
}
.card.interdep .title { color: #6a1b9a; }
.card.interdep .meta { color: #4a148c; }

.card.project {
  background: #e3f2fd;
  border-color: #bbdefb;
}
.card.project .title { color: #0d47a1; }
.card.project .meta { color: #1565c0; }

/* Empty state */
.empty-hint {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  text-align: center;
  color: #78909c;
  padding: 24px;
  pointer-events: none;
}
.empty-hint .icon {
  font-size: 56px;
  margin-bottom: 8px;
  opacity: .8;
}
.empty-hint .title {
  font-weight: 700;
  color: #455a64;
}
.empty-hint .subtitle {
  margin-top: 6px;
  font-size: 14px;
}

/* Nice scrollbars (WebKit) */
.stack::-webkit-scrollbar { width: 10px; }
.stack::-webkit-scrollbar-track { background: #f1f3f5; border-radius: 10px; }
.stack::-webkit-scrollbar-thumb { background: #cfd8dc; border-radius: 10px; }
.stack::-webkit-scrollbar-thumb:hover { background: #b0bec5; }

/* Keep the whole toolbar aligned */
.v-card .d-flex.align-center { align-items: center; }

/* Remove the extra bottom space Vuetify reserves for details */
.inline-select :deep(.v-input) {
  margin: 0 !important;
}

/* Match button height and vertical rhythm (≈40px) */
.inline-select :deep(.v-field) {
  border-radius: 9999px;              /* pill look like buttons */
}

.inline-select :deep(.v-field__input) {
  min-height: 40px;                   /* match v-btn (comfortable) */
  padding-top: 6px;
  padding-bottom: 6px;
  align-items: center;                /* center label vertically */
}

/* Keep prepend/append icons centered if you add them later */
.inline-select :deep(.v-field__prepend-inner),
.inline-select :deep(.v-field__append-inner) {
  padding-block: 6px;
}

/* Optional: tighten solo variant top/bottom padding a bit more */
.inline-select :deep(.v-field--variant-solo .v-field__overlay) {
  border-radius: 9999px;
}

.graph-paper { width: 100%; height: 700px; }
.analysis-pre {
  background: #0b1020;
  color: #e6f0ff;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 12px;
  line-height: 1.4;
  max-height: 320px;
  overflow: auto;
}
.help-block {
  border: 1px solid #e6eaee;
  border-radius: 12px;
  padding: 10px 12px;
  background: #fff;
}
</style>
