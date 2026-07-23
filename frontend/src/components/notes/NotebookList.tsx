import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notebooksApi } from '../../lib/notebooks'
import type { Notebook } from '../../lib/api'

export function NotebookList({
  selectedId,
  onSelect,
  fullWidth,
}: {
  selectedId: string | null
  onSelect: (id: string) => void
  fullWidth?: boolean
}) {
  const queryClient = useQueryClient()
  const [newTitle, setNewTitle] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')

  const { data: notebooks } = useQuery({
    queryKey: ['notebooks'],
    queryFn: notebooksApi.list,
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['notebooks'] })

  const createNotebook = useMutation({
    mutationFn: (title: string) => notebooksApi.create({ title }),
    onSuccess: (nb) => {
      invalidate()
      onSelect(nb.id)
    },
  })

  const renameNotebook = useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) => notebooksApi.update(id, { title }),
    onSuccess: invalidate,
  })

  const deleteNotebook = useMutation({
    mutationFn: (id: string) => notebooksApi.remove(id),
    onSuccess: () => {
      invalidate()
      if (selectedId) onSelect('')
    },
  })

  function startEdit(nb: Notebook) {
    setEditingId(nb.id)
    setEditTitle(nb.title)
  }

  function commitEdit() {
    if (editingId && editTitle.trim()) {
      renameNotebook.mutate({ id: editingId, title: editTitle.trim() })
    }
    setEditingId(null)
  }

  return (
    <div className={fullWidth ? 'w-full p-3' : 'w-56 shrink-0 border-r border-neutral-800 p-3'}>
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-sm font-medium text-neutral-400">Notebooks</h2>
      </div>
      <form
        className="mb-3 flex gap-1"
        onSubmit={(e) => {
          e.preventDefault()
          if (newTitle.trim()) {
            createNotebook.mutate(newTitle.trim())
            setNewTitle('')
          }
        }}
      >
        <input
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          placeholder="New notebook..."
          className="w-full rounded bg-neutral-900 px-2 py-1 text-sm outline-none placeholder:text-neutral-600"
        />
      </form>
      <div className="flex flex-col gap-1">
        {notebooks?.map((nb) => (
          <div
            key={nb.id}
            className={`group flex items-center rounded px-2 py-1.5 text-sm ${
              selectedId === nb.id ? 'bg-neutral-800' : 'hover:bg-neutral-900'
            }`}
          >
            {editingId === nb.id ? (
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
                onClick={() => onSelect(nb.id)}
                onDoubleClick={() => startEdit(nb)}
                className={`flex-1 truncate text-left ${
                  selectedId === nb.id ? 'text-white' : 'text-neutral-300'
                }`}
              >
                {nb.title}
              </button>
            )}
            {editingId !== nb.id && (
              <button
                onClick={() => {
                  if (confirm(`Delete notebook "${nb.title}" and all its chapters?`)) {
                    deleteNotebook.mutate(nb.id)
                  }
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
  )
}
