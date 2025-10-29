<template>
  <v-container fluid>
    <v-card>
      <v-card-title class="d-flex align-center">
        <div class="text-h6">
          Interlinkage #{{ id }}
          <span v-if="titleParts.project">— {{ titleParts.project }}</span>
        </div>
        <v-spacer />
        <v-btn variant="text" prepend-icon="mdi-arrow-left" @click="$router.push({ name: 'interlinkages' })">
          Back to list
        </v-btn>
        <v-btn v-if="1==0" color="primary" class="ml-2" prepend-icon="mdi-content-save" @click="saveCore" :loading="savingCore">
          Save
        </v-btn>
      </v-card-title>

      <v-divider />

      <v-card-text>
        <v-expansion-panels v-model="openPanels" multiple>

          <!-- ============ CORE / OVERVIEW ============ -->
          <v-expansion-panel value="core">
            <v-expansion-panel-title>
              <v-icon class="mr-2">mdi-file-document-outline</v-icon> Overview
            </v-expansion-panel-title>

            <v-expansion-panel-text>
              <div class="overview-grid">
                <!-- Left column -->
                <div class="overview-col">
                  <div class="kv"><span class="k">Sponsor</span><span class="v">{{ leName(core.sponsor_id) }}</span></div>
                  <div class="kv"><span class="k">Counterparty</span><span class="v">{{ leName(core.counterparty_id) }}</span></div>
                  <div class="kv"><span class="k">Booking Entity</span><span class="v">{{ leName(core.booking_entity_id) || '—' }}</span></div>
                  <div class="kv"><span class="k">Project</span><span class="v">{{ projectName(core.project_id) }}</span></div>
                  <div class="kv"><span class="k">PRA Activity</span><span class="v">{{ praLabel(core.pra_activity_id) || '—' }}</span></div>
                  <div class="kv"><span class="k">Counterparty Type</span><span class="v">{{ cptLabel(core.counterparty_type_id) || '—' }}</span></div>
                  <div class="kv"><span class="k">Facility</span><span class="v">{{ facilityRef(core.facility_id) || '—' }}</span></div>
                  <div class="kv"><span class="k">Instrument</span><span class="v">{{ instrumentRef(core.instrument_id) || '—' }}</span></div>
                </div>

                <!-- Right column -->
                <div class="overview-col">
                  <div class="kv"><span class="k">Deal Date</span><span class="v">{{ formatDate(core.deal_date) || '—' }}</span></div>
                  <div class="kv"><span class="k">Effective Date</span><span class="v">{{ formatDate(core.effective_date) || '—' }}</span></div>
                  <div class="kv"><span class="k">Maturity Date</span><span class="v">{{ formatDate(core.maturity_date) || '—' }}</span></div>

                  <div class="kv">
                    <span class="k">Notional Amount</span>
                    <span class="v">
                      {{ formatMoney(core.notional_amount, currencyCode(core.currency_id)) || '—' }}
                      <v-chip v-if="core.currency_id" size="x-small" class="ml-2" variant="tonal">
                        {{ currencyCode(core.currency_id) }}
                      </v-chip>
                    </span>
                  </div>

                  <div class="kv">
                    <span class="k">Status</span>
                    <span class="v">
                      <v-chip size="small" :color="statusColor(core.status)" variant="elevated">{{ core.status }}</v-chip>
                    </span>
                  </div>

                  <div class="kv"><span class="k">Purpose</span><span class="v">{{ core.purpose || '—' }}</span></div>

                  <div class="kv kv-multiline">
                    <span class="k">Remarks</span>
                    <span class="v text-medium-emphasis" style="white-space:pre-wrap">{{ core.remarks || '—' }}</span>
                  </div>
                </div>
              </div>
            </v-expansion-panel-text>
          </v-expansion-panel>


          <!-- ============ ANALYSIS ============ -->
          <v-expansion-panel value="analysis">
            <v-expansion-panel-title>
              <v-icon class="mr-2">mdi-text-long</v-icon> Analysis
              <v-spacer />
              <v-btn-toggle
                v-model="analysisMode"
                density="compact"
                mandatory
                rounded="lg"
                class="ml-4"
              >
                <v-btn value="edit" prepend-icon="mdi-pencil">Edit</v-btn>
                <v-btn value="preview" prepend-icon="mdi-eye">Preview</v-btn>
              </v-btn-toggle>
            </v-expansion-panel-title>

            <v-expansion-panel-text>
              <!-- EDIT MODE -->
              <v-form v-if="analysisMode === 'edit'" @submit.prevent="saveAnalysis">
                <!-- Rich text editor -->
                <QuillEditor
                  v-model:content="analysis.content"
                  content-type="html"
                  theme="snow"
                  toolbar="full"
                  class="rounded-lg border"
                  style="min-height: 220px;"
                />
                <div class="d-flex justify-end mt-3">
                  <v-btn
                    color="primary"
                    prepend-icon="mdi-content-save"
                    @click="saveAnalysis"
                    :loading="savingAnalysis"
                  >
                    Save Analysis
                  </v-btn>
                </div>
              </v-form>

              <!-- PREVIEW MODE -->
              <div v-else class="pa-2">
                <div
                  class="ql-editor rounded-lg border pa-4"
                  v-html="sanitizedAnalysis"
                />
                <div class="d-flex justify-end mt-3">
                  <v-btn color="primary" prepend-icon="mdi-pencil" @click="analysisMode = 'edit'">
                    Edit
                  </v-btn>
                </div>
              </div>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <!-- ============ INTERDEPENDENCES ============ -->
          <v-expansion-panel value="interdependences">
            <v-expansion-panel-title>
              <v-icon class="mr-2">mdi-source-merge</v-icon> Interdependences
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <div class="d-flex justify-end mb-2">
                <v-btn color="primary" prepend-icon="mdi-plus" @click="openInterdepDialog()">Add dependency</v-btn>
              </div>

              <v-data-table
                :headers="interdepHeaders"
                :items="interdeps"
                :items-per-page="10"
              >
                <template #item.project="{ item }">
                  {{ projectName(item.project_id) || item.project_name }}
                </template>
                <template #item.actions="{ item }">
                  <div class="d-flex align-center justify-center" style="gap:6px;">
                    <v-btn size="small" icon="mdi-pencil" variant="text" @click="openInterdepDialog(item)" />
                    <v-btn size="small" icon="mdi-delete" variant="text" color="error" @click="deleteInterdep(item)" />
                  </div>
                </template>
              </v-data-table>

              <!-- Interdependence dialog -->
              <v-dialog v-model="interdepDialog.open" max-width="760">
                <v-card>
                  <v-card-title class="text-h6">
                    {{ interdepDialog.editId ? 'Edit' : 'Add' }} Interdependence
                  </v-card-title>
                  <v-card-text>
                    <v-form @submit.prevent="saveInterdep">
                      <div class="d-grid" style="grid-template-columns: repeat(12, 1fr); gap: 12px;">
                        <div class="col-span-6 d-flex flex-column ga-3">
                          <v-text-field v-model="interdepDialog.model.interdependence_identifier" label="Identifier*" density="compact" />
                          <v-select v-model="interdepDialog.model.type" :items="interdepTypes" label="Type" density="compact" clearable />
                          <v-select v-model="interdepDialog.model.level" :items="interdepLevels" label="Level" density="compact" clearable />
                        </div>
                        <div class="col-span-6 d-flex flex-column ga-3">
                          <v-select
                            v-model="interdepDialog.model.project_id"
                            :items="projects"
                            item-title="name" item-value="id"
                            label="Project"
                            density="compact" clearable
                          />
                          <v-text-field v-model="interdepDialog.model.project_name" label="Project (free text)" density="compact" />
                          <div class="d-flex ga-2">
                            <v-text-field v-model="interdepDialog.model.effective_date" type="date" label="Effective" density="compact" />
                            <v-text-field v-model="interdepDialog.model.expiry_date" type="date" label="Expiry" density="compact" />
                          </div>
                        </div>
                      </div>
                      <v-textarea v-model="interdepDialog.model.risk_assessment" label="Risk assessment" rows="3" auto-grow density="compact" />
                    </v-form>
                  </v-card-text>
                  <v-card-actions>
                    <v-spacer />
                    <v-btn variant="text" @click="interdepDialog.open = false">Cancel</v-btn>
                    <v-btn color="primary" @click="saveInterdep" :loading="savingInterdep">Save</v-btn>
                  </v-card-actions>
                </v-card>
              </v-dialog>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <!-- ============ EXPOSURES ============ -->
          <v-expansion-panel value="exposures">
            <v-expansion-panel-title>
              <v-icon class="mr-2">mdi-chart-areaspline</v-icon> Exposures
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <div class="d-flex justify-end mb-2">
                <v-btn color="primary" prepend-icon="mdi-plus" @click="openExposureDialog()">Add snapshot</v-btn>
              </div>

              <v-data-table
                :headers="exposureHeaders"
                :items="exposures"
                :items-per-page="10"
              >
                <template #item.currency="{ item }">
                  {{ currencyCode(item.currency_id) }}
                </template>
                <template #item.actions="{ item }">
                  <div class="d-flex align-center justify-center" style="gap:6px;">
                    <v-btn size="small" icon="mdi-pencil" variant="text" @click="openExposureDialog(item)" />
                    <v-btn size="small" icon="mdi-delete" variant="text" color="error" @click="deleteExposure(item)" />
                  </div>
                </template>
              </v-data-table>

              <!-- Exposure dialog -->
              <v-dialog v-model="exposureDialog.open" max-width="820">
                <v-card>
                  <v-card-title class="text-h6">
                    {{ exposureDialog.editId ? 'Edit' : 'Add' }} Exposure snapshot
                  </v-card-title>
                  <v-card-text>
                    <v-form @submit.prevent="saveExposure">
                      <div class="d-grid" style="grid-template-columns: repeat(12, 1fr); gap: 12px;">
                        <div class="col-span-6 d-flex flex-column ga-3">
                          <v-text-field v-model="exposureDialog.model.as_of_date" type="date" label="As of date*" density="compact" />
                          <v-select v-model="exposureDialog.model.currency_id" :items="currencies" item-title="code" item-value="id" label="Currency*" density="compact" />
                          <div class="d-flex ga-2">
                            <v-text-field v-model="exposureDialog.model.ead" type="number" label="EAD" density="compact" />
                            <v-text-field v-model="exposureDialog.model.undrawn" type="number" label="Undrawn" density="compact" />
                          </div>
                          <div class="d-flex ga-2">
                            <v-text-field v-model="exposureDialog.model.mtm" type="number" label="MTM" density="compact" />
                            <v-text-field v-model="exposureDialog.model.pnl" type="number" label="PnL" density="compact" />
                          </div>
                        </div>
                        <div class="col-span-6 d-flex flex-column ga-3">
                          <div class="d-flex ga-2">
                            <v-text-field v-model="exposureDialog.model.rwa" type="number" label="RWA" density="compact" />
                            <v-text-field v-model="exposureDialog.model.pd" type="number" step="0.0001" label="PD (0..1)" density="compact" />
                          </div>
                          <div class="d-flex ga-2">
                            <v-text-field v-model="exposureDialog.model.lgd" type="number" step="0.0001" label="LGD (0..1)" density="compact" />
                            <v-text-field v-model="exposureDialog.model.fx_to_reporting" type="number" step="0.00000001" label="FX→reporting" density="compact" />
                          </div>
                        </div>
                      </div>
                    </v-form>
                  </v-card-text>
                  <v-card-actions>
                    <v-spacer />
                    <v-btn variant="text" @click="exposureDialog.open = false">Cancel</v-btn>
                    <v-btn color="primary" @click="saveExposure" :loading="savingExposure">Save</v-btn>
                  </v-card-actions>
                </v-card>
              </v-dialog>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <!-- ============ ATTACHMENTS (upload + viewer) ============ -->
          <v-expansion-panel value="attachments">
            <v-expansion-panel-title>
              <v-icon class="mr-2">mdi-paperclip</v-icon> Attachments
              <v-spacer />
              <v-chip size="small" class="mr-2" variant="tonal">
                {{ attachments.length }} file{{ attachments.length !== 1 ? 's' : '' }}
              </v-chip>
            </v-expansion-panel-title>

            <v-expansion-panel-text>
              <!-- Upload zone -->
              <v-sheet
                class="upload-zone"
                :class="{ dragging: isDragging }"
                elevation="1"
                rounded="lg"
                @dragover.prevent="onDragOver"
                @dragleave.prevent="onDragLeave"
                @drop.prevent="onDrop"
              >
                <div class="zone-inner">
                  <v-icon size="42">mdi-cloud-upload</v-icon>
                  <div class="text-subtitle-1 mt-2">Drop files here to upload</div>
                  <div class="text-medium-emphasis">or</div>
                  <div class="d-flex ga-2 mt-2 flex-wrap">
                    <v-file-input
                      v-model="fileInput"
                      variant="solo-filled"
                      density="comfortable"
                      prepend-icon="mdi-paperclip"
                      label="Select files..."
                      multiple
                      show-size
                      hide-details
                      @change="queueFilesFromPicker"
                      style="min-width: 280px"
                    />
                    <v-text-field
                      v-model="uploadDescription"
                      density="comfortable"
                      variant="solo-filled"
                      clearable
                      label="Optional description for all"
                      hide-details
                      style="min-width: 260px"
                    />
                    <v-btn
                      color="primary"
                      :disabled="!pendingUploads.length || uploading"
                      :loading="uploading"
                      prepend-icon="mdi-upload"
                      @click="startUpload"
                    >
                      Upload
                    </v-btn>
                  </div>
                </div>

                <!-- Upload queue / progress -->
                <div v-if="pendingUploads.length" class="mt-4">
                  <v-alert type="info" variant="tonal" class="mb-3">
                    Files queued: {{ pendingUploads.length }}
                  </v-alert>
                  <v-table density="compact">
                    <thead>
                      <tr>
                        <th>File</th><th>Size</th><th>Status</th><th style="width:220px">Progress</th><th></th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="u in pendingUploads" :key="u.id">
                        <td>{{ u.file.name }}</td>
                        <td>{{ humanSize(u.file.size) }}</td>
                        <td>
                          <v-chip size="x-small" :color="u.statusColor" variant="elevated">
                            {{ u.status }}
                          </v-chip>
                        </td>
                        <td>
                          <v-progress-linear :model-value="u.progress" height="8" rounded></v-progress-linear>
                        </td>
                        <td class="text-right">
                          <v-btn size="small" icon="mdi-close" variant="text" @click="removeFromQueue(u)" />
                        </td>
                      </tr>
                    </tbody>
                  </v-table>
                </div>
              </v-sheet>

              <!-- List + search -->
              <div class="d-flex justify-space-between align-center mt-6 mb-2">
                <div class="text-subtitle-1">Uploaded files</div>
                <v-text-field
                  v-model="attachSearch"
                  density="compact"
                  label="Search"
                  prepend-inner-icon="mdi-magnify"
                  hide-details
                  style="max-width: 340px;"
                />
              </div>

              <v-data-table
                :headers="attachHeadersRich"
                :items="filteredAttachments"
                :items-per-page="10"
                item-key="id"
              >
                <!-- filename cell -->
                <template #item.filename="{ item }">
                  <div class="d-flex align-center ga-2">
                    <v-icon>{{ fileIcon(item.mime_type) }}</v-icon>
                    <a class="attach-link" :href="downloadUrl(item)" target="_blank" rel="noopener">
                      {{ item.filename }}
                    </a>
                  </div>
                </template>



                <template #item.size="{ item }">
                  {{ humanSize(item.size) || '—' }}
                </template>

                <template #item.meta="{ item }">
                  <div class="text-caption">
                    <div v-if="item.created_at">Added: {{ formatDateTime(item.created_at) }}</div>
                    <div v-if="item.created_by">By: {{ item.created_by }}</div>
                    <div v-if="item.checksum">Checksum: {{ item.checksum.slice(0, 10) }}…</div>
                  </div>
                </template>

                <template #item.description="{ item }">
                  <v-text-field
                    v-model="item._descDraft"
                    density="compact"
                    variant="underlined"
                    hide-details
                    placeholder="Add a note..."
                    @blur="commitDescription(item)"
                  />
                </template>

                <!-- actions cell -->
                <template #item.actions="{ item }">
                  <div class="d-flex align-center justify-center" style="gap:6px;">
                    <v-btn size="small" icon="mdi-open-in-new" variant="text" :href="downloadUrl(item)" target="_blank" />
                    <v-btn size="small" icon="mdi-content-copy" variant="text" @click="copyLink(downloadUrl(item))" />
                    <v-btn size="small" icon="mdi-delete" variant="text" color="error" @click="deleteAttachment(item)" />
                  </div>
                </template>
              </v-data-table>
            </v-expansion-panel-text>
          </v-expansion-panel>


          <!-- ============ NOTES (timeline) ============ -->
          <v-expansion-panel value="notes">
            <v-expansion-panel-title>
              <v-icon class="mr-2">mdi-note-text</v-icon> Notes
            </v-expansion-panel-title>

            <v-expansion-panel-text>
              <!-- Toolbar -->
              <div class="d-flex flex-wrap align-center ga-2 mb-3">
                <v-btn color="primary" prepend-icon="mdi-plus" @click="openNoteDialog()">Add note</v-btn>
                <v-spacer />
                <v-select
                  v-model="noteVisibilityFilter"
                  :items="[{title:'All', value:''},{title:'Internal', value:'internal'},{title:'External', value:'external'}]"
                  hide-details
                  density="compact"
                  label="Visibility"
                  style="max-width: 180px;"
                  clearable
                />
                <v-text-field
                  v-model="noteSearch"
                  density="compact"
                  hide-details
                  prepend-inner-icon="mdi-magnify"
                  label="Search notes"
                  style="max-width: 280px;"
                  clearable
                />
              </div>

              <!-- Timeline -->
              <v-timeline density="compact" align="start">
                <v-timeline-item
                  v-for="n in filteredNotes"
                  :key="n.id"
                  :dot-color="avatarColor(n)"
                  size="small"
                >
                  <template #icon>
                    <v-avatar size="28" class="elevated-avatar">
                      <span class="text-caption">{{ initials(n) }}</span>
                    </v-avatar>
                  </template>

                  <div class="d-flex align-start justify-space-between ga-4">
                    <div class="flex-1-1">
                      <div class="d-flex align-center ga-2">
                        <div class="text-subtitle-2">{{ n.title }}</div>
                        <v-chip size="x-small" variant="tonal" :color="n.visibility === 'internal' ? 'indigo' : 'teal'" v-if="n.visibility">
                          {{ n.visibility }}
                        </v-chip>
                      </div>
                      <div class="text-body-2" style="white-space:pre-wrap">{{ n.body }}</div>
                      <div class="text-caption text-medium-emphasis mt-1">
                        <v-icon size="14" class="mr-1">mdi-clock-outline</v-icon>
                        <span v-if="n.created_at">{{ formatFromNow(n.created_at) }} · {{ formatDateTime(n.created_at) }}</span>
                      </div>
                    </div>

                    <div class="d-flex align-center ga-1">
                      <v-btn size="small" icon="mdi-pencil" variant="text" @click="openNoteDialog(n)" />
                      <v-btn size="small" icon="mdi-delete" variant="text" color="error" @click="deleteNote(n)" />
                    </div>
                  </div>
                </v-timeline-item>

                <div v-if="!filteredNotes.length" class="text-medium-emphasis py-4 text-center">
                  No notes yet
                </div>
              </v-timeline>

              <!-- Dialog (unchanged) -->
              <v-dialog v-model="noteDialog.open" max-width="760">
                <v-card>
                  <v-card-title class="text-h6">{{ noteDialog.editId ? 'Edit' : 'Add' }} Note</v-card-title>
                  <v-card-text>
                    <v-form @submit.prevent="saveNote">
                      <v-text-field v-model="noteDialog.model.title" label="Title*" density="compact" />
                      <v-select v-model="noteDialog.model.visibility" :items="['internal','external']" label="Visibility" clearable density="compact" />
                      <v-textarea v-model="noteDialog.model.body" label="Body*" rows="5" auto-grow density="compact" />
                    </v-form>
                  </v-card-text>
                  <v-card-actions>
                    <v-spacer />
                    <v-btn variant="text" @click="noteDialog.open=false">Cancel</v-btn>
                    <v-btn color="primary" @click="saveNote" :loading="savingNote">Save</v-btn>
                  </v-card-actions>
                </v-card>
              </v-dialog>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, watch, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { QuillEditor } from '@vueup/vue-quill'
