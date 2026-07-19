import { api, type Project, type Task, type Subtask } from './api'

export const projectsApi = {
  list: () => api.get<Project[]>('/projects').then((r) => r.data),
  create: (data: { title: string; description?: string }) =>
    api.post<Project>('/projects', data).then((r) => r.data),
  update: (id: string, data: Partial<Pick<Project, 'title' | 'description'>>) =>
    api.patch<Project>(`/projects/${id}`, data).then((r) => r.data),
  remove: (id: string) => api.delete(`/projects/${id}`),
  listTasks: (projectId: string) =>
    api.get<Task[]>(`/projects/${projectId}/tasks`).then((r) => r.data),
}

export const subtasksApi = {
  list: (taskId: string) => api.get<Subtask[]>(`/tasks/${taskId}/subtasks`).then((r) => r.data),
  create: (taskId: string, title: string) =>
    api.post<Subtask>(`/tasks/${taskId}/subtasks`, { title }).then((r) => r.data),
  toggle: (subtaskId: string, done: boolean) =>
    api.patch<Subtask>(`/tasks/subtasks/${subtaskId}`, { done }).then((r) => r.data),
  remove: (subtaskId: string) => api.delete(`/tasks/subtasks/${subtaskId}`),
}
