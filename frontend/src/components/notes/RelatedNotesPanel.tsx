import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { aiApi } from '../../lib/ai'

export function RelatedNotesPanel({ chapterId }: { chapterId: string }) {
  const navigate = useNavigate()
  const { data: related } = useQuery({
    queryKey: ['related-notes', chapterId],
    queryFn: () => aiApi.relatedNotes(chapterId),
  })

  if (related && related.length === 0) return null

  return (
    <div className="mt-6">
      <h2 className="mb-2 text-sm font-medium text-neutral-400">Related notes</h2>
      {related ? (
        <ul className="flex flex-col gap-1">
          {related.map((r) => (
            <li key={`${r.type}-${r.id}`}>
              <button
                onClick={() => navigate(r.type === 'chapter' ? `/notes?chapter=${r.id}` : '/journal')}
                className="block w-full truncate rounded px-2 py-1 text-left text-sm text-neutral-300 hover:bg-neutral-900"
                title={r.snippet}
              >
                {r.title}
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-neutral-600">Loading…</p>
      )}
    </div>
  )
}
