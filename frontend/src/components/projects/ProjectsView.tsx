import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projectsApi } from '../../lib/projects'
import type { Project } from '../../lib/api'

export function ProjectsView() {
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [newTitle, setNewTitle] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')

  const { data: projects } = useQuery({ queryKey: ['projects'], queryFn: projectsApi.list })
  const { data: projectTasks } = useQuery({
    queryKey: ['project-tasks', selectedId],
    queryFn: () => projectsApi.listTasks(selectedId!),
    enabled: !!selectedId,
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['projects'] })

  const createProject = useMutation({
    mutationFn: (title: string) => projectsApi.create({ title }),
    onSuccess: (p) => {
      invalidate()
      setSelectedId(p.id)
    },
  })

  const renameProject = useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) => projectsApi.update(id, { title }),
    onSuccess: invalidate,
  })

  const updateDescription = useMutation({
    mutationFn: ({ id, description }: { id: string; description: string }) =>
      projectsApi.update(id, { description }),
    onSuccess: invalidate,
  })

  const deleteProject = useMutation({
    mutationFn: (id: string) => projectsApi.remove(id),
    onSuccess: () => {
      invalidate()
      setSelectedId(null)
    },
  })

  function startEdit(p: Project) {
    setEditingId(p.id)
    setEditTitle(p.title)
  }

  function commitEdit() {
    if (editingId && editTitle.trim()) renameProject.mutate({ id: editingId, title: editTitle.trim() })
    setEditingId(null)
  }

  const selectedProject = projects?.find((p) => p.id === selectedId)
  const [descDraft, setDescDraft] = useState('')

  useEffect(() => {
    setDescDraft(selectedProject?.description ?? '')
  }, [selectedProject?.id])

  return (
    <div className="flex h-full">
      <div className="w-64 shrink-0 border-r border-neutral-800 p-3">
        <h2 className="mb-2 text-sm font-medium text-neutral-400">Projects</h2>
        <form
          className="mb-3 flex gap-1"
          onSubmit={(e) => {
            e.preventDefault()
            if (newTitle.trim()) {
              createProject.mutate(newTitle.trim())
              setNewTitle('')
            }
          }}
        >
          <input
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="New project..."
            className="w-full rounded bg-neutral-900 px-2 py-1 text-sm outline-none placeholder:text-neutral-600"
          />
        </form>
        <div className="flex flex-col gap-1">
          {projects?.map((p) => (
            <div
              key={p.id}
              className={`group flex items-center rounded px-2 py-1.5 text-sm ${
                selectedId === p.id ? 'bg-neutral-800' : 'hover:bg-neutral-900'
              }`}
            >
              {editingId === p.id ? (
                <input
                  autoFocus
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  onBlur={commitEdit}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') commitEdit()
                    if (e.key === 'Escape') setEditingId(null)
                  }}
                  className="w-full bg-transparent outline-none"
                />
              ) : (
                <button
                  onClick={() => setSelectedId(p.id)}
                  onDoubleClick={() => startEdit(p)}
                  className={`flex-1 truncate text-left ${selectedId === p.id ? 'text-white' : 'text-neutral-300'}`}
                >
                  {p.title}
                </button>
              )}
              {editingId !== p.id && (
                <button
                  onClick={() => {
                    if (confirm(`Delete project "${p.title}"?`)) deleteProject.mutate(p.id)
                  }}
                  className="ml-1 hidden text-neutral-600 hover:text-red-400 group-hover:inline"
                  title="Delete"
                >
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-6">
        {!selectedId && <p className="text-sm text-neutral-600">Select a project</p>}
        {selectedId && (
          <>
            <h1 className="mb-2 text-xl font-semibold">{selectedProject?.title}</h1>
            <textarea
              value={descDraft}
              onChange={(e) => setDescDraft(e.target.value)}
              onBlur={() => {
                if (selectedId && descDraft !== (selectedProject?.description ?? '')) {
                  updateDescription.mutate({ id: selectedId, description: descDraft })
                }
              }}
              placeholder="Add a description..."
              rows={2}
              className="mb-4 w-full resize-none rounded bg-neutral-900 p-2 text-sm text-neutral-300 outline-none placeholder:text-neutral-600"
            />
            <h2 className="mb-2 text-sm font-medium text-neutral-400">Tasks</h2>
            <div className="flex flex-col gap-2">
              {projectTasks?.map((t) => (
                <div key={t.id} className="rounded bg-neutral-900 px-3 py-2 text-sm">
                  <span className="mr-2 text-xs uppercase text-neutral-500">{t.status}</span>
                  {t.title}
                </div>
              ))}
              {projectTasks?.length === 0 && (
                <p className="text-sm text-neutral-600">
                  No tasks linked to this project yet.
                </p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
