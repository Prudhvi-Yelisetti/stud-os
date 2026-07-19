import { api, type TrashedItem } from './api'

export const trashApi = {
  list: () => api.get<TrashedItem[]>('/trash').then((r) => r.data),
  restore: (type: string, id: string) =>
    api.post<TrashedItem>(`/trash/${type}/${id}/restore`).then((r) => r.data),
  permanentlyDelete: (type: string, id: string) => api.delete(`/trash/${type}/${id}`),
}
