import { useQuery } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { tagsApi } from '../lib/tags'

const TYPE_ICON: Record<string, string> = {
  chapter: '📄',
  journal: '📔',
}

export function TagsPage() {
  const navigate = useNavigate()
  const { tagName } = useParams<{ tagName?: string }>()

  const { data: tags } = useQuery({ queryKey: ['tags'], queryFn: tagsApi.list })
  const { data: taggedItems } = useQuery({
    queryKey: ['tagged-items', tagName],
    queryFn: () => tagsApi.getTagged(tagName!),
    enabled: !!tagName,
  })

  function openItem(type: string, id: string) {
    if (type === 'chapter') navigate(`/notes?chapter=${id}`)
    else if (type === 'journal') navigate('/journal')
  }

  if (tagName) {
    return (
      <div className="h-full overflow-y-auto p-6">
        <button onClick={() => navigate('/tags')} className="mb-3 text-sm text-neutral-400 hover:text-neutral-200">
          ← All tags
        </button>
        <h1 className="mb-4 text-xl font-semibold">#{tagName}</h1>
        <div className="flex flex-col gap-1">
          {taggedItems?.map((item) => (
            <button
              key={`${item.type}-${item.id}`}
              onClick={() => openItem(item.type, item.id)}
              className="flex items-center gap-2 rounded px-3 py-2 text-left text-sm text-neutral-300 hover:bg-neutral-900"
            >
              <span>{TYPE_ICON[item.type]}</span>
              {item.title}
            </button>
          ))}
          {taggedItems?.length === 0 && <p className="text-sm text-neutral-600">Nothing tagged #{tagName}.</p>}
        </div>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      <h1 className="mb-4 text-xl font-semibold">Tags</h1>
      <div className="flex flex-wrap gap-2">
        {tags?.map((t) => (
          <button
            key={t.name}
            onClick={() => navigate(`/tags/${encodeURIComponent(t.name)}`)}
            className="rounded bg-indigo-950 px-3 py-1.5 text-sm text-indigo-300 hover:bg-indigo-900"
          >
            #{t.name} <span className="text-indigo-500">{t.count}</span>
          </button>
        ))}
      </div>
      {tags?.length === 0 && (
        <p className="text-sm text-neutral-600">
          No tags yet — add #tags to a note or journal entry to see them here.
        </p>
      )}
    </div>
  )
}
