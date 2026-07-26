import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notebooksApi } from '../../lib/notebooks'
import type { Chapter } from '../../lib/api'
import { DropdownMenu } from '../shared/DropdownMenu'
import { ChapterFormModal } from './ChapterFormModal'

export function ChapterList({
  notebookId,
  selectedId,
  onSelect,
  fullWidth,
}: {
  notebookId: string
  selectedId: string | null
  onSelect: (id: string) => void
  fullWidth?: boolean
}) {
  const queryClient = useQueryClient()
  const [query, setQuery] = useState('')
  const [modalMode, setModalMode] = useState<'create' | null>(null)
  const [editingChapter, setEditingChapter] = useState<Chapter | null>(null)

  const { data: chapters } = useQuery({
    queryKey: ['chapters', notebookId],
    queryFn: () => notebooksApi.listChapters(notebookId),
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['chapters', notebookId] })

  const createChapter = useMutation({
    mutationFn: (data: { title: string; content?: string }) => notebooksApi.createChapter(notebookId, data),
    onSuccess: (ch) => {
      invalidate()
      onSelect(ch.id)
      setModalMode(null)
    },
  })

  const updateChapter = useMutation({
    mutationFn: ({ id, title, content }: { id: string; title: string; content: string }) =>
      notebooksApi.updateChapter(id, { title, content }),
    onSuccess: () => {
      invalidate()
      setEditingChapter(null)
    },
  })

  const deleteChapter = useMutation({
    mutationFn: (id: string) => notebooksApi.deleteChapter(id),
    onSuccess: (_data, id) => {
      invalidate()
      if (id === selectedId) onSelect('')
    },
  })

  const filteredChapters = chapters?.filter((ch) =>
    ch.title.toLowerCase().includes(query.trim().toLowerCase()),
  )

  return (
    <div className={fullWidth ? 'w-full p-3' : 'w-64 shrink-0 border-r border-neutral-800 p-3'}>
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-sm font-medium text-neutral-400">Chapters</h2>
        <button
          onClick={() => setModalMode('create')}
          className="rounded px-1.5 text-neutral-500 hover:bg-neutral-900 hover:text-neutral-300"
          title="New chapter"
        >
          +
        </button>
      </div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search chapters..."
        className="mb-3 w-full rounded bg-neutral-900 px-2 py-1 text-sm text-neutral-400 outline-none placeholder:text-neutral-600"
      />
      <div className="flex flex-col gap-1">
        {filteredChapters?.map((ch) => (
          <div
            key={ch.id}
            className={`group flex items-center rounded px-2 py-1.5 text-sm ${
              selectedId === ch.id ? 'bg-neutral-800' : 'hover:bg-neutral-900'
            }`}
          >
            <button
              onClick={() => onSelect(ch.id)}
              className={`flex-1 truncate text-left ${selectedId === ch.id ? 'text-white' : 'text-neutral-300'}`}
            >
              {ch.pinned ? '📌 ' : ''}
              {ch.title}
            </button>
            <div className="opacity-0 group-hover:opacity-100">
              <DropdownMenu
                items={[
                  { label: 'Edit', onClick: () => setEditingChapter(ch) },
                  {
                    label: 'Export',
                    onClick: () => window.open(notebooksApi.exportChapterUrl(ch.id), '_blank'),
                  },
                  {
                    label: 'Delete',
                    danger: true,
                    onClick: () => {
                      if (confirm(`Delete chapter "${ch.title}"?`)) deleteChapter.mutate(ch.id)
                    },
                  },
                ]}
              />
            </div>
          </div>
        ))}
        {filteredChapters?.length === 0 && chapters && chapters.length > 0 && (
          <p className="px-2 py-1.5 text-sm text-neutral-600">No chapters match "{query}".</p>
        )}
        {chapters?.length === 0 && (
          <p className="px-2 py-1.5 text-sm text-neutral-600">No chapters yet — click + to create one.</p>
        )}
      </div>

      {modalMode === 'create' && (
        <ChapterFormModal
          onSubmit={(title, content) => createChapter.mutate({ title, content: content || undefined })}
          onClose={() => setModalMode(null)}
          submitting={createChapter.isPending}
        />
      )}
      {editingChapter && (
        <ChapterFormModal
          initial={{ title: editingChapter.title, content: editingChapter.content }}
          onSubmit={(title, content) => updateChapter.mutate({ id: editingChapter.id, title, content })}
          onClose={() => setEditingChapter(null)}
          submitting={updateChapter.isPending}
        />
      )}
    </div>
  )
}
