import 'unfonts.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'
import { notifyPlugin } from './plugins/notify'
import { detectApiBase, API_BASE } from '@/config/runtime'
import 'jointjs/dist/joint.css'

;(async () => {
  await detectApiBase()
  console.log('API base:', API_BASE)

  const app = createApp(App)
  app.use(createPinia())
  app.use(router)
  app.use(vuetify)
  app.use(notifyPlugin)
  app.mount('#app')
})()