import DOMPurify from 'dompurify'
import '@vueup/vue-quill/dist/vue-quill.snow.css'


const UPLOAD_URL = '/api/interlinkage-attachments/upload'

const analysisMode = ref('preview')

const route = useRoute()
const router = useRouter()
const id = computed(() => Number(route.params.id))

const { resource, notify } = useApi()

// main + child APIs
const api    = resource('interlinkages')
const anApi  = resource('interlinkage-analyses')
const depApi = resource('interdependences')
const expApi = resource('exposures')
const attApi = resource('interlinkage-attachments')
const noteApi= resource('interlinkage-notes')

// referentials
const leApi  = resource('legal-entities')
const prjApi = resource('projects')
const praApi = resource('pra-activities')
const cptApi = resource('counterparty-types')
const facApi = resource('facilities')
const insApi = resource('instruments')
const curApi = resource('currencies')

const statusOptions = ['draft','validated','archived','deleted']
const interdepTypes = ['ownership','credit','guarantee','management','technical','juridical','legal','contractual','equity','funding','governance','strategic','other']
const interdepLevels= ['low','medium','high','critical']

// UI
const openPanels = ref(['core','analysis','interdependences','exposures']) // default opened

// referentials
const legalEntities = ref([])
const projects = ref([])
const praActivities = ref([])
const counterpartyTypes = ref([])
const facilities = ref([])
const instruments = ref([])
const currencies = ref([])

