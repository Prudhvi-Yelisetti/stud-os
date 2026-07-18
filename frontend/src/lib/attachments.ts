import { api, type Attachment } from './api'

export const attachmentsApi = {
  list: (ownerType: string, ownerId: string) =>
    api
      .get<Attachment[]>('/attachments', { params: { owner_type: ownerType, owner_id: ownerId } })
      .then((r) => r.data),
  upload: (ownerType: string, ownerId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api
      .post<Attachment>('/attachments', formData, {
        params: { owner_type: ownerType, owner_id: ownerId },
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data)
  },
  downloadUrl: (id: string) => `/api/attachments/${id}/download`,
  remove: (id: string) => api.delete(`/attachments/${id}`),
}
