import { api, type TagCount, type TaggedItem } from './api'

export const tagsApi = {
  list: () => api.get<TagCount[]>('/tags').then((r) => r.data),
  getTagged: (tagName: string) => api.get<TaggedItem[]>(`/tags/${encodeURIComponent(tagName)}`).then((r) => r.data),
}