// core model
const core = ref({
  sponsor_id:null, counterparty_id:null, booking_entity_id:null,
  project_id:null, pra_activity_id:null, counterparty_type_id:null,
  facility_id:null, instrument_id:null,
  deal_date:'', effective_date:'', maturity_date:'',
  notional_amount:'', currency_id:null,
  status:'draft', purpose:'', remarks:'',
})

function byId(arr, id) { return arr?.find?.(x => x.id === id) || null }

function leName(id) {
  const le = byId(legalEntities.value, id)
  if (!le) return ''
  return le.rmpm_code ? `${le.name} [${le.rmpm_code}]` : le.name
}
function praLabel(id) { return byId(praActivities.value, id)?.label || '' }
function cptLabel(id) { return byId(counterpartyTypes.value, id)?.label || '' }
function facilityRef(id){ return byId(facilities.value, id)?.reference || '' }
function instrumentRef(id){ return byId(instruments.value, id)?.reference || '' }

function formatDate(d) {
  if (!d) return ''
  try { return new Date(d).toLocaleDateString() } catch { return d }
}
function formatMoney(v, ccy) {
  if (v == null || v === '') return ''
  const n = Number(v)
  if (!Number.isFinite(n)) return String(v)
  try { return new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(n) + (ccy ? ` ${ccy}` : '') }
  catch { return `${n}${ccy ? ' ' + ccy : ''}` }
}
function statusColor(s) {
  switch ((s || '').toLowerCase()) {
    case 'validated': return 'green'
    case 'archived':  return 'grey'
    case 'deleted':   return 'red'
    default:          return 'blue'
  }
}

