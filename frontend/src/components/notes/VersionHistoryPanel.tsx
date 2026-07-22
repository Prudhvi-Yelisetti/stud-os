import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notebooksApi } from '../../lib/notebooks'

export function VersionHistoryPanel({
  chapterId,
  onClose,
}: {
  chapterId: string
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const { data: versions } = useQuery({
    queryKey: ['chapter-versions', chapterId],
    queryFn: () => notebooksApi.listVersions(chapterId),
  })

  const restore = useMutation({
    mutationFn: (versionId: string) => notebooksApi.restoreVersion(chapterId, versionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chapter', chapterId] })
      queryClient.invalidateQueries({ queryKey: ['chapter-versions', chapterId] })
      queryClient.invalidateQueries({ queryKey: ['backlinks'] })
      onClose()
    },
  })

  return (
    <div className="absolute inset-y-0 right-0 z-10 w-80 overflow-y-auto border-l border-neutral-800 bg-neutral-950 p-4 shadow-xl">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-medium text-neutral-300">Version history</h2>
        <button onClick={onClose} className="text-neutral-500 hover:text-neutral-300">
          ✕
        </button>
      </div>
      <div className="flex flex-col gap-2">
        {versions?.map((v) => (
          <div key={v.id} className="rounded bg-neutral-900 p-3">
            <div className="mb-1 flex items-center justify-between">
              <span className="text-xs font-medium text-neutral-400">v{v.version_number}</span>
              <span className="text-xs text-neutral-600">{new Date(v.created_at).toLocaleString()}</span>
            </div>
            <p className="mb-2 line-clamp-3 whitespace-pre-wrap text-xs text-neutral-400">
              {v.content_snapshot || '(empty)'}
            </p>
            <button
              onClick={() => {
                if (confirm(`Restore to v${v.version_number}? The current content will be saved to history first.`)) {
                  restore.mutate(v.id)
                }
              }}
              className="rounded bg-neutral-800 px-2 py-1 text-xs text-neutral-300 hover:bg-neutral-700"
            >
              Restore this version
            </button>
          </div>
        ))}
        {versions?.length === 0 && (
          <p className="text-sm text-neutral-600">No past versions yet — edit the content to start building history.</p>
        )}
      </div>
    </div>
  )
}
