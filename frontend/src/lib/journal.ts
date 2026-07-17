import { api, type JournalEntry, type Mood } from './api'

export const journalApi = {
  list: () => api.get<JournalEntry[]>('/journal').then((r) => r.data),
  create: (data: { title: string; content?: string; mood?: Mood; entry_date: string }) =>
    api.post<JournalEntry>('/journal', data).then((r) => r.data),
  update: (id: string, data: Partial<Pick<JournalEntry, 'title' | 'content' | 'mood'>>) =>
    api.patch<JournalEntry>(`/journal/${id}`, data).then((r) => r.data),
  remove: (id: string) => api.delete(`/journal/${id}`),
}
