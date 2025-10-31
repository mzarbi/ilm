<script setup>
import { AdaptiveCardModel, shapesNS } from '@/graph/adaptive-card'

import { ref, watch, onMounted, nextTick } from 'vue'
import * as joint from 'jointjs'
import 'jointjs/dist/joint.css'

// ======================= Props / Emits =======================
const props = defineProps({
  open:   { type: Boolean, default: false },
  title:  { type: String,  default: 'Expiry Monitoring' },
  // backend payload from /analysis/expiry-monitoring
  payload:{ type: Object,  default: () => ({}) },
  // optional context (not required because backend now embeds names/ccy)
  context:{ type: Object,  default: () => ({ interlinkages: {}, entities: {}, currencies: {} }) }
})
const emit = defineEmits(['update:open'])

// ======================= Graph refs =======================
const el = ref(null)
let paper = null
let graph = null

// ======================= Helpers =======================
const safe = (v, d = '—') => (v == null || v === '' ? d : String(v))
const fmtAmt = (x, ccy = 'EUR') => {
  if (x == null) return '—'
  const n = Number(x)
  if (!isFinite(n)) return `${x} ${ccy || ''}`.trim()
  try {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency: ccy, maximumFractionDigits: 2 }).format(n)
  } catch {
    return `${x} ${ccy || ''}`.trim()
  }
}
const colorForBucket = (label = '') => {
  const l = String(label).toLowerCase()
  if (l.includes('overdue')) return { style: 'attention', edge: '#C62828' }         // red
  if (l.match(/(^|[^0-9])0-?3?0([^0-9]|$)/)) return { style: 'warning', edge: '#EF6C00' } // orange (0-30)
  if (l.match(/31-?9?0/)) return { style: 'warning', edge: '#F9A825' }              // amber (31-90)
  if (l.match(/91-?1?8?0/)) return { style: 'accent', edge: '#1565C0' }             // blue (91-180)
  if (l.startsWith('>')) return { style: 'good', edge: '#2E7D32' }                  // green (>last)
  return { style: 'default', edge: '#607D8B' }
}

// ======================= AdaptiveCard templates =======================
function ilExpiryCardTemplate(it) {
  // it: {id, sponsor_name, counterparty_name, currency_code, notional_amount, maturity_date, days_to_maturity, bucket, measure?}
  const sponsor = safe(it.sponsor_name)
  const cpty    = safe(it.counterparty_name)
  const ccy     = safe(it.currency_code || 'EUR')
  const amount  = fmtAmt(it.notional_amount, ccy)
  const days    = it.days_to_maturity
  const whenTxt = days == null ? '—' : (days < 0 ? `${Math.abs(days)} day(s) overdue` : `${days} day(s)`)

  const { style } = colorForBucket(it.bucket)

  return {
    type: 'AdaptiveCard',
    $schema: 'http://adaptivecards.io/schemas/adaptive-card.json',
    version: '1.5',
    body: [
      {
        type: 'Container',
        style,
        bleed: true,
        items: [
          { type: 'TextBlock', text: `Interlinkage #${it.id}`, weight: 'Bolder', size: 'Medium', wrap: true },
          { type: 'TextBlock', text: `Bucket: ${safe(it.bucket)}`, size: 'Small', isSubtle: true, spacing: 'None' }
        ]
      },
      {
        type: 'Container',
        spacing: 'Small',
        items: [
          {
            type: 'ColumnSet',
            columns: [
              {
                type: 'Column', width: 'stretch',
                items: [{ type: 'TextBlock', text: sponsor, weight: 'Bolder', size: 'Small', wrap: true, color: 'Accent' }]
              },
              {
                type: 'Column', width: 'auto',
                items: [{ type: 'TextBlock', text: '→', size: 'Medium', weight: 'Bolder', horizontalAlignment: 'Center' }]
              },
              {
                type: 'Column', width: 'stretch',
                items: [{ type: 'TextBlock', text: cpty, weight: 'Bolder', size: 'Small', wrap: true, color: 'Good' }]
              }
            ]
          }
        ]
      },
      {
        type: 'ColumnSet',
        spacing: 'Small',
        columns: [
          {
            type: 'Column', width: 'stretch',
            items: [
              { type: 'TextBlock', text: 'Notional', isSubtle: true, size: 'Small' },
              { type: 'TextBlock', text: amount, weight: 'Bolder', size: 'Small' }
            ]
          },
          {
            type: 'Column', width: 'auto',
            items: [
              { type: 'TextBlock', text: 'Currency', isSubtle: true, size: 'Small' },
              { type: 'TextBlock', text: ccy, weight: 'Bolder', size: 'Small' }
            ]
          }
        ]
      },
      {
        type: 'ColumnSet',
        spacing: 'Small',
        columns: [
          {
            type: 'Column', width: 'stretch',
            items: [
              { type: 'TextBlock', text: 'Maturity', isSubtle: true, size: 'Small' },
              { type: 'TextBlock', text: safe(it.maturity_date), weight: 'Bolder', size: 'Small' }
            ]
          },
          {
            type: 'Column', width: 'stretch',
            items: [
              { type: 'TextBlock', text: 'Time Left', isSubtle: true, size: 'Small' },
              { type: 'TextBlock', text: whenTxt, weight: 'Bolder', size: 'Small' }
            ]
          }
        ]
      }
    ]
  }
}