const currentProject = computed(() =>
  projects.value.find(p => p.id === core.value.project_id) || null
)
const currentProjectName = computed(() => currentProject.value?.name || '')


const savingCore = ref(false)


function newInterdepDefaults() {
  return {
    interdependence_identifier: 'DEP-' + createRandomString(6),
    type: null,
    level: null,
    project_id: core.value.project_id || null,
    project_name: currentProjectName.value || '',
    effective_date: '',
    expiry_date: '',
    risk_assessment: '',
  }
}

const titleParts = computed(() => {
  const pr = projects.value.find(p => p.id === core.value.project_id)
  return { project: pr?.name || '' }
})

function leItemTitle(le) {
  if (!le) return ''
  const code = le.rmpm_code ? ` [${le.rmpm_code}]` : ''
  return `${le.name}${code}`
}
function projectName(id) { return projects.value.find(p => p.id === id)?.name || '' }
function currencyCode(id) { return currencies.value.find(c => c.id === id)?.code || '' }

function normalizeCore(r) {
  core.value = {
    sponsor_id: r.sponsor_id ?? null,
    counterparty_id: r.counterparty_id ?? null,
    booking_entity_id: r.booking_entity_id ?? null,
    project_id: r.project_id ?? null,
    pra_activity_id: r.pra_activity_id ?? null,
    counterparty_type_id: r.counterparty_type_id ?? null,
    facility_id: r.facility_id ?? null,
    instrument_id: r.instrument_id ?? null,
    deal_date: r.deal_date || '',
    effective_date: r.effective_date || '',
    maturity_date: r.maturity_date || '',
    notional_amount: r.notional_amount != null ? String(r.notional_amount) : '',
    currency_id: r.currency_id ?? null,
    status: r.status || 'draft',
    purpose: r.purpose || '',
    remarks: r.remarks || '',
  }
}

