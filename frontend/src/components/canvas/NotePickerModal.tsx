import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { notebooksApi } from '../../lib/notebooks'
import { Modal } from '../shared/Modal'
import { useDebouncedValue } from '../../lib/useDebouncedValue'

/** Small search-as-you-type picker for adding a note-reference card to a
 * canvas -- reuses the same title-search endpoint the [[ ]] autocomplete
 * already uses elsewhere, rather than listing every chapter at once. */
export function NotePickerModal({
  onPick,
  onClose,
}: {
  onPick: (chapter: { id: string; title: string }) => void
  onClose: () => void
}) {
  const [query, setQuery] = useState('')
  const debouncedQuery = useDebouncedValue(query, 200)
  const { data: matches } = useQuery({
    queryKey: ['chapter-search', debouncedQuery],
    queryFn: () => notebooksApi.searchChapterTitles(debouncedQuery),
    enabled: debouncedQuery.trim().length > 0,
  })

  return (
    <Modal title="Add a note to canvas" onClose={onClose}>
      <input
        autoFocus
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search notes by title..."
        className="mb-2 w-full rounded bg-neutral-900 px-3 py-2 text-sm text-neutral-200 outline-none placeholder:text-neutral-600"
      />
      <div className="flex max-h-64 flex-col gap-1 overflow-y-auto">
        {matches?.map((m) => (
          <button
            key={m.id}
            onClick={() => onPick({ id: m.id, title: m.title })}
            className="rounded px-3 py-2 text-left text-sm text-neutral-300 hover:bg-neutral-800"
          >
            {m.title}
          </button>
        ))}
        {debouncedQuery.trim() && matches?.length === 0 && (
          <p className="px-1 py-2 text-sm text-neutral-600">No notes match "{debouncedQuery}".</p>
        )}
      </div>
    </Modal>
  )
}