function bucketCardTemplate(bucket) {
  // bucket: {label, count, total_notional:[{currency_code, amount}]}
  const { style } = colorForBucket(bucket.label)
  const totalsText = (bucket.total_notional || [])
    .map(t => `${fmtAmt(t.amount, t.currency_code || 'EUR')}`)
    .join('  •  ') || '—'

  return {
    type: 'AdaptiveCard',
    $schema: 'http://adaptivecards.io/schemas/adaptive-card.json',
    version: '1.5',
    body: [
      {
        type: 'Container',
        style,
        bleed: true,
        items: [
          { type: 'TextBlock', text: `Bucket — ${safe(bucket.label)}`, weight: 'Bolder', size: 'Medium', wrap: true },
          { type: 'TextBlock', text: `Items: ${bucket.count}`, spacing: 'None', isSubtle: true }
        ]
      },
      {
        type: 'Container',
        spacing: 'Small',
        items: [
          { type: 'TextBlock', text: 'Total Notional', isSubtle: true, size: 'Small' },
          { type: 'TextBlock', text: totalsText, weight: 'Bolder', size: 'Small', wrap: true }
        ]
      }
    ]
  }
}

// ======================= Node factories =======================
function makeBucketNode(g, bucket) {
  const id = `bucket:${bucket.label}`
  const cell = new AdaptiveCardModel({
    id,
    size: { width: 300, height: 120 },
    template: bucketCardTemplate(bucket)
  })
  cell.set('typeTag', 'bucket')
  cell.set('data', { label: bucket.label })
  cell.addTo(g)
  return cell
}

function makeILCard(g, it) {
  const cell = new AdaptiveCardModel({
    id: `il-${it.id}`,
    size: { width: 280, height: 120 },
    template: ilExpiryCardTemplate(it)
  })
  cell.set('typeTag', 'interlinkage')
  cell.set('data', it)
  cell.addTo(g)
  return cell
}

function makeLink(a, b, label = '') {
  const edgeColor = colorForBucket(b.get('data')?.label || '').edge
  const l = new joint.shapes.standard.Link()
  l.source(a)
  l.target(b)
  l.attr({
    line: {
      stroke: edgeColor || '#607D8B',
      strokeWidth: 1.5,
      targetMarker: { type: 'classic', stroke: edgeColor || '#607D8B', fill: edgeColor || '#607D8B' }
    }
  })
  if (label) {
    l.appendLabel({ attrs: { text: { text: label, fontSize: 11, fill: '#37474F' } }, position: 0.5 })
  }
  l.addTo(graph)
  return l
}