async function loadCore() {
  const r = await api.get(id.value)
  normalizeCore(r || {})
}

// analysis
const analysis = reactive({
  id: null,
  content: ''
})

const sanitizedAnalysis = computed(() => DOMPurify.sanitize(analysis.content || ''))

const savingAnalysis = ref(false)
async function loadAnalysis() {
  try {
    const r = await anApi.list({
      interlinkage_id: id.value,
      page: 1,
      page_size: 1,
      sort: 'id:desc' // ensure latest (or only) analysis
    })
    const a = (r.items || [])[0]
    if (a) {
      Object.assign(analysis, { id: a.id, content: a.content || '' })
    } else {
      Object.assign(analysis, { id: null, content: '' })
    }
    analysisMode.value = analysis.content ? 'preview' : 'edit'
  } catch {
    Object.assign(analysis, { id: null, content: '' })
    analysisMode.value = 'edit'
  }
}

async function saveAnalysis() {
  try {
    savingAnalysis.value = true
    if (analysis.id) {
      await anApi.update(
        analysis.id,
        { interlinkage_id: id.value, content: analysis.content || '' },
        'Analysis saved'
      )
    } else {
      const r = await anApi.create(
        { interlinkage_id: id.value, content: analysis.content || '' },
        'Analysis saved'
      )
      analysis.id = r.id
    }
    analysisMode.value = 'preview'
  } catch (e) {
    notify?.error(e?.message || 'Failed to save analysis')
  } finally {
    savingAnalysis.value = false
  }
}


// interdependences
const interdepHeaders = [
  { key:'interdependence_identifier', title:'Identifier' },
  { key:'type', title:'Type' },
  { key:'level', title:'Level' },
  { key:'project', title:'Project' },
  { key:'effective_date', title:'Effective' },
  { key:'expiry_date', title:'Expiry' },
  { key:'actions', title:'Actions', sortable:false, width:110 },
]
const interdeps = ref([])
const interdepDialog = ref({
  open:false,
  editId:null,
  model:newInterdepDefaults()
})
const savingInterdep = ref(false)

