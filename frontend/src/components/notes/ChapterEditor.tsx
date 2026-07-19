import { useEffect, useMemo, useRef, useState } from 'react'
import { useQuery, useQueries, useMutation, useQueryClient } from '@tanstack/react-query'
import { notebooksApi } from '../../lib/notebooks'
import { AttachmentPanel } from '../attachments/AttachmentPanel'
import { splitByWikiLinks, extractWikiLinkTitles, detectActiveWikiLinkQuery } from '../../lib/wikiLinks'

export function ChapterEditor({
  chapterId,
  onDeleted,
  onNavigate,
}: {
  chapterId: string
  onDeleted?: () => void
  onNavigate: (notebookId: string, chapterId: string) => void
}) {
  const queryClient = useQueryClient()
  const [content, setContent] = useState('')
  const [mode, setMode] = useState<'edit' | 'preview'>('edit')
  const [editingTitle, setEditingTitle] = useState(false)
  const [titleDraft, setTitleDraft] = useState('')
  const [suggestions, setSuggestions] = useState<{ id: string; title: string; notebook_id: string }[]>([])
  const [linkQueryStart, setLinkQueryStart] = useState<number | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

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
    queryClient.invalidateQueries({ queryKey: ['graph'] })
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

  const createChapter = useMutation({
    mutationFn: (title: string) => notebooksApi.createChapter(chapter!.notebook_id, { title }),
  })

  // Resolve every [[Title]] in the content to a real chapter (or null if
  // it doesn't exist yet) so preview mode can render clickable / creatable
  // links. Only runs in preview mode to avoid firing on every keystroke.
  const linkTitles = useMemo(() => extractWikiLinkTitles(content), [content])
  const titleQueries = useQueries({
    queries: linkTitles.map((title) => ({
      queryKey: ['chapter-title-match', title],
      queryFn: () => notebooksApi.searchChapterTitles(title),
      enabled: mode === 'preview',
      staleTime: 10_000,
    })),
  })

  const resolvedLinks = useMemo(() => {
    const map = new Map<string, { id: string; notebook_id: string } | null>()
    linkTitles.forEach((title, i) => {
      const matches = titleQueries[i]?.data
      const exact = matches?.find((m) => m.title.toLowerCase() === title.toLowerCase())
      map.set(title, exact ? { id: exact.id, notebook_id: exact.notebook_id } : null)
    })
    return map
  }, [linkTitles, titleQueries])

  function handleLinkClick(title: string) {
    const resolved = resolvedLinks.get(title)
    if (resolved) {
      onNavigate(resolved.notebook_id, resolved.id)
    } else if (chapter && confirm(`No chapter titled "${title}" yet. Create it in this notebook?`)) {
      createChapter.mutate(title, {
        onSuccess: (newChapter) => {
          queryClient.invalidateQueries({ queryKey: ['chapters'] })
          onNavigate(newChapter.notebook_id, newChapter.id)
        },
      })
    }
  }

  async function handleContentChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    const newContent = e.target.value
    setContent(newContent)

    const cursor = e.target.selectionStart
    const active = detectActiveWikiLinkQuery(newContent.slice(0, cursor))
    if (active && active.query.length > 0) {
      setLinkQueryStart(active.startIndex)
      const matches = await notebooksApi.searchChapterTitles(active.query)
      setSuggestions(matches)
    } else {
      setLinkQueryStart(null)
      setSuggestions([])
    }
  }

  function applySuggestion(title: string) {
    if (linkQueryStart === null || !textareaRef.current) return
    const cursor = textareaRef.current.selectionStart
    const before = content.slice(0, linkQueryStart)
    const after = content.slice(cursor)
    const newContent = `${before}[[${title}]]${after}`
    setContent(newContent)
    setSuggestions([])
    setLinkQueryStart(null)
    requestAnimationFrame(() => textareaRef.current?.focus())
  }

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
            <div className="flex overflow-hidden rounded border border-neutral-800 text-xs">
              <button
                onClick={() => setMode('edit')}
                className={`px-2 py-1 ${mode === 'edit' ? 'bg-neutral-700 text-white' : 'text-neutral-500 hover:text-neutral-300'}`}
              >
                Edit
              </button>
              <button
                onClick={() => setMode('preview')}
                className={`px-2 py-1 ${mode === 'preview' ? 'bg-neutral-700 text-white' : 'text-neutral-500 hover:text-neutral-300'}`}
              >
                Preview
              </button>
            </div>
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
        {mode === 'edit' ? (
          <div className="relative h-[calc(100%-3rem)]">
            <textarea
              ref={textareaRef}
              value={content}
              onChange={handleContentChange}
              onBlur={() => {
                setTimeout(() => setSuggestions([]), 150) // allow suggestion click to register first
                if (content !== chapter.content) save.mutate(content)
              }}
              placeholder="Write markdown here. Use [[Chapter Title]] to link other chapters."
              className="h-full w-full resize-none rounded bg-neutral-900 p-4 font-mono text-sm outline-none placeholder:text-neutral-600"
            />
            {suggestions.length > 0 && (
              <div className="absolute bottom-2 left-2 z-10 w-72 rounded bg-neutral-800 shadow-lg">
                {suggestions.map((s) => (
                  <button
                    key={s.id}
                    onMouseDown={(e) => {
                      e.preventDefault() // keep textarea focus so cursor position survives
                      applySuggestion(s.title)
                    }}
                    className="block w-full truncate px-3 py-2 text-left text-sm text-neutral-200 hover:bg-neutral-700"
                  >
                    {s.title}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="h-[calc(100%-3rem)] w-full overflow-y-auto whitespace-pre-wrap rounded bg-neutral-900 p-4 text-sm leading-relaxed">
            {splitByWikiLinks(content).map((part, i) =>
              part.type === 'text' ? (
                <span key={i}>{part.content}</span>
              ) : (
                <button
                  key={i}
                  onClick={() => handleLinkClick(part.content)}
                  className={
                    resolvedLinks.get(part.content)
                      ? 'text-emerald-400 underline decoration-emerald-700 hover:text-emerald-300'
                      : 'text-neutral-500 underline decoration-dashed decoration-neutral-600 hover:text-neutral-300'
                  }
                  title={resolvedLinks.get(part.content) ? 'Go to chapter' : 'Create this chapter'}
                >
                  {part.content}
                </button>
              ),
            )}
            {content.trim() === '' && <span className="text-neutral-600">Nothing written yet.</span>}
          </div>
        )}
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
