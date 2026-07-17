import { api, type SearchResult, type GraphData } from './api'

export const searchApi = {
  query: (q: string) => api.get<SearchResult[]>('/search', { params: { q } }).then((r) => r.data),
}

export const graphApi = {
  get: () => api.get<GraphData>('/graph').then((r) => r.data),
}
