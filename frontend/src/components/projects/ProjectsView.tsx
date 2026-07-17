import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projectsApi } from '../../lib/projects'

export function ProjectsView() {
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [newTitle, setNewTitle] = useState('')

  const { data: projects } = useQuery({ queryKey: ['projects'], queryFn: projectsApi.list })
  const { data: projectTasks } = useQuery({
    queryKey: ['project-tasks', selectedId],
    queryFn: () => projectsApi.listTasks(selectedId!),
    enabled: !!selectedId,
  })

  const createProject = useMutation({
    mutationFn: (title: string) => projectsApi.create({ title }),
    onSuccess: (p) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setSelectedId(p.id)
    },
  })

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
            <button
              key={p.id}
              onClick={() => setSelectedId(p.id)}
              className={`rounded px-2 py-1.5 text-left text-sm ${
                selectedId === p.id ? 'bg-neutral-800' : 'hover:bg-neutral-900 text-neutral-300'
              }`}
            >
              {p.title}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-6">
        {!selectedId && <p className="text-sm text-neutral-600">Select a project</p>}
        {selectedId && (
          <>
            <h1 className="mb-4 text-xl font-semibold">
              {projects?.find((p) => p.id === selectedId)?.title}
            </h1>
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
