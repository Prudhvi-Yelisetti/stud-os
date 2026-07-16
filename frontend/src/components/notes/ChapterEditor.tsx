import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notebooksApi } from '../../lib/notebooks'

export function ChapterEditor({ chapterId }: { chapterId: string }) {
  const queryClient = useQueryClient()
  const [content, setContent] = useState('')

  const { data: chapter } = useQuery({
    queryKey: ['chapter', chapterId],
    queryFn: () => notebooksApi.getChapter(chapterId),
  })

  const { data: backlinks } = useQuery({
    queryKey: ['backlinks', chapterId],
    queryFn: () => notebooksApi.getBacklinks(chapterId),
  })

  useEffect(() => {
    if (chapter) setContent(chapter.content)
  }, [chapter?.id])

  const save = useMutation({
    mutationFn: (newContent: string) => notebooksApi.updateChapter(chapterId, { content: newContent }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chapter', chapterId] })
      queryClient.invalidateQueries({ queryKey: ['backlinks'] })
    },
  })

  if (!chapter) return <div className="p-6 text-neutral-500">Loading...</div>

  return (
    <div className="flex h-full">
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold">{chapter.title}</h1>
          <span className="text-xs text-neutral-500">v{chapter.version}</span>
        </div>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onBlur={() => {
            if (content !== chapter.content) save.mutate(content)
          }}
          placeholder="Write markdown here. Use [[Chapter Title]] to link other chapters."
          className="h-[calc(100%-3rem)] w-full resize-none rounded bg-neutral-900 p-4 font-mono text-sm outline-none placeholder:text-neutral-600"
        />
      </div>
      <div className="w-64 shrink-0 border-l border-neutral-800 p-4">
        <h2 className="mb-2 text-sm font-medium text-neutral-400">Referenced by</h2>
        {backlinks && backlinks.length > 0 ? (
          <ul className="flex flex-col gap-1">
            {backlinks.map((b) => (
              <li key={b.id} className="rounded px-2 py-1 text-sm text-neutral-300 hover:bg-neutral-900">
                {b.title}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-neutral-600">No backlinks yet.</p>
        )}
      </div>
    </div>
  )
}
