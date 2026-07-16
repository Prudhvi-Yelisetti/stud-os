import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notebooksApi } from '../../lib/notebooks'

export function ChapterList({
  notebookId,
  selectedId,
  onSelect,
}: {
  notebookId: string
  selectedId: string | null
  onSelect: (id: string) => void
}) {
  const queryClient = useQueryClient()
  const [newTitle, setNewTitle] = useState('')

  const { data: chapters } = useQuery({
    queryKey: ['chapters', notebookId],
    queryFn: () => notebooksApi.listChapters(notebookId),
  })

  const createChapter = useMutation({
    mutationFn: (title: string) => notebooksApi.createChapter(notebookId, { title }),
    onSuccess: (ch) => {
      queryClient.invalidateQueries({ queryKey: ['chapters', notebookId] })
      onSelect(ch.id)
    },
  })

  return (
    <div className="w-64 shrink-0 border-r border-neutral-800 p-3">
      <h2 className="mb-2 text-sm font-medium text-neutral-400">Chapters</h2>
      <form
        className="mb-3 flex gap-1"
        onSubmit={(e) => {
          e.preventDefault()
          if (newTitle.trim()) {
            createChapter.mutate(newTitle.trim())
            setNewTitle('')
          }
        }}
      >
        <input
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          placeholder="New chapter..."
          className="w-full rounded bg-neutral-900 px-2 py-1 text-sm outline-none placeholder:text-neutral-600"
        />
      </form>
      <div className="flex flex-col gap-1">
        {chapters?.map((ch) => (
          <button
            key={ch.id}
            onClick={() => onSelect(ch.id)}
            className={`truncate rounded px-2 py-1.5 text-left text-sm ${
              selectedId === ch.id ? 'bg-neutral-800' : 'hover:bg-neutral-900 text-neutral-300'
            }`}
          >
            {ch.pinned ? '📌 ' : ''}
            {ch.title}
          </button>
        ))}
      </div>
    </div>
  )
}
