/**
 * router/index.ts
 *
 * Automatic routes for `./src/pages/*.vue`
 */

// Composables
import { createRouter, createWebHistory } from 'vue-router'
import { routes } from 'vue-router/auto-routes'
import DemoPage from '@/views/DemoPage.vue'
import Referentials from '@/views/Referentials.vue'
import LegalEntities from '@/views/LegalEntities.vue'
import Projects from '@/views/Projects.vue'
import FacilitiesInstruments from '@/views/FacilitiesInstruments.vue'
import Interlinkages from '@/views/Interlinkages.vue'
import InterlinkageDetail from '@/views/InterlinkageDetail.vue'
import Sample from '@/views/Sample.vue'


const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/sm', name: 'home', component: DemoPage },
    { path: '/', name: 'home', component: Sample },
    { path: '/refs', name: 'refs', component: Referentials },
    { path: '/entities', name: 'entities', component: LegalEntities },
    { path: '/projects', name: 'projects', component: Projects },
    { path: '/fi', name: 'fi', component: FacilitiesInstruments },
    { path: '/interlinkages', name: 'interlinkages', component: Interlinkages },
    { path: '/interlinkages/:id', name: 'interlinkage-detail', component: InterlinkageDetail },
  ],
})

// Workaround for https://github.com/vitejs/vite/issues/11804
router.onError((err, to) => {
  if (err?.message?.includes?.('Failed to fetch dynamically imported module')) {
    if (localStorage.getItem('vuetify:dynamic-reload')) {
      console.error('Dynamic import error, reloading page did not fix it', err)
    } else {
      console.log('Reloading page to fix dynamic import error')
      localStorage.setItem('vuetify:dynamic-reload', 'true')
      location.assign(to.fullPath)
    }
  } else {
    console.error(err)
  }
})

router.isReady().then(() => {
  localStorage.removeItem('vuetify:dynamic-reload')
})

export default router
