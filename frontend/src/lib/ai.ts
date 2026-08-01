import { api, type AIProviderStatus, type AISettings, type RelatedNote, type TaskSuggestions } from './api'

export const aiApi = {
  providers: () => api.get<AIProviderStatus[]>('/ai/providers').then((r) => r.data),
  getSettings: (feature: string) => api.get<AISettings>(`/ai/settings/${feature}`).then((r) => r.data),
  updateSettings: (feature: string, payload: { provider_key: string | null }) =>
    api.put<AISettings>(`/ai/settings/${feature}`, payload).then((r) => r.data),
  relatedNotes: (chapterId: string) =>
    api.get<RelatedNote[]>(`/ai/suggestions/related/${chapterId}`).then((r) => r.data),
  taskSuggestions: () => api.get<TaskSuggestions>('/ai/suggestions/tasks').then((r) => r.data),
}
