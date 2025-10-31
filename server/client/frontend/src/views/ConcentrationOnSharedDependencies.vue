<script setup>
import { AdaptiveCardModel, shapesNS } from '@/graph/adaptive-card'

import { ref, watch, onMounted, nextTick } from 'vue'
import * as joint from 'jointjs'
import 'jointjs/dist/joint.css'
import dagre from 'dagre'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: 'Analysis' },
  payload: { type: Object, default: () => ({}) },
  // optional context from the parent (to enrich labels)
  context: {
    type: Object,
    default: () => ({ interlinkages: {}, entities: {}, currencies: {} })
  }
})
const emit = defineEmits(['update:open'])

const el = ref(null)
let paper = null
let graph = null

// --- helpers
const safe = (v, d = '—') => (v == null || v === '') ? d : String(v)
const fmtAmt = (x, ccy = 'EUR') => {
  if (x == null) return '—'
  try {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency: ccy, maximumFractionDigits: 2 })
      .format(Number(x))
  } catch {
    return `${x} ${ccy}`
  }
}
const levelsToBadge = (mix = {}) => {
  const parts = []
  const L = mix.low || 0, M = mix.medium || 0, H = mix.high || 0, C = mix.critical || 0
  if (L) parts.push(`L:${L}`)
  if (M) parts.push(`M:${M}`)
  if (H) parts.push(`H:${H}`)
  if (C) parts.push(`C:${C}`)
  return parts.length ? parts.join(' ') : '—'
}

function makeClusterNode(g, { id, identifier, depType, membersCount, total, totalCcy, levelsMix }) {
  const cell = new AdaptiveCardModel({
    id,
    size: { width: 300, height: 120 },
    template: clusterCardTemplate(identifier, depType, membersCount, { amount: total, ccy: totalCcy }, levelsMix)
  })
  cell.set('typeTag', 'cluster')
  cell.set('data', { id, identifier, depType })
  cell.addTo(g)
  return cell
}

function makeILCard(g, il, ctx) {
  const cell = new AdaptiveCardModel({
    id: `il-${il.id}`,
    size: { width: 260, height: 96 }, // compact; expands if needed
    template: interlinkageCardTemplateCompact(il, ctx)
  })
  cell.set('typeTag', 'interlinkage')
  cell.set('data', il)
  cell.addTo(g)
  return cell
}

function makeLink(a, b, label = 'shares dep') {
  const l = new joint.shapes.standard.Link()
  l.source(a)
  l.target(b)
  l.attr({
    line: {
      stroke: '#607D8B',
      strokeWidth: 1.5,
      targetMarker: { type: 'classic', stroke: '#607D8B', fill: '#607D8B' }
    }
  })
  if (label) {
    l.appendLabel({
      attrs: { text: { text: label, fontSize: 11, fill: '#37474F' } },
      position: 0.5
    })
  }
  l.addTo(graph)
  return l
}

function layoutGrid(clusterNodes, ilNodesMap, links) {
  // Lanes
  const LEFT_X  = 100;   // IL pills
  const RIGHT_X = 760;   // Cluster cards
  const GAP_Y   = 18;    // vertical gap between ILs inside one cluster
  const BLOCK_GAP = 40;  // vertical gap between clusters
  const IL_H    = 70;
  const CL_H    = 110;

  let cursorY = 40;

  for (const c of clusterNodes) {
    // Place cluster box on the right
    c.position(RIGHT_X, cursorY);

    // ILs for this cluster
    const ilNodes = ilNodesMap.get(c.get('data').identifier) || [];
    let y = cursorY;

    ilNodes.forEach((n, idx) => {
      n.position(LEFT_X, y);
      y += IL_H + GAP_Y;
    });

    // Advance block cursor by the tallest column within the block
    const blockHeight = Math.max(CL_H, ilNodes.length * (IL_H + GAP_Y) - GAP_Y);
    cursorY += blockHeight + BLOCK_GAP;
  }

  // Fit
  if (paper && typeof paper.scaleContentToFit === 'function') {
    paper.scaleContentToFit({ padding: 30 });
  }
}

