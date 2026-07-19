import { api, type Task, type TaskStatus, type TaskPriority, type RepeatRule, type GamificationEvent } from './api'

export const tasksApi = {
  list: (status?: TaskStatus) =>
    api.get<Task[]>('/tasks', { params: status ? { status } : {} }).then((r) => r.data),
  create: (data: {
    title: string
    priority?: TaskPriority
    description?: string
    project_id?: string
    due_at?: string
    repeat_rule?: RepeatRule
  }) => api.post<Task>('/tasks', data).then((r) => r.data),
  update: (id: string, data: Partial<Pick<Task, 'title' | 'status' | 'priority' | 'description'>>) =>
    api.patch<Task>(`/tasks/${id}`, data).then((r) => r.data),
  complete: (id: string) =>
    api.post<{ task: Task; gamification: GamificationEvent }>(`/tasks/${id}/complete`).then((r) => r.data),
  remove: (id: string) => api.delete(`/tasks/${id}`),
}
