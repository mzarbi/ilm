import { API_BASE } from '@/config/runtime'

function join(base, url) {
  if (/^https?:\/\//i.test(url)) return url
  return `${base}${url.startsWith('/') ? '' : '/'}${url}`
}

export function createHttp() {
  async function request(method, url, body) {
    const full = join(API_BASE, url)
    const res = await fetch(full, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: body != null ? JSON.stringify(body) : undefined,
    })
    const isJSON = res.headers.get('content-type')?.includes('application/json')
    const data = isJSON ? await res.json() : await res.text()
    if (!res.ok) {
      const err = new Error((data && data.message) || res.statusText)
      err.status = res.status
      err.data = data
      // Optional: customize uniqueness message
      if (err.status === 409) err.message = 'Already exists (unique constraint).'
      throw err
    }
    return data
  }

  return {
    get:  (url) => request('GET', url),
    post: (url, body) => request('POST', url, body),
    put:  (url, body) => request('PUT', url, body),
    del:  (url) => request('DELETE', url),
  }
}
