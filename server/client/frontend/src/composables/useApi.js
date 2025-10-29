import { inject } from 'vue'
import { createHttp } from '@/lib/http'

export function useApi() {
  const notify = inject('notify')
  const http = createHttp()

  function resource(name) {
    const base = `/${name}`
    return {
      list: (params) =>
        http.get(base + (params ? '?' + new URLSearchParams(params).toString() : '')),
      get: (id) => http.get(`${base}/${id}`),
      create: (payload, msg='Created') =>
        http.post(base, payload).then(r => (notify?.success(msg), r)),
      update: (id, payload, msg='Updated') =>
        http.post(`${base}/${id}/update`, payload).then(r => (notify?.success(msg), r)),
      remove: (id, soft=true, msg='Deleted') =>
        http.post(`${base}/${id}/delete${soft ? '' : '?soft=0'}`).then(r => (notify?.success(msg), r)),
      // ⭐ new: idempotent helper
      async getOrCreate(payload, uniqueKeys, msg='Created') {
        const filters = {}
        uniqueKeys.forEach(k => { filters[k] = payload[k] })
        const found = await this.list(filters)
        if (found?.items?.length) return found.items[0]
        try {
          return await this.create(payload, msg)
        } catch (e) {
          if (e?.status === 409) {
            const again = await this.list(filters)
            if (again?.items?.length) return again.items[0]
          }
          throw e
        }
      },
    }
  }

  return { http, resource, notify }
}
