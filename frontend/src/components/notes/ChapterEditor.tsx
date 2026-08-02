import { useEffect, useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notebooksApi } from '../../lib/notebooks'
import { AttachmentPanel } from '../attachments/AttachmentPanel'
import { WikiLinkText } from '../shared/WikiLinkText'
import { useResolvedWikiLinks } from '../../lib/useResolvedWikiLinks'
import { detectActiveWikiLinkQuery } from '../../lib/wikiLinks'
import { VersionHistoryPanel } from './VersionHistoryPanel'
import { RelatedNotesPanel } from './RelatedNotesPanel'
import { QuizPanel } from './QuizPanel'

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
  const [showHistory, setShowHistory] = useState(false)
  const [showSidePanel, setShowSidePanel] = useState(false)
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

  // Only resolves in preview mode to avoid firing on every keystroke.
  const resolvedLinks = useResolvedWikiLinks(content, mode === 'preview')

  function handleResolvedClick(resolved: { id: string; notebook_id: string }) {
    onNavigate(resolved.notebook_id, resolved.id)
  }

  function handleUnresolvedClick(title: string) {
    if (chapter && confirm(`No chapter titled "${title}" yet. Create it in this notebook?`)) {
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

  const sidePanelContent = (
    <>
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
      <RelatedNotesPanel chapterId={chapterId} />
      <QuizPanel chapterId={chapterId} />
    </>
  )

  return (
    <div className="relative flex h-full flex-1 overflow-hidden">
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
              onClick={() => setShowSidePanel(true)}
              className="text-sm text-neutral-500 hover:text-neutral-300 md:hidden"
              title="Backlinks & attachments"
            >
              🔗
            </button>
            <button
              onClick={() => togglePin.mutate(!chapter.pinned)}
              className={`text-sm ${chapter.pinned ? 'text-yellow-400' : 'text-neutral-600 hover:text-neutral-400'}`}
              title={chapter.pinned ? 'Unpin' : 'Pin'}
            >
              📌
            </button>
            <button
              onClick={() => setShowHistory((v) => !v)}
              className="text-xs text-neutral-500 underline decoration-dotted hover:text-neutral-300"
              title="View version history"
            >
              v{chapter.version}
            </button>
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
          <div className="h-[calc(100%-3rem)] w-full overflow-y-auto rounded bg-neutral-900 p-4">
            <WikiLinkText
              content={content}
              resolvedLinks={resolvedLinks}
              onResolvedClick={handleResolvedClick}
              onUnresolvedClick={handleUnresolvedClick}
              emptyPlaceholder="Nothing written yet."
            />
          </div>
        )}
      </div>
      <div className="hidden w-64 shrink-0 border-l border-neutral-800 p-4 md:block">{sidePanelContent}</div>
      {showSidePanel && (
        <div className="absolute inset-y-0 right-0 z-10 w-full max-w-xs overflow-y-auto border-l border-neutral-800 bg-neutral-950 p-4 shadow-xl md:hidden">
          <button onClick={() => setShowSidePanel(false)} className="mb-3 text-sm text-neutral-500 hover:text-neutral-300">
            ✕ Close
          </button>
          {sidePanelContent}
        </div>
      )}
      {showHistory && <VersionHistoryPanel chapterId={chapterId} onClose={() => setShowHistory(false)} />}
    </div>
  )
}
