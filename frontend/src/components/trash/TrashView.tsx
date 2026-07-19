import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { trashApi } from '../../lib/trash'
import type { TrashedItem } from '../../lib/api'

const TYPE_ICON: Record<TrashedItem['type'], string> = {
  notebook: '📓',
  chapter: '📄',
  task: '✅',
  journal: '📔',
  project: '📁',
}

export function TrashView() {
  const queryClient = useQueryClient()
  const { data: items } = useQuery({ queryKey: ['trash'], queryFn: trashApi.list })

  const invalidateAll = () => {
    // Restoring/purging an item can affect nearly every list view, so
    // invalidate broadly rather than tracking each entity's query key here.
    queryClient.invalidateQueries()
  }

  const restore = useMutation({
    mutationFn: ({ type, id }: { type: string; id: string }) => trashApi.restore(type, id),
    onSuccess: invalidateAll,
  })

  const purge = useMutation({
    mutationFn: ({ type, id }: { type: string; id: string }) => trashApi.permanentlyDelete(type, id),
    onSuccess: invalidateAll,
  })

  return (
    <div className="h-full overflow-y-auto p-6">
      <h1 className="mb-2 text-xl font-semibold">Trash</h1>
      <p className="mb-6 text-sm text-neutral-500">
        Deleted items land here first. Restore them or permanently remove them.
      </p>
      <div className="flex flex-col gap-2">
        {items?.map((item) => (
          <div
            key={`${item.type}-${item.id}`}
            className="flex items-center justify-between rounded bg-neutral-900 px-3 py-2 text-sm"
          >
            <div className="flex items-center gap-2 truncate">
              <span>{TYPE_ICON[item.type]}</span>
              <span className="truncate">{item.title}</span>
              <span className="text-xs uppercase text-neutral-600">{item.type}</span>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <span className="text-xs text-neutral-600">
                {item.trashed_at && new Date(item.trashed_at).toLocaleDateString()}
              </span>
              <button
                onClick={() => restore.mutate({ type: item.type, id: item.id })}
                className="rounded bg-neutral-800 px-2 py-1 text-xs text-neutral-300 hover:bg-neutral-700"
              >
                Restore
              </button>
              <button
                onClick={() => {
                  if (confirm(`Permanently delete "${item.title}"? This cannot be undone.`)) {
                    purge.mutate({ type: item.type, id: item.id })
                  }
                }}
                className="rounded bg-red-950 px-2 py-1 text-xs text-red-300 hover:bg-red-900"
              >
                Delete forever
              </button>
            </div>
          </div>
        ))}
        {items?.length === 0 && <p className="text-sm text-neutral-600">Trash is empty.</p>}
      </div>
    </div>
  )
}