function createRandomString(length) {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let result = "";
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

async function loadInterdeps() {
  const r = await depApi.list({ interlinkage_id: id.value, page:1, page_size:1000, sort:'interdependence_identifier:asc' })
  interdeps.value = r.items || []
}
function openInterdepDialog(row) {
  if (row) {
    interdepDialog.value.editId = row.id
    interdepDialog.value.model = {
      interdependence_identifier: row.interdependence_identifier || 'DEP-' + createRandomString(6),
      type: row.type || null,
      level: row.level || null,
      project_id: row.project_id ?? core.value.project_id ?? null,
      project_name: row.project_name ?? currentProjectName.value ?? '',
      effective_date: row.effective_date || '',
      expiry_date: row.expiry_date || '',
      risk_assessment: row.risk_assessment || '',
    }
  } else {
    interdepDialog.value.editId = null
    interdepDialog.value.model = newInterdepDefaults()
  }
  interdepDialog.value.open = true
}
async function saveInterdep() {
  const p = { ...interdepDialog.value.model, interlinkage_id: id.value }
  if (!p.interdependence_identifier) { notify?.error('Identifier is required'); return }
  try {
    savingInterdep.value = true
    if (interdepDialog.value.editId) {
      await depApi.update(interdepDialog.value.editId, p, 'Interdependence saved')
    } else {
      await depApi.create(p, 'Interdependence added')
    }
    interdepDialog.value.open = false
    await loadInterdeps()
  } catch (e) {
    const msg = String(e?.message || '')
    if (msg.toLowerCase().includes('uq_interdep_per_interlinkage')) {
      notify?.error('Identifier must be unique per interlinkage')
    } else {
      notify?.error('Save failed')
    }
  } finally {
    savingInterdep.value = false
  }
}
async function deleteInterdep(row) {
  try {
    await depApi.remove(row.id, false, 'Interdependence deleted') // hard delete ok
    await loadInterdeps()
  } catch (e) {
    notify?.error(e?.message || 'Delete failed')
  }
}

watch(() => core.value.project_id, () => {
  if (interdepDialog.value.open && !interdepDialog.value.editId) {
    interdepDialog.value.model.project_id = core.value.project_id
    interdepDialog.value.model.project_name = currentProjectName.value
  }
})

// exposures
const exposureHeaders = [
  { key:'as_of_date', title:'As of' },
  { key:'currency', title:'CCY' },
  { key:'ead', title:'EAD' },
  { key:'undrawn', title:'Undrawn' },
  { key:'mtm', title:'MTM' },
  { key:'pnl', title:'PnL' },
  { key:'rwa', title:'RWA' },
  { key:'pd', title:'PD' },
  { key:'lgd', title:'LGD' },
  { key:'fx_to_reporting', title:'FX→rep' },
  { key:'actions', title:'Actions', sortable:false, width:110 },
]
const exposures = ref([])
const exposureDialog = ref({
  open:false,
  editId:null,
  model:{
    as_of_date:'', currency_id:null,
    ead:'', undrawn:'', mtm:'', pnl:'',
    rwa:'', pd:'', lgd:'', fx_to_reporting:'',
  }
})
const savingExposure = ref(false)

async function loadExposures() {
  const r = await expApi.list({ interlinkage_id:id.value, page:1, page_size:1000, sort:'as_of_date:desc' })
  exposures.value = r.items || []
}
function openExposureDialog(row) {
  if (row) {
    exposureDialog.value.editId = row.id
    exposureDialog.value.model = {
      as_of_date: row.as_of_date || '',
      currency_id: row.currency_id || null,
      ead: str(row.ead),
      undrawn: str(row.undrawn),
      mtm: str(row.mtm),
      pnl: str(row.pnl),
      rwa: str(row.rwa),
      pd: str(row.pd),
      lgd: str(row.lgd),
      fx_to_reporting: str(row.fx_to_reporting),
    }
  } else {
    exposureDialog.value.editId = null
    exposureDialog.value.model = {
      as_of_date:'', currency_id:null,
      ead:'', undrawn:'', mtm:'', pnl:'',
      rwa:'', pd:'', lgd:'', fx_to_reporting:'',
    }
  }
  exposureDialog.value.open = true
}
function numOrNull(v) { if (v === '' || v == null) return null; const n = Number(v); return Number.isFinite(n) ? n : null }
function str(v) { return (v == null) ? '' : String(v) }
async function saveExposure() {
  const p = { ...exposureDialog.value.model, interlinkage_id:id.value }
  if (!p.as_of_date || !p.currency_id) { notify?.error('As-of date and currency are required'); return }
  // cast numeric
  ;['ead','undrawn','mtm','pnl','rwa','pd','lgd','fx_to_reporting'].forEach(k => p[k] = numOrNull(p[k]))
  try {
    savingExposure.value = true
    if (exposureDialog.value.editId) {
      await expApi.update(exposureDialog.value.editId, p, 'Exposure saved')
    } else {
      await expApi.create(p, 'Exposure added')
    }
    exposureDialog.value.open = false
    await loadExposures()
  } catch (e) {
    const msg = String(e?.message || '')
    if (msg.toLowerCase().includes('uq_exposure_timeseries')) {
      notify?.error('A snapshot for this date already exists')
    } else {
      notify?.error('Save failed')
    }
  } finally {
    savingExposure.value = false
  }
}
async function deleteExposure(row) {
  try {
    await expApi.remove(row.id, false, 'Exposure deleted')
    await loadExposures()
  } catch (e) {
    notify?.error(e?.message || 'Delete failed')
  }
}

// attachments (stub CRUD)

function downloadUrl(item) {
  return `/api/interlinkage-attachments/${item.id}/download`
}
const attachHeadersRich = [
  { key:'filename', title:'File' },
  { key:'mime_type', title:'MIME' },
  { key:'size', title:'Size' },
  { key:'meta', title:'Meta' },
  { key:'description', title:'Description' },
  { key:'actions', title:'', sortable:false, width:130 },
]

const attachments = ref([])
const attachSearch = ref('')

// Upload state
const isDragging = ref(false)
const fileInput = ref(null)
const pendingUploads = ref([]) // [{id, file, progress, status, statusColor, description}]
const uploading = ref(false)
const uploadDescription = ref('')

function fileIcon(mime){
  const m = (mime || '').toLowerCase()
  if (m.includes('pdf')) return 'mdi-file-pdf-box'
  if (m.includes('image')) return 'mdi-file-image'
  if (m.includes('excel') || m.includes('spreadsheet')) return 'mdi-file-excel'
  if (m.includes('word')) return 'mdi-file-word'
  if (m.includes('zip') || m.includes('tar') || m.includes('gz')) return 'mdi-folder-zip'
  if (m.includes('text') || m.includes('plain')) return 'mdi-file-document-outline'
  return 'mdi-file'
}
function humanSize(bytes){
  if (!Number.isFinite(bytes)) return ''
  const units = ['B','KB','MB','GB','TB']
  let i = 0, v = bytes
  while (v >= 1024 && i < units.length-1) { v /= 1024; i++ }
  return `${v.toFixed(v >= 10 || i === 0 ? 0 : 1)} ${units[i]}`
}

function newQueueItem(file) {
  return {
    id: `${file.name}-${file.size}-${file.lastModified}-${Math.random().toString(36).slice(2)}`,
    file,
    progress: 0,
    status: 'queued',
    statusColor: 'grey',
    description: uploadDescription.value?.trim() || ''
  }
}
function onDragOver(){ isDragging.value = true }
function onDragLeave(){ isDragging.value = false }
function onDrop(e){
  isDragging.value = false
  const files = Array.from(e.dataTransfer.files || [])
  queueFiles(files)
}
function queueFilesFromPicker(){
  if (!fileInput.value) return
  const files = Array.isArray(fileInput.value) ? fileInput.value : [fileInput.value]
  queueFiles(files.filter(Boolean))
  fileInput.value = null
}
function queueFiles(files){
  const add = files.map(f => newQueueItem(f))
  pendingUploads.value = [...pendingUploads.value, ...add]
}
function removeFromQueue(u){
  pendingUploads.value = pendingUploads.value.filter(x => x.id !== u.id)
}

async function startUpload(){
  if (!pendingUploads.value.length) return
  uploading.value = true
  try {
    for (const u of pendingUploads.value) {
      u.status = 'uploading'; u.statusColor = 'blue'
      await uploadOne(u) // POST multipart to /api/interlinkage-attachments/upload
      u.status = 'done'; u.statusColor = 'green'; u.progress = 100
    }
    notify?.success?.('Upload complete')
    pendingUploads.value = []
    await loadAttachments() // refresh list
  } catch (e) {
    notify?.error?.(e?.message || 'Some uploads failed')
  } finally {
    uploading.value = false
  }
}

async function uploadOne(u){
  const fd = new FormData()
  fd.append('interlinkage_id', String(id.value))
  fd.append('description', u.description || uploadDescription.value || '')
  fd.append('file', u.file, u.file.name)

  await new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', UPLOAD_URL, true)
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) u.progress = Math.round((e.loaded / e.total) * 100)
    }
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve()
      else reject(new Error(`Upload failed (${xhr.status})`))
    }
    xhr.onerror = () => reject(new Error('Network error during upload'))
    xhr.send(fd)
  })
}