// ======================= Layout =======================
// Two-lane grid: ILs left, Buckets right, grouped by bucket label
function layoutGrid(bucketNodes, ilNodesByBucket) {
  const LEFT_X  = 80
  const RIGHT_X = 760
  const GAP_Y   = 18
  const BLOCK_GAP = 44
  const IL_H    = 120
  const CL_H    = 120

  let cursorY = 40
  for (const b of bucketNodes) {
    b.position(RIGHT_X, cursorY)

    const arr = ilNodesByBucket.get(b.get('data').label) || []
    let y = cursorY
    arr.forEach(n => {
      n.position(LEFT_X, y)
      y += IL_H + GAP_Y
    })

    const blockHeight = Math.max(CL_H, arr.length * (IL_H + GAP_Y) - GAP_Y)
    cursorY += blockHeight + BLOCK_GAP
  }

  if (paper && typeof paper.scaleContentToFit === 'function') {
    paper.scaleContentToFit({ padding: 30 })
  }
}

// ======================= Build graph =======================
function buildFromPayload(data) {
  graph.clear()

  const items   = Array.isArray(data?.items) ? data.items : []
  const buckets = Array.isArray(data?.buckets) ? data.buckets : []
  const overlayNodes = Array.isArray(data?.overlay?.nodes) ? data.overlay.nodes : []
  const overlayLinks = Array.isArray(data?.overlay?.links) ? data.overlay.links : []

  const bucketNodes = []
  const ilNodesByBucket = new Map()
  const ilNodeById = new Map()
  const bucketNodeByLabel = new Map()

  // Preferred path: we got structured buckets + items
  if (buckets.length) {
    // 1) bucket nodes
    for (const b of buckets) {
      if (b.count <= 0) continue
      const bn = makeBucketNode(graph, b)
      bucketNodes.push(bn)
      bucketNodeByLabel.set(b.label, bn)
    }

    // 2) IL nodes, group under bucket, link
    for (const it of items) {
      if (!it.bucket || !bucketNodeByLabel.has(it.bucket)) continue
      let pill = ilNodeById.get(it.id)
      if (!pill) {
        pill = makeILCard(graph, it)
        ilNodeById.set(it.id, pill)
      }
      const arr = ilNodesByBucket.get(it.bucket) || []
      arr.push(pill)
      ilNodesByBucket.set(it.bucket, arr)

      const label = (typeof it.days_to_maturity === 'number')
        ? (it.days_to_maturity < 0 ? `${Math.abs(it.days_to_maturity)}d overdue` : `${it.days_to_maturity}d`)
        : 'expires-in'
      makeLink(pill, bucketNodeByLabel.get(it.bucket), label)
    }
  } else if (overlayNodes.length) {
    // Fallback to overlay-only descriptions
    const nodeMap = new Map()
    for (const n of overlayNodes) {
      if (n.kind === 'bucket') {
        const bn = makeBucketNode(graph, { label: n.label, count: n.count ?? 0, total_notional: [] })
        bucketNodes.push(bn)
        bucketNodeByLabel.set(n.label, bn)
        nodeMap.set(n.id || `bucket:${n.label}`, bn)
      } else if (n.kind === 'interlinkage') {
        // If overlay provides IL ids only, we can't enrich; show minimal card
        const pill = makeILCard(graph, {
          id: n.id,
          sponsor_name: '—', counterparty_name: '—',
          currency_code: 'EUR', notional_amount: null,
          maturity_date: '—', days_to_maturity: null, bucket: '—'
        })
        ilNodeById.set(n.id, pill)
        nodeMap.set(`il:${n.id}`, pill)
      }
    }
    for (const e of overlayLinks) {
      const a = nodeMap.get(e.from) || nodeMap.get(`il:${e.from}`)
      const b = nodeMap.get(e.to)   || nodeMap.get(`bucket:${e.to}`)
      if (a && b) {
        // Best-effort: attempt to add to grouping map using b's label
        const lbl = b.get('data')?.label
        const arr = ilNodesByBucket.get(lbl) || []
        if (!arr.includes(a)) arr.push(a)
        ilNodesByBucket.set(lbl, arr)
        makeLink(a, b, e.label || 'expires-in')
      }
    }
  }

  layoutGrid(bucketNodes, ilNodesByBucket)
}

