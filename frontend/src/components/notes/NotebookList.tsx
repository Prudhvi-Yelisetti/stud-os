import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notebooksApi } from '../../lib/notebooks'

export function NotebookList({
  selectedId,
  onSelect,
}: {
  selectedId: string | null
  onSelect: (id: string) => void
}) {
  const queryClient = useQueryClient()
  const [newTitle, setNewTitle] = useState('')

  const { data: notebooks } = useQuery({
    queryKey: ['notebooks'],
    queryFn: notebooksApi.list,
  })

  const createNotebook = useMutation({
    mutationFn: (title: string) => notebooksApi.create({ title }),
    onSuccess: (nb) => {
      queryClient.invalidateQueries({ queryKey: ['notebooks'] })
      onSelect(nb.id)
    },
  })

  return (
    <div className="w-56 shrink-0 border-r border-neutral-800 p-3">
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
          <button
            key={nb.id}
            onClick={() => onSelect(nb.id)}
            className={`rounded px-2 py-1.5 text-left text-sm ${
              selectedId === nb.id ? 'bg-neutral-800' : 'hover:bg-neutral-900 text-neutral-300'
            }`}
          >
            {nb.title}
          </button>
        ))}
      </div>
    </div>
  )
}