// CRUD: list, inline description update, delete
async function loadAttachments() {
  try {
    const r = await attApi.list({ interlinkage_id:id.value, page:1, page_size:1000, sort:'id:desc' })
    // If your /upload returns size/checksum (not stored in DB), they won't be present on list
    // unless you add columns. This is fine; UI shows "—" gracefully.
    const rows = (r.items || []).map(x => ({ ...x, _descDraft: x.description || '' }))
    attachments.value = rows
  } catch {
    attachments.value = []
  }
}
async function commitDescription(item){
  try {
    if ((item._descDraft || '') === (item.description || '')) return
    await attApi.update(item.id, {
      interlinkage_id: id.value,
      filename: item.filename,
      mime_type: item.mime_type,
      storage_uri: item.storage_uri,
      description: item._descDraft || ''
    }, 'Attachment updated')
    item.description = item._descDraft || ''
  } catch (e) {
    notify?.error(e?.message || 'Failed to update description')
    item._descDraft = item.description || ''
  }
}
async function deleteAttachment(row) {
  try {
    await attApi.remove(row.id, false, 'Attachment deleted')
    await loadAttachments()
  } catch (e) {
    notify?.error(e?.message || 'Delete failed')
  }
}
async function copyLink(url){
  try {
    await navigator.clipboard.writeText(url)
    notify?.success?.('Link copied')
  } catch { notify?.error?.('Copy failed') }
}

// search
const filteredAttachments = computed(() => {
  const q = (attachSearch.value || '').toLowerCase().trim()
  if (!q) return attachments.value
  return attachments.value.filter(a =>
    (a.filename || '').toLowerCase().includes(q) ||
    (a.mime_type || '').toLowerCase().includes(q) ||
    (a.description || '').toLowerCase().includes(q) ||
    (a.created_by || '').toLowerCase().includes(q)
  )
})

// notes (stub CRUD)
// notes (timeline)
import moment from 'moment' // npm i moment
// Optionally set locale:
// moment.locale(navigator.language || 'en')

const noteHeaders = [] // not used anymore, but kept if other code references it
const notes = ref([])
const noteSearch = ref('')
const noteVisibilityFilter = ref('')

const noteDialog = ref({ open:false, editId:null, model:{ title:'', body:'', visibility:null } })
const savingNote = ref(false)

async function loadNotes() {
  try {
    const r = await noteApi.list({ interlinkage_id:id.value, page:1, page_size:1000, sort:'id:desc' })
    notes.value = (r.items || [])
  } catch { notes.value = [] }
}

