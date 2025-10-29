import { useApi } from '@/composables/useApi'

export function useResources() {
  const api = useApi()
  return {
    currencies: api.resource('currencies'),
    countries: api.resource('countries'),
    sectors: api.resource('sectors'),
    praActivities: api.resource('pra-activities'),
    counterpartyTypes: api.resource('counterparty-types'),
    legalEntities: api.resource('legal-entities'),
    projects: api.resource('projects'),
    facilities: api.resource('facilities'),
    instruments: api.resource('instruments'),
    interlinkages: api.resource('interlinkages'),
    interdependences: api.resource('interdependences'),
    exposures: api.resource('exposures'),
  }
}
