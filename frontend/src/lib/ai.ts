import { api, type AIProviderStatus, type AISettings, type AIModel, type RelatedNote, type TaskSuggestions, type Quiz, type AskMessage, type AskResponse } from './api'

export const aiApi = {
  providers: () => api.get<AIProviderStatus[]>('/ai/providers').then((r) => r.data),
  setProviderKey: (providerKey: string, apiKey: string) =>
    api.put<AIProviderStatus>(`/ai/providers/${providerKey}/key`, { api_key: apiKey }).then((r) => r.data),
  verifyProvider: (providerKey: string) =>
    api.post<AIProviderStatus>(`/ai/providers/${providerKey}/verify`).then((r) => r.data),
  getSettings: (feature: string) => api.get<AISettings>(`/ai/settings/${feature}`).then((r) => r.data),
  updateSettings: (feature: string, payload: { provider_key?: string | null; model_override?: string | null }) =>
    api.put<AISettings>(`/ai/settings/${feature}`, payload).then((r) => r.data),
  relatedNotes: (chapterId: string) =>
    api.get<RelatedNote[]>(`/ai/suggestions/related/${chapterId}`).then((r) => r.data),
  taskSuggestions: () => api.get<TaskSuggestions>('/ai/suggestions/tasks').then((r) => r.data),
  generateQuiz: (chapterId: string) =>
    api.post<Quiz>(`/ai/study/quiz/${chapterId}`).then((r) => r.data),
  ask: (messages: AskMessage[], sources: string[], model?: string | null) =>
    api.post<AskResponse>('/ai/ask', { messages, sources, model: model || undefined }).then((r) => r.data),
  availableModels: (providerKey: string) =>
    api.get<string[]>(`/ai/providers/${providerKey}/available-models`).then((r) => r.data),
  addedModels: (providerKey: string) =>
    api.get<AIModel[]>(`/ai/providers/${providerKey}/models`).then((r) => r.data),
  addModel: (providerKey: string, modelId: string) =>
    api.post<AIModel>(`/ai/providers/${providerKey}/models`, { model_id: modelId }).then((r) => r.data),
  removeModel: (providerKey: string, modelRowId: string) =>
    api.delete(`/ai/providers/${providerKey}/models/${modelRowId}`),
  setDefaultModel: (providerKey: string, modelRowId: string) =>
    api.put<AIModel>(`/ai/providers/${providerKey}/models/${modelRowId}/default`).then((r) => r.data),
}
