import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { canvasApi } from '../../lib/canvas'

export function CanvasesView() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [newTitle, setNewTitle] = useState('')

  const { data: canvases } = useQuery({ queryKey: ['canvases'], queryFn: canvasApi.list })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['canvases'] })

  const createCanvas = useMutation({
    mutationFn: (title: string) => canvasApi.create(title),
    onSuccess: (canvas) => {
      invalidate()
      navigate(`/canvas/${canvas.id}`)
    },
  })

  const deleteCanvas = useMutation({
    mutationFn: (id: string) => canvasApi.remove(id),
    onSuccess: invalidate,
  })

  function handleCreate() {
    const title = newTitle.trim() || 'Untitled canvas'
    createCanvas.mutate(title)
    setNewTitle('')
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      <h1 className="mb-4 text-xl font-semibold">Canvas</h1>
      <div className="mb-6 flex gap-2">
        <input
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
          placeholder="New canvas title..."
          className="flex-1 rounded bg-neutral-900 px-3 py-2 text-sm text-neutral-200 outline-none placeholder:text-neutral-600"
        />
        <button
          onClick={handleCreate}
          disabled={createCanvas.isPending}
          className="rounded bg-neutral-700 px-4 py-2 text-sm font-medium hover:bg-neutral-600 disabled:opacity-50"
        >
          + New
        </button>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
        {canvases?.map((c) => (
          <div
            key={c.id}
            className="group relative rounded border border-neutral-800 bg-neutral-900 p-4 hover:border-neutral-700"
          >
            <button onClick={() => navigate(`/canvas/${c.id}`)} className="block w-full text-left">
              <div className="mb-2 text-2xl">🖼️</div>
              <p className="truncate text-sm text-neutral-200">{c.title}</p>
              <p className="text-xs text-neutral-600">{new Date(c.updated_at).toLocaleDateString()}</p>
            </button>
            <button
              onClick={() => {
                if (confirm(`Delete canvas "${c.title}"?`)) deleteCanvas.mutate(c.id)
              }}
              className="absolute right-2 top-2 hidden text-neutral-600 hover:text-red-400 group-hover:block"
              title="Delete"
            >
              ✕
            </button>
          </div>
        ))}
      </div>
      {canvases?.length === 0 && (
        <p className="text-sm text-neutral-600">No canvases yet — create one to start a visual board.</p>
      )}
    </div>
  )
}
