import { useState } from 'react'
import { Modal } from '../shared/Modal'

export function NotebookFormModal({
  initial,
  onSubmit,
  onClose,
  submitting,
}: {
  initial?: { title: string; description: string | null }
  onSubmit: (title: string, description: string) => void
  onClose: () => void
  submitting?: boolean
}) {
  const [title, setTitle] = useState(initial?.title ?? '')
  const [description, setDescription] = useState(initial?.description ?? '')

  return (
    <Modal title={initial ? 'Edit notebook' : 'New notebook'} onClose={onClose}>
      <form
        className="flex flex-col gap-3"
        onSubmit={(e) => {
          e.preventDefault()
          if (title.trim()) onSubmit(title.trim(), description.trim())
        }}
      >
        <div>
          <label className="mb-1 block text-xs text-neutral-500">Title</label>
          <input
            autoFocus
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Notebook title..."
            className="w-full rounded bg-neutral-800 px-3 py-2 text-sm outline-none placeholder:text-neutral-600"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-neutral-500">Description (optional)</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What's this notebook for?"
            rows={3}
            className="w-full resize-none rounded bg-neutral-800 px-3 py-2 text-sm outline-none placeholder:text-neutral-600"
          />
        </div>
        <div className="mt-1 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded px-3 py-1.5 text-sm text-neutral-400 hover:bg-neutral-800"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={!title.trim() || submitting}
            className="rounded bg-neutral-700 px-3 py-1.5 text-sm font-medium hover:bg-neutral-600 disabled:opacity-50"
          >
            {initial ? 'Save' : 'Create'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
