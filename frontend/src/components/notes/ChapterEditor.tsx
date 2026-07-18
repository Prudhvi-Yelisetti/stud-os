import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notebooksApi } from '../../lib/notebooks'
import { AttachmentPanel } from '../attachments/AttachmentPanel'

export function ChapterEditor({ chapterId, onDeleted }: { chapterId: string; onDeleted?: () => void }) {
  const queryClient = useQueryClient()
  const [content, setContent] = useState('')
  const [editingTitle, setEditingTitle] = useState(false)
  const [titleDraft, setTitleDraft] = useState('')

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

  const invalidateChapterLists = () => {
    queryClient.invalidateQueries({ queryKey: ['chapter', chapterId] })
    queryClient.invalidateQueries({ queryKey: ['chapters'] })
    queryClient.invalidateQueries({ queryKey: ['backlinks'] })
    queryClient.invalidateQueries({ queryKey: ['recent-chapters'] })
  }

  const save = useMutation({
    mutationFn: (newContent: string) => notebooksApi.updateChapter(chapterId, { content: newContent }),
    onSuccess: invalidateChapterLists,
  })

  const renameChapter = useMutation({
    mutationFn: (title: string) => notebooksApi.updateChapter(chapterId, { title }),
    onSuccess: invalidateChapterLists,
  })

  const togglePin = useMutation({
    mutationFn: (pinned: boolean) => notebooksApi.updateChapter(chapterId, { pinned }),
    onSuccess: invalidateChapterLists,
  })

  const deleteChapter = useMutation({
    mutationFn: () => notebooksApi.deleteChapter(chapterId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chapters'] })
      onDeleted?.()
    },
  })

  if (!chapter) return <div className="p-6 text-neutral-500">Loading...</div>

  return (
    <div className="flex h-full">
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mb-4 flex items-center justify-between">
          {editingTitle ? (
            <input
              autoFocus
              value={titleDraft}
              onChange={(e) => setTitleDraft(e.target.value)}
              onBlur={() => {
                if (titleDraft.trim() && titleDraft !== chapter.title) renameChapter.mutate(titleDraft.trim())
                setEditingTitle(false)
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') e.currentTarget.blur()
                if (e.key === 'Escape') setEditingTitle(false)
              }}
              className="bg-transparent text-xl font-semibold outline-none"
            />
          ) : (
            <h1
              className="cursor-text text-xl font-semibold"
              onClick={() => {
                setTitleDraft(chapter.title)
                setEditingTitle(true)
              }}
              title="Click to rename"
            >
              {chapter.title}
            </h1>
          )}
          <div className="flex items-center gap-3">
            <button
              onClick={() => togglePin.mutate(!chapter.pinned)}
              className={`text-sm ${chapter.pinned ? 'text-yellow-400' : 'text-neutral-600 hover:text-neutral-400'}`}
              title={chapter.pinned ? 'Unpin' : 'Pin'}
            >
              📌
            </button>
            <span className="text-xs text-neutral-500">v{chapter.version}</span>
            <button
              onClick={() => {
                if (confirm(`Delete chapter "${chapter.title}"?`)) deleteChapter.mutate()
              }}
              className="text-xs text-neutral-600 hover:text-red-400"
              title="Delete chapter"
            >
              ✕
            </button>
          </div>
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
        <AttachmentPanel ownerType="chapter" ownerId={chapterId} />
      </div>
    </div>
  )
}
