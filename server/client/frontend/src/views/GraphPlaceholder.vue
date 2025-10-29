<script setup>
import { computed } from 'vue'

const props = defineProps({
  nodes: { type: Array, default: () => [] },  // [{id,kind,x,y,label,data}]
  links: { type: Array, default: () => [] },  // [{from, to, meta?}]
})

const emit = defineEmits(['select', 'fit'])

// Quick lookup for link endpoints
const nodeById = computed(() => {
  const m = new Map()
  for (const n of props.nodes) m.set(n.id, n)
  return m
})

function pickNode(n) {
  emit('select', { kind: n.kind, data: n.data })
}
</script>

<template>
  <div class="placeholder-root">
    <svg class="placeholder-canvas" :width="'100%'" :height="Math.max(600, (nodes.length*90)+120)">
      <!-- Links -->
      <g v-for="(l, idx) in links" :key="'L'+idx">
        <line
          v-if="nodeById.get(l.from) && nodeById.get(l.to)"
          :x1="nodeById.get(l.from).x" :y1="nodeById.get(l.from).y"
          :x2="nodeById.get(l.to).x"   :y2="nodeById.get(l.to).y"
          stroke-width="2" stroke="currentColor" opacity="0.35"
        />
      </g>

      <!-- Nodes -->
      <g v-for="n in nodes" :key="n.id" @click="pickNode(n)" style="cursor:pointer">
        <rect
          :x="n.x - 90" :y="n.y - 22" rx="10" ry="10" width="180" height="44"
          fill="white" stroke="currentColor" stroke-width="1.5"
        />
        <text :x="n.x" :y="n.y+4" text-anchor="middle" style="font-size:13px;">
          {{ n.label }}
        </text>
      </g>
    </svg>
  </div>
</template>
<style>
  .placeholder-root { position: relative; overflow: auto; }
.placeholder-canvas { display: block; }
</style>
