import { useState } from 'react'
import { Modal } from '../shared/Modal'

export function ChapterFormModal({
  initial,
  onSubmit,
  onClose,
  submitting,
}: {
  initial?: { title: string; content: string }
  onSubmit: (title: string, content: string) => void
  onClose: () => void
  submitting?: boolean
}) {
  const [title, setTitle] = useState(initial?.title ?? '')
  const [content, setContent] = useState(initial?.content ?? '')

  return (
    <Modal title={initial ? 'Edit chapter' : 'New chapter'} onClose={onClose}>
      <form
        className="flex flex-col gap-3"
        onSubmit={(e) => {
          e.preventDefault()
          if (title.trim()) onSubmit(title.trim(), content)
        }}
      >
        <div>
          <label className="mb-1 block text-xs text-neutral-500">Title</label>
          <input
            autoFocus
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Chapter title..."
            className="w-full rounded bg-neutral-800 px-3 py-2 text-sm outline-none placeholder:text-neutral-600"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-neutral-500">Description (optional)</label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Start writing, or leave blank and fill it in later..."
            rows={5}
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
