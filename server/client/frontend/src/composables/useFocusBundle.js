// src/composables/useFocusBundle.js
import { useApi } from '@/composables/useApi'

export function useFocusBundle() {
  const api = useApi()
  // This will hit GET /api/focus-bundle with query params via .list()
  const focus = api.resource('focus-bundle')

  function fetchFocusBundle(params) {
    return focus.list(params) // maps to GET /api/focus-bundle?...
  }

  return { fetchFocusBundle }
}