// ======================= Init / Zoom-Pan =======================
function init() {
  if (paper) { try { paper.remove() } catch(_){} paper = null }
  if (el.value) el.value.innerHTML = ''

  graph = new joint.dia.Graph({}, { cellNamespace: shapesNS })
  paper = new joint.dia.Paper({
    el: el.value,
    model: graph,
    width: '100%',
    height: 640,
    gridSize: 10,
    drawGrid: true,
    background: { color: '#FAFAFA' },
    interactive: { linkMove: false },
    defaultRouter: { name: 'orthogonal' },
    defaultConnector: { name: 'rounded' },
    cellViewNamespace: shapesNS
  })

  setupZoomPan(paper)
  paper.on('element:pointerdown', (view) => {
    const d = view.model.get('data')
    // hook for future: show a small tooltip or side panel
    // console.log(view.model.get('typeTag'), d)
  })
}

function setupZoomPan(paper) {
  // Pan
  let panning = false
  let panStart = { x: 0, y: 0 }
  let originStart = { x: 0, y: 0 }

  paper.on('blank:pointerdown', (evt, x, y) => {
    panning = true
    panStart = { x, y }
    originStart = paper.options.origin || { x: 0, y: 0 }
  })
  const stopPan = () => { panning = false }
  paper.on('blank:pointerup', stopPan)
  paper.on('cell:pointerup', stopPan)
  paper.on('blank:pointermove', (evt, x, y) => {
    if (!panning) return
    const dx = x - panStart.x
    const dy = y - panStart.y
    paper.setOrigin(originStart.x + dx, originStart.y + dy)
  })

  // Zoom to pointer
  const elNode = paper.el
  elNode.addEventListener('wheel', (e) => {
    e.preventDefault()
    const rect = elNode.getBoundingClientRect()
    const clientX = e.clientX - rect.left
    const clientY = e.clientY - rect.top

    const cur = paper.scale().sx
    const factor = e.deltaY < 0 ? 1.1 : 1/1.1
    const next = clamp(cur * factor, 0.2, 3)

    const pLocal = clientToLocal(paper, clientX, clientY)
    paper.scale(next, next)
    const newLocal = clientToLocal(paper, clientX, clientY)

    const ox = (paper.options.origin?.x || 0) + (newLocal.x - pLocal.x) * next
    const oy = (paper.options.origin?.y || 0) + (newLocal.y - pLocal.y) * next
    paper.setOrigin(ox, oy)
  }, { passive: false })
}
function clamp(v, a, b) { return Math.max(a, Math.min(b, v)) }
function clientToLocal(paper, cx, cy) {
  const scale = paper.scale().sx || 1
  const origin = paper.options.origin || { x: 0, y: 0 }
  return { x: cx/scale - origin.x/scale, y: cy/scale - origin.y/scale }
}

// ======================= Lifecycle =======================
watch(() => props.open, async (v) => {
  if (!v) return
  await nextTick()
  init()
  buildFromPayload(props.payload || {})
})
onMounted(() => {
  if (props.open) {
    init()
    buildFromPayload(props.payload || {})
  }
})
</script>

<template>
  <v-dialog
    :model-value="open"
    @update:model-value="val => emit('update:open', val)"
    max-width="1200px"
    persistent
  >
    <v-card>
      <v-card-title class="d-flex align-center">
        <div class="text-h6">{{ title }}</div>
        <v-spacer />
        <v-chip class="mr-2" size="small" color="blue-lighten-4"  text-color="blue-darken-3">Bucket</v-chip>
        <v-chip class="mr-2" size="small" color="green-lighten-4" text-color="green-darken-3">Interlinkage</v-chip>
        <v-btn icon="mdi-close" variant="text" @click="emit('update:open', false)" />
      </v-card-title>
      <v-divider />
      <v-card-text>
        <div ref="el" style="width:100%; height:640px;"></div>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>