function openNoteDialog(row) {
  if (row) {
    noteDialog.value = { open:true, editId:row.id, model:{ title:row.title||'', body:row.body||'', visibility:row.visibility||null } }
  } else {
    noteDialog.value = { open:true, editId:null, model:{ title:'', body:'', visibility:null } }
  }
}
async function saveNote() {
  const p = { ...noteDialog.value.model, interlinkage_id:id.value }
  if (!p.title || !p.body) { notify?.error('Title and Body are required'); return }
  try {
    savingNote.value = true
    if (noteDialog.value.editId) await noteApi.update(noteDialog.value.editId, p, 'Note saved')
    else await noteApi.create(p, 'Note added')
    noteDialog.value.open = false
    await loadNotes()
  } catch (e) { notify?.error(e?.message || 'Save failed') }
  finally { savingNote.value = false }
}
async function deleteNote(row) {
  try { await noteApi.remove(row.id, false, 'Note deleted'); await loadNotes() }
  catch (e) { notify?.error(e?.message || 'Delete failed') }
}

// Helpers
function formatFromNow(dt) {
  try { return moment(dt).fromNow() } catch { return '' }
}
function initials(n) {
  // Use created_by if you have it; else derive from title
  const src = (n.created_by || n.title || '').trim()
  if (!src) return 'NA'
  const parts = src.split(/[\s._-]+/).filter(Boolean)
  const i1 = parts[0]?.[0] || ''
  const i2 = parts[1]?.[0] || ''
  return (i1 + i2).toUpperCase()
}
function avatarColor(n) {
  // deterministic color by hash of created_by/title
  const s = (n.created_by || n.title || 'x')
  let h = 0
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0
  const palette = ['primary','teal','indigo','deep-purple','cyan','pink','amber','orange','green','blue']
  return palette[h % palette.length]
}

// Sort & filter
const sortedNotes = computed(() => {
  return [...notes.value].sort((a,b) => {
    const da = new Date(a.created_at || 0).getTime()
    const db = new Date(b.created_at || 0).getTime()
    return db - da
  })
})
const filteredNotes = computed(() => {
  const q = (noteSearch.value || '').toLowerCase().trim()
  const vis = (noteVisibilityFilter.value || '').toLowerCase()
  return sortedNotes.value.filter(n => {
    const visMatch = !vis || (n.visibility || '').toLowerCase() === vis
    const qMatch = !q || [n.title, n.body, n.created_by, n.visibility].some(v => (v || '').toLowerCase().includes(q))
    return visMatch && qMatch
  })
})


// workflow (read-only)
function formatDateTime(dt) {
  if (!dt) return ''
  try {
    return new Date(dt).toLocaleString()
  } catch { return dt }
}

// save core
async function saveCore() {
  // cast number where needed
  const p = { ...core.value }
  if (p.notional_amount === '') delete p.notional_amount
  else if (typeof p.notional_amount === 'string') p.notional_amount = Number(p.notional_amount)
  if (!p.sponsor_id || !p.counterparty_id || !p.project_id || !p.status) {
    notify?.error('Sponsor, Counterparty, Project and Status are required')
    return
  }
  try {
    savingCore.value = true
    await api.update(id.value, p, 'Interlinkage saved')
    await loadCore()
  } catch (e) {
    const msg = String(e?.message || '')
    if (msg.toLowerCase().includes('uq_interlinkage_natural')) {
      notify?.error('An interlinkage with same Sponsor / Project / Counterparty / Deal Date already exists')
    } else {
      notify?.error('Save failed')
    }
  } finally {
    savingCore.value = false
  }
}

// bootstrap
async function loadRefs() {
  const [les, prj, pra, cpt, fac, ins, cur] = await Promise.all([
    leApi.list({ page:1, page_size:1000, sort:'name:asc' }),
    prjApi.list({ page:1, page_size:1000, sort:'name:asc' }),
    praApi.list({ page:1, page_size:1000, sort:'label:asc' }),
    cptApi.list({ page:1, page_size:1000, sort:'label:asc' }),
    facApi.list({ page:1, page_size:1000, sort:'reference:asc' }),
    insApi.list({ page:1, page_size:1000, sort:'reference:asc' }),
    curApi.list({ page:1, page_size:1000, sort:'code:asc' }),
  ])
  legalEntities.value = les.items || []
  projects.value = prj.items || []
  praActivities.value = pra.items || []
  counterpartyTypes.value = cpt.items || []
  facilities.value = fac.items || []
  instruments.value = ins.items || []
  currencies.value = cur.items || []
}

async function loadAll() {
  await Promise.all([
    loadCore(),
    loadAnalysis(),
    loadInterdeps(),
    loadExposures(),
    loadAttachments(),
    loadNotes(),
  ])
}

watch(id, async () => { await loadAll() }, { immediate: true })
onMounted(async () => {
  await loadRefs()
})
</script>

<style scoped>
.d-grid { display: grid; }
.col-span-6 { grid-column: span 6; }
@media (max-width: 1200px) {
  .col-span-6 { grid-column: span 12; }
}

/* put inside <style scoped> */
.overview-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px 24px;
}
.overview-col {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.kv {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 8px;
  align-items: start;
}
.k {
  font-weight: 600;
  color: rgba(0,0,0,.6);
}
.v {
  min-height: 24px;
}
.kv-multiline .v {
  padding-top: 2px;
}
@media (max-width: 1200px) {
  .overview-grid { grid-template-columns: 1fr; }
  .kv { grid-template-columns: 150px 1fr; }
}
.upload-zone {
  border: 2px dashed rgba(0,0,0,.15);
  transition: all .15s ease;
  padding: 16px;
}
.upload-zone.dragging {
  border-color: var(--v-theme-primary);
  background: rgba(0,0,0,.02);
}
.zone-inner {
  display: grid;
  place-items: center;
  text-align: center;
  padding: 16px;
}
.attach-link {
  text-decoration: none;
}
.attach-link:hover {
  text-decoration: underline;
}
.elevated-avatar {
  box-shadow: 0 2px 6px rgba(0,0,0,.12);
  color: white;
}
</style>