function layout() {
  const g = new dagre.graphlib.Graph()
  g.setGraph({ rankdir: 'LR', nodesep: 80, ranksep: 140 })
  g.setDefaultEdgeLabel(() => ({}))

  const nodes = graph.getElements()
  const edges = graph.getLinks()

  nodes.forEach(n => {
    const s = n.size()
    g.setNode(n.id, { width: s.width, height: s.height })
  })
  edges.forEach(e => {
    const s = e.get('source').id
    const t = e.get('target').id
    if (s && t) g.setEdge(s, t)
  })

  dagre.layout(g)

  nodes.forEach(n => {
    const d = g.node(n.id)
    if (!d) return
    const s = n.size()
    n.position(d.x - s.width / 2, d.y - s.height / 2)
  })

  if (paper && typeof paper.scaleContentToFit === 'function') {
    paper.scaleContentToFit({ padding: 30 })
  }
}

function buildFromPayload(data, ctx) {
  graph.clear();

  const clusters = Array.isArray(data?.clusters) ? data.clusters : [];
  const overlayNodes = Array.isArray(data?.overlay?.nodes) ? data.overlay.nodes : [];
  const overlayLinks = Array.isArray(data?.overlay?.links) ? data.overlay.links : [];

  // When backend provides clusters with interlinkages array
  // we’ll derive member IL ids from there.
  // We’ll build:
  //   - clusterNodes: array of JointJS elements (right lane)
  //   - ilNodesByClusterId: Map<identifier, JointJS elements[]>
  //   - also dedupe IL nodes in case same IL belongs to multiple clusters
  const clusterNodes = [];
  const ilNodesByClusterId = new Map();     // identifier -> [Element]
  const ilElementById = new Map();          // ilId -> Element (dedupe)

  // 1) Render clusters from 'clusters'
  for (const c of clusters) {
    const identifier = c.label || c.key || c.identifier || '—';
    const depType    = (c.types && c.types[0]) || c.dep_type || '—';
    const levelsMix  = Array.isArray(c.levels)
      ? c.levels.reduce((acc, lvl) => { acc[lvl] = (acc[lvl] || 0) + 1; return acc; }, {})
      : (c.levels || {});
    const members    = Array.isArray(c.interlinkages) ? c.interlinkages : [];

    // Sum notional in a single currency if consistent; else show currency of first.
    const firstCcy = members[0]?.currency_id ? (ctx.currencies[members[0].currency_id]?.code || 'EUR') : 'EUR';
    const totalAmt = members.reduce((sum, il) => sum + Number(il.notional_amount || 0), 0);

    const clusterNode = makeClusterNode(graph, {
      id: `cluster:${identifier}`,
      identifier,
      depType,
      membersCount: members.length,
      total: totalAmt,
      totalCcy: firstCcy,
      levelsMix
    });
    clusterNodes.push(clusterNode);

    // Build IL nodes for the cluster
    const arr = [];
    for (const il of members) {
      const ilId = il.id;
      let pill = ilElementById.get(ilId);
      if (!pill) {
        pill = makeILCard(graph, il, ctx);
        ilElementById.set(ilId, pill);
      }
      arr.push(pill);

      // Link (dedupe: check if link exists is overkill; let duplicates be rare)
      makeLink(pill, clusterNode, 'shared-dependency');
    }
    ilNodesByClusterId.set(identifier, arr);
  }

  // 2) If clusters array is empty, fall back to overlay nodes/links
  if (!clusters.length && overlayNodes.length) {
    const nodeById = new Map();
    for (const n of overlayNodes) {
      if (n.kind === 'cluster') {
        const clusterNode = makeClusterNode(graph, {
          id: n.id || `cluster:${n.label || n.identifier || 'n/a'}`,
          identifier: n.label || n.identifier || 'n/a',
          depType: n.dep_type || (Array.isArray(n.types) ? n.types[0] : '—'),
          membersCount: n.il_count || n.members_count || 0,
          total: n.total_amount,
          totalCcy: n.total_ccy || 'EUR',
          levelsMix: n.levels || {}
        });
        clusterNodes.push(clusterNode);
        nodeById.set(n.id || clusterNode.id, clusterNode);
      } else if (n.kind === 'interlinkage') {
        const il = ctx.interlinkages[n.id];
        if (!il) continue;
        const pill = makeILCard(graph, il, ctx)
        ilElementById.set(n.id, pill);
        nodeById.set(`il:${n.id}`, pill);
      }
    }
    for (const e of overlayLinks) {
      const a = nodeById.get(e.from) || nodeById.get(`il:${e.from}`);
      const b = nodeById.get(e.to)   || nodeById.get(`cluster:${e.to}`);
      if (a && b) makeLink(a, b, e.label || 'shared-dependency');
    }

    // Group ILs under cluster identifiers (best-effort using link targets)
    for (const e of overlayLinks) {
      if (!String(e.to).startsWith('cluster:')) continue;
      const ident = String(e.to).split(':').slice(1).join(':');
      const pill = nodeById.get(e.from) || nodeById.get(`il:${e.from}`);
      if (!pill) continue;
      const arr = ilNodesByClusterId.get(ident) || [];
      if (!arr.includes(pill)) arr.push(pill);
      ilNodesByClusterId.set(ident, arr);
    }
  }

  // 3) Lay out in two lanes
  layoutGrid(clusterNodes, ilNodesByClusterId);
}

