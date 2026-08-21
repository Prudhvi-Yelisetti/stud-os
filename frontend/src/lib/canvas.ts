import { api, type Canvas } from './api'

export const canvasApi = {
  list: () => api.get<Canvas[]>('/canvases').then((r) => r.data),
  create: (title: string) => api.post<Canvas>('/canvases', { title }).then((r) => r.data),
  get: (id: string) => api.get<Canvas>(`/canvases/${id}`).then((r) => r.data),
  update: (id: string, data: Partial<Pick<Canvas, 'title' | 'data'>>) =>
    api.patch<Canvas>(`/canvases/${id}`, data).then((r) => r.data),
  remove: (id: string) => api.delete(`/canvases/${id}`),
}
