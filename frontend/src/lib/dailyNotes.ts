import { api, type Chapter } from './api'

export const dailyNotesApi = {
  today: () => api.post<Chapter>('/daily-notes/today').then((r) => r.data),
}