function statusToCardStyle(status) {
  const s = String(status || '').toLowerCase()
  if (['validated','active','approved'].includes(s)) return 'good'
  if (['pending','review','in_review'].includes(s))  return 'warning'
  if (['rejected','blocked','cancelled'].includes(s)) return 'attention'
  if (s === 'draft') return 'accent'
  return 'default'
}

function interlinkageCardTemplateCompact(il, ctx) {
  const sponsor = il.sponsor_name || ctx.entities[il.sponsor_id]?.name || '—'
  const cpty    = il.counterparty_name || ctx.entities[il.counterparty_id]?.name || '—'
  const ccy     = il.currency_code || ctx.currencies[il.currency_id]?.code || 'EUR'

  const status  = il.status || 'active'

  const amount  = (() => {
    try {
      return new Intl.NumberFormat(undefined, { style: 'currency', currency: ccy, maximumFractionDigits: 2 })
        .format(Number(il.notional_amount ?? 0))
    } catch { return `${il.notional_amount ?? '—'} ${ccy}` }
  })()

  return {
    type: 'AdaptiveCard',
    $schema: 'http://adaptivecards.io/schemas/adaptive-card.json',
    version: '1.5',
    body: [
      // Header (colored by status)
      {
        type: 'Container',
        style: statusToCardStyle(status),
        bleed: true,
        items: [
          {
            type: 'TextBlock',
            text: `Interlinkage #${il.id}`,
            weight: 'Bolder',
            size: 'Medium',
            wrap: true
          },
          {
            type: 'TextBlock',
            text: `Status: ${status}`,
            size: 'Small',
            isSubtle: true,
            spacing: 'None'
          }
        ]
      },

      // Sponsor → Counterparty pair
      {
        type: 'Container',
        spacing: 'Small',
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
                    text: sponsor,
                    weight: 'Bolder',
                    size: 'Small',
                    wrap: true,
                    color: 'Accent'
                  }
                ]
              },
              {
                type: 'Column',
                width: 'auto',
                items: [
                  {
                    type: 'TextBlock',
                    text: '→',
                    size: 'Medium',
                    weight: 'Bolder',
                    horizontalAlignment: 'Center'
                  }
                ]
              },
              {
                type: 'Column',
                width: 'stretch',
                items: [
                  {
                    type: 'TextBlock',
                    text: cpty,
                    weight: 'Bolder',
                    size: 'Small',
                    wrap: true,
                    color: 'Good'
                  }
                ]
              }
            ]
          }
        ]
      },

      // Core KPIs
      {
        type: 'ColumnSet',
        spacing: 'Small',
        columns: [
          {
            type: 'Column',
            width: 'stretch',
            items: [
              { type: 'TextBlock', text: 'Notional', isSubtle: true, size: 'Small' },
              { type: 'TextBlock', text: amount, weight: 'Bolder', size: 'Small' }
            ]
          },
          {
            type: 'Column',
            width: 'auto',
            items: [
              { type: 'TextBlock', text: 'Currency', isSubtle: true, size: 'Small' },
              { type: 'TextBlock', text: ccy, weight: 'Bolder', size: 'Small' }
            ]
          }
        ]
      }
    ]
  }
}


