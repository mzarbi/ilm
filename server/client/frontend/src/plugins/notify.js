 import { createVNode, render } from 'vue'
 import AppNotifications from '@/components/AppNotifications.vue'
 import { useNotifications } from '@/stores/notifications'

 export const notifyPlugin = {
   install(app) {
     // mount once
     const el = document.createElement('div')
     document.body.appendChild(el)
     const vnode = createVNode(AppNotifications)
     // 👇 give the vnode the same app context that has Vuetify provides
     vnode.appContext = app._context
     render(vnode, el)

     const api = {
       success: (m, t=3500) => useNotifications().pushSnack({ color:'success', message:m, timeout:t }),
       error:   (m, t=4500) => useNotifications().pushSnack({ color:'error',   message:m, timeout:t }),
       info:    (m, t=3000) => useNotifications().pushSnack({ color:'info',    message:m, timeout:t }),
       warning: (m, t=3500) => useNotifications().pushSnack({ color:'warning', message:m, timeout:t }),
       showProgress: (o={}) => useNotifications().showProgress(o),
       updateProgress: (p) => useNotifications().updateProgress(p),
       hideProgress: () => useNotifications().hideProgress(),
     }

     app.config.globalProperties.$notify = api
     app.provide('notify', api)
   },
 }
