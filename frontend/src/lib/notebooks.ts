import { api, type Notebook, type Chapter, type Backlink } from './api'

export const notebooksApi = {
  list: () => api.get<Notebook[]>('/notebooks').then((r) => r.data),
  create: (data: { title: string; description?: string }) =>
    api.post<Notebook>('/notebooks', data).then((r) => r.data),
  get: (id: string) => api.get<Notebook>(`/notebooks/${id}`).then((r) => r.data),

  listChapters: (notebookId: string) =>
    api.get<Chapter[]>(`/notebooks/${notebookId}/chapters`).then((r) => r.data),
  createChapter: (notebookId: string, data: { title: string; content?: string }) =>
    api.post<Chapter>(`/notebooks/${notebookId}/chapters`, data).then((r) => r.data),
  getChapter: (chapterId: string) =>
    api.get<Chapter>(`/notebooks/chapters/${chapterId}`).then((r) => r.data),
  updateChapter: (chapterId: string, data: Partial<Pick<Chapter, 'title' | 'content' | 'pinned'>>) =>
    api.patch<Chapter>(`/notebooks/chapters/${chapterId}`, data).then((r) => r.data),
  getBacklinks: (chapterId: string) =>
    api.get<Backlink[]>(`/notebooks/chapters/${chapterId}/backlinks`).then((r) => r.data),
  listRecentChapters: (limit = 5) =>
    api.get<Chapter[]>('/notebooks/chapters/recent', { params: { limit } }).then((r) => r.data),
}
