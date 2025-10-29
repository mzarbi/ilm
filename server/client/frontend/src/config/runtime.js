// Map Flask's X-App-Env header -> actual API base
export const API_BASE_MAP = {
  dev:  'http://127.0.0.1:5000/api',
  sit:  'https://sit.api.company.com/api',
  uat:  'https://uat.api.company.com/api',
  prod: '/api', // same-origin in prod
}

export let API_BASE = '/api' // fallback

export async function detectApiBase() {
  try {
    const res = await fetch('/health', { method: 'GET', cache: 'no-store' })
    const key = (res.headers.get('x-app-env') || 'prod').toLowerCase()
    API_BASE = API_BASE_MAP[key] || API_BASE_MAP.prod
  } catch (e) {
    API_BASE = API_BASE_MAP.prod
  }
  return API_BASE
}