function clusterCardTemplate(identifier, depType, membersCount, totals, levelsMix) {
  const totalAmt = totals?.amount ?? null
  const totalCcy = totals?.ccy || 'EUR'
  const totalText = (() => {
    try {
      if (totalAmt == null) return '—'
      return new Intl.NumberFormat(undefined, { style: 'currency', currency: totalCcy, maximumFractionDigits: 2 })
        .format(Number(totalAmt))
    } catch { return `${totalAmt ?? '—'} ${totalCcy}` }
  })()

  const levelBadges = (() => {
    const L = levelsMix?.low || 0, M = levelsMix?.medium || 0, H = levelsMix?.high || 0, C = levelsMix?.critical || 0
    const parts = []
    if (L) parts.push(`L:${L}`)
    if (M) parts.push(`M:${M}`)
    if (H) parts.push(`H:${H}`)
    if (C) parts.push(`C:${C}`)
    return parts.join(' ') || '—'
  })()

  return {
    type: 'AdaptiveCard',
    $schema: 'http://adaptivecards.io/schemas/adaptive-card.json',
    version: '1.5',
    body: [
      {
        type: 'Container',
        style: 'emphasis',
        bleed: true,
        items: [
          { type: 'TextBlock', text: `Cluster — ${identifier}`, weight: 'Bolder', size: 'Medium', wrap: true },
          { type: 'TextBlock', text: `Type: ${depType || '—'}`, spacing: 'None', isSubtle: true, wrap: true }
        ]
      },
      {
        type: 'ColumnSet',
        spacing: 'Small',
        columns: [
          {
            type: 'Column',
            width: 'stretch',
            items: [
              { type: 'TextBlock', text: 'Members', isSubtle: true, size: 'Small' },
              { type: 'TextBlock', text: String(membersCount || 0), weight: 'Bolder', size: 'Small' }
            ]
          },
          {
            type: 'Column',
            width: 'stretch',
            items: [
              { type: 'TextBlock', text: 'Total', isSubtle: true, size: 'Small' },
              { type: 'TextBlock', text: totalText, weight: 'Bolder', size: 'Small' }
            ]
          },
          {
            type: 'Column',
            width: 'stretch',
            items: [
              { type: 'TextBlock', text: 'Levels', isSubtle: true, size: 'Small' },
              { type: 'TextBlock', text: levelBadges, weight: 'Bolder', size: 'Small', wrap: true }
            ]
          }
        ]
      }
    ]
  }
}

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
    // emit/inspect if you like
  })
}

function setupZoomPan(paper) {
  // --- Pan (drag on blank) ---
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

  // --- Zoom to pointer with wheel ---
  const elNode = paper.el
  elNode.addEventListener('wheel', (e) => {
    e.preventDefault()
    const rect = elNode.getBoundingClientRect()
    const clientX = e.clientX - rect.left
    const clientY = e.clientY - rect.top

    // current scale & origin
    const cur = paper.scale().sx
    const factor = e.deltaY < 0 ? 1.1 : 1/1.1
    const next = clamp(cur * factor, 0.2, 3)

    // Convert the mouse point to paper local coords before scaling
    const pLocal = clientToLocal(paper, clientX, clientY)

    // Apply scale
    paper.scale(next, next)

    // After scaling, compute new origin so the point under the mouse stays put
    const newLocal = clientToLocal(paper, clientX, clientY)
    const ox = (paper.options.origin?.x || 0) + (newLocal.x - pLocal.x) * next
    const oy = (paper.options.origin?.y || 0) + (newLocal.y - pLocal.y) * next
    paper.setOrigin(ox, oy)
  }, { passive: false })
}

function clamp(v, a, b) { return Math.max(a, Math.min(b, v)) }

// Convert client (px) to paper local coords, considering origin & scale.
function clientToLocal(paper, cx, cy) {
  const scale = paper.scale().sx || 1
  const origin = paper.options.origin || { x: 0, y: 0 }
  return { x: cx/scale - origin.x/scale, y: cy/scale - origin.y/scale }
}

watch(() => props.open, async (v) => {
  if (!v) return
  await nextTick()
  init()
  buildFromPayload(props.payload, props.context || {})
})

onMounted(() => {
  if (props.open) {
    init()
    buildFromPayload(props.payload, props.context || {})
  }
})
</script>

<template>
  <v-dialog :model-value="open" @update:model-value="val => emit('update:open', val)" max-width="1200px" persistent>
    <v-card>
      <v-card-title class="d-flex align-center">
        <div class="text-h6">{{ title }}</div>
        <v-spacer />
        <v-chip class="mr-2" size="small" color="blue-lighten-4" text-color="blue-darken-3">Cluster</v-chip>
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
