import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notebooksApi } from '../../lib/notebooks'
import type { Notebook } from '../../lib/api'
import { DropdownMenu } from '../shared/DropdownMenu'
import { NotebookFormModal } from './NotebookFormModal'

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
  const [query, setQuery] = useState('')
  const [modalMode, setModalMode] = useState<'create' | null>(null)
  const [editingNotebook, setEditingNotebook] = useState<Notebook | null>(null)

  const { data: notebooks } = useQuery({
    queryKey: ['notebooks'],
    queryFn: notebooksApi.list,
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['notebooks'] })

  const createNotebook = useMutation({
    mutationFn: (data: { title: string; description?: string }) => notebooksApi.create(data),
    onSuccess: (nb) => {
      invalidate()
      onSelect(nb.id)
      setModalMode(null)
    },
  })

  const updateNotebook = useMutation({
    mutationFn: ({ id, title, description }: { id: string; title: string; description: string }) =>
      notebooksApi.update(id, { title, description }),
    onSuccess: () => {
      invalidate()
      setEditingNotebook(null)
    },
  })

  const deleteNotebook = useMutation({
    mutationFn: (id: string) => notebooksApi.remove(id),
    onSuccess: () => {
      invalidate()
      if (selectedId) onSelect('')
    },
  })

  const filteredNotebooks = notebooks?.filter((nb) =>
    nb.title.toLowerCase().includes(query.trim().toLowerCase()),
  )

  const menuItemsFor = (nb: Notebook) => [
    { label: 'Edit', onClick: () => setEditingNotebook(nb) },
    { label: 'Export as .zip', onClick: () => window.open(notebooksApi.exportNotebookUrl(nb.id), '_blank') },
    {
      label: 'Delete',
      danger: true,
      onClick: () => {
        if (confirm(`Delete notebook "${nb.title}" and all its chapters?`)) deleteNotebook.mutate(nb.id)
      },
    },
  ]

  const modals = (
    <>
      {modalMode === 'create' && (
        <NotebookFormModal
          onSubmit={(title, description) => createNotebook.mutate({ title, description })}
          onClose={() => setModalMode(null)}
          submitting={createNotebook.isPending}
        />
      )}
      {editingNotebook && (
        <NotebookFormModal
          initial={{ title: editingNotebook.title, description: editingNotebook.description }}
          onSubmit={(title, description) =>
            updateNotebook.mutate({ id: editingNotebook.id, title, description })
          }
          onClose={() => setEditingNotebook(null)}
          submitting={updateNotebook.isPending}
        />
      )}
    </>
  )

  if (fullWidth) {
    return (
      <div className="p-6">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-medium text-neutral-300">Notebooks</h2>
          <button
            onClick={() => setModalMode('create')}
            className="rounded px-2 py-1 text-neutral-400 hover:bg-neutral-900 hover:text-neutral-200"
            title="New notebook"
          >
            + New
          </button>
        </div>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search notebooks..."
          className="mb-4 w-full max-w-sm rounded bg-neutral-900 px-3 py-2 text-base text-neutral-300 outline-none placeholder:text-neutral-600"
        />
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {filteredNotebooks?.map((nb) => (
            <div
              key={nb.id}
              className={`group relative rounded p-4 ${
                selectedId === nb.id ? 'bg-neutral-800' : 'bg-neutral-900 hover:bg-neutral-800'
              }`}
            >
              <button onClick={() => onSelect(nb.id)} className="block w-full text-left">
                <div className="mb-1 truncate text-base font-medium text-neutral-200">{nb.title}</div>
                {nb.description && (
                  <p className="line-clamp-2 text-sm text-neutral-500">{nb.description}</p>
                )}
              </button>
              <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100">
                <DropdownMenu items={menuItemsFor(nb)} />
              </div>
            </div>
          ))}
        </div>
        {filteredNotebooks?.length === 0 && notebooks && notebooks.length > 0 && (
          <p className="text-base text-neutral-600">No notebooks match "{query}".</p>
        )}
        {notebooks?.length === 0 && (
          <p className="text-base text-neutral-600">No notebooks yet — click + New to create one.</p>
        )}
        {modals}
      </div>
    )
  }

  return (
    <div className="w-56 shrink-0 border-r border-neutral-800 p-3">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-sm font-medium text-neutral-400">Notebooks</h2>
        <button
          onClick={() => setModalMode('create')}
          className="rounded px-1.5 text-neutral-500 hover:bg-neutral-900 hover:text-neutral-300"
          title="New notebook"
        >
          +
        </button>
      </div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search notebooks..."
        className="mb-3 w-full rounded bg-neutral-900 px-2 py-1 text-sm text-neutral-400 outline-none placeholder:text-neutral-600"
      />
      <div className="flex flex-col gap-1">
        {filteredNotebooks?.map((nb) => (
          <div
            key={nb.id}
            className={`group flex items-center rounded px-2 py-1.5 text-sm ${
              selectedId === nb.id ? 'bg-neutral-800' : 'hover:bg-neutral-900'
            }`}
          >
            <button
              onClick={() => onSelect(nb.id)}
              className={`flex-1 truncate text-left ${selectedId === nb.id ? 'text-white' : 'text-neutral-300'}`}
            >
              {nb.title}
            </button>
            <div className="opacity-0 group-hover:opacity-100">
              <DropdownMenu items={menuItemsFor(nb)} />
            </div>
          </div>
        ))}
        {filteredNotebooks?.length === 0 && notebooks && notebooks.length > 0 && (
          <p className="px-2 py-1.5 text-sm text-neutral-600">No notebooks match "{query}".</p>
        )}
        {notebooks?.length === 0 && (
          <p className="px-2 py-1.5 text-sm text-neutral-600">No notebooks yet — click + to create one.</p>
        )}
      </div>
      {modals}
    </div>
  )
}
