import { api, type Notebook, type Chapter, type Backlink, type ChapterTitleMatch, type ChapterVersion } from './api'

export const notebooksApi = {
  list: () => api.get<Notebook[]>('/notebooks').then((r) => r.data),
  create: (data: { title: string; description?: string }) =>
    api.post<Notebook>('/notebooks', data).then((r) => r.data),
  get: (id: string) => api.get<Notebook>(`/notebooks/${id}`).then((r) => r.data),
  update: (id: string, data: Partial<Pick<Notebook, 'title' | 'description'>>) =>
    api.patch<Notebook>(`/notebooks/${id}`, data).then((r) => r.data),
  remove: (id: string) => api.delete(`/notebooks/${id}`),

  listChapters: (notebookId: string) =>
    api.get<Chapter[]>(`/notebooks/${notebookId}/chapters`).then((r) => r.data),
  createChapter: (notebookId: string, data: { title: string; content?: string }) =>
    api.post<Chapter>(`/notebooks/${notebookId}/chapters`, data).then((r) => r.data),
  getChapter: (chapterId: string) =>
    api.get<Chapter>(`/notebooks/chapters/${chapterId}`).then((r) => r.data),
  updateChapter: (
    chapterId: string,
    data: Partial<Pick<Chapter, 'title' | 'content' | 'pinned' | 'is_template' | 'is_daily_template'>>,
  ) => api.patch<Chapter>(`/notebooks/chapters/${chapterId}`, data).then((r) => r.data),
  updateChapterProperties: (chapterId: string, properties: Record<string, unknown>) =>
    api.patch<Chapter>(`/notebooks/chapters/${chapterId}/properties`, { properties }).then((r) => r.data),
  deleteChapter: (chapterId: string) => api.delete(`/notebooks/chapters/${chapterId}`),
  getBacklinks: (chapterId: string) =>
    api.get<Backlink[]>(`/notebooks/chapters/${chapterId}/backlinks`).then((r) => r.data),
  listRecentChapters: (limit = 5) =>
    api.get<Chapter[]>('/notebooks/chapters/recent', { params: { limit } }).then((r) => r.data),
  searchChapterTitles: (q: string) =>
    api.get<ChapterTitleMatch[]>('/notebooks/chapters/search', { params: { q } }).then((r) => r.data),
  listTemplates: () => api.get<Chapter[]>('/notebooks/chapters/templates').then((r) => r.data),
  createChapterFromTemplate: (notebookId: string, templateId: string) =>
    api.post<Chapter>(`/notebooks/${notebookId}/chapters/from-template/${templateId}`).then((r) => r.data),
  listVersions: (chapterId: string) =>
    api.get<ChapterVersion[]>(`/notebooks/chapters/${chapterId}/versions`).then((r) => r.data),
  restoreVersion: (chapterId: string, versionId: string) =>
    api.post<Chapter>(`/notebooks/chapters/${chapterId}/versions/${versionId}/restore`).then((r) => r.data),
  exportNotebookUrl: (notebookId: string) => `/api/notebooks/${notebookId}/export`,
  exportChapterUrl: (chapterId: string) => `/api/notebooks/chapters/${chapterId}/export`,
}
