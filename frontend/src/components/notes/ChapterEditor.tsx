import { useEffect, useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { notebooksApi } from '../../lib/notebooks'
import { AttachmentPanel } from '../attachments/AttachmentPanel'
import { PropertiesPanel } from '../shared/PropertiesPanel'
import { ContentWithEmbeds } from '../shared/ContentWithEmbeds'
import { LiveMarkdownEditor, type LiveMarkdownEditorHandle } from '../shared/LiveMarkdownEditor'
import { useResolvedWikiLinks } from '../../lib/useResolvedWikiLinks'
import { detectActiveWikiLinkQuery } from '../../lib/wikiLinks'
import { stripFrontmatter } from '../../lib/frontmatter'
import { VersionHistoryPanel } from './VersionHistoryPanel'
import { RelatedNotesPanel } from './RelatedNotesPanel'
import { QuizPanel } from './QuizPanel'
import { OutlineSidebar } from './OutlineSidebar'
import { LocalGraphModal } from '../graph/LocalGraphModal'

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
  const navigate = useNavigate()
  const [content, setContent] = useState('')
  const [mode, setMode] = useState<'edit' | 'preview'>('edit')
  const [editingTitle, setEditingTitle] = useState(false)
  const [titleDraft, setTitleDraft] = useState('')
  const [suggestions, setSuggestions] = useState<{ id: string; title: string; notebook_id: string }[]>([])
  const [linkQueryStart, setLinkQueryStart] = useState<number | null>(null)
  const [showHistory, setShowHistory] = useState(false)
  const [showSidePanel, setShowSidePanel] = useState(false)
  const [showLocalGraph, setShowLocalGraph] = useState(false)
  const editorRef = useRef<LiveMarkdownEditorHandle>(null)
  const previewRef = useRef<HTMLDivElement>(null)

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

  const toggleTemplate = useMutation({
    mutationFn: (is_template: boolean) => notebooksApi.updateChapter(chapterId, { is_template }),
    onSuccess: invalidateChapterLists,
  })

  const toggleDailyTemplate = useMutation({
    mutationFn: (is_daily_template: boolean) => notebooksApi.updateChapter(chapterId, { is_daily_template }),
    onSuccess: invalidateChapterLists,
  })

  const saveProperties = useMutation({
    mutationFn: (properties: Record<string, unknown>) => notebooksApi.updateChapterProperties(chapterId, properties),
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

  function handleTagClick(tag: string) {
    navigate(`/tags/${encodeURIComponent(tag)}`)
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

  // Ctrl/Cmd+click on a wiki-link or embed marker while editing --
  // resolved on demand since edit mode doesn't keep a live resolvedLinks
  // map (that's only computed in preview mode, to avoid a lookup on
  // every keystroke). Falls back to the create-new-chapter prompt so
  // Ctrl+click on an unresolved link behaves the same as clicking it in
  // Preview.
  async function handleEditorLinkClick(title: string) {
    const matches = await notebooksApi.searchChapterTitles(title)
    const exact = matches.find((m) => m.title.toLowerCase() === title.toLowerCase())
    if (exact) onNavigate(exact.notebook_id, exact.id)
    else handleUnresolvedClick(title)
  }

  function handleContentChange(newContent: string, cursor: number) {
    setContent(newContent)

    const active = detectActiveWikiLinkQuery(newContent.slice(0, cursor))
    if (active && active.query.length > 0) {
      setLinkQueryStart(active.startIndex)
      notebooksApi.searchChapterTitles(active.query).then(setSuggestions)
    } else {
      setLinkQueryStart(null)
      setSuggestions([])
    }
  }

  function applySuggestion(title: string) {
    if (linkQueryStart === null || !editorRef.current) return
    // Re-derive the in-progress "[[query" length directly from content at
    // linkQueryStart -- more reliable than trying to track the cursor
    // position separately as the user types.
    const activeQuery = content.slice(linkQueryStart).match(/^\[\[([^[\]]*)/)
    const queryLength = activeQuery ? activeQuery[0].length : 0
    editorRef.current.insertAtCursor(`[[${title}]]`, linkQueryStart, linkQueryStart + queryLength)
    setSuggestions([])
    setLinkQueryStart(null)
  }

  if (!chapter) return <div className="p-6 text-neutral-500">Loading...</div>

  const sidePanelContent = (
    <>
      {mode === 'preview' && <OutlineSidebar content={stripFrontmatter(content)} scrollContainerRef={previewRef} />}
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
      <PropertiesPanel properties={chapter.properties} onSave={(props) => saveProperties.mutate(props)} />
      <div className="mt-4 border-t border-neutral-800 pt-3">
        <h3 className="mb-2 text-xs font-medium text-neutral-500">Template</h3>
        <label className="mb-1 flex items-center gap-2 text-xs text-neutral-400">
          <input
            type="checkbox"
            checked={chapter.is_template}
            onChange={(e) => toggleTemplate.mutate(e.target.checked)}
          />
          Use as template
        </label>
        <label className="flex items-center gap-2 text-xs text-neutral-400">
          <input
            type="checkbox"
            checked={chapter.is_daily_template}
            onChange={(e) => toggleDailyTemplate.mutate(e.target.checked)}
          />
          Use for daily notes
        </label>
      </div>
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
              onClick={() => setShowLocalGraph(true)}
              className="text-sm text-neutral-500 hover:text-neutral-300"
              title="Local graph"
            >
              🕸️
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
          <div className="relative h-[calc(100%-3rem)] rounded bg-neutral-900 p-4">
            <LiveMarkdownEditor
              ref={editorRef}
              value={content}
              onChange={handleContentChange}
              onBlur={() => {
                setTimeout(() => setSuggestions([]), 150) // allow suggestion click to register first
                if (content !== chapter.content) save.mutate(content)
              }}
              placeholder="Write markdown here. Use [[Chapter Title]] to link other chapters, ![[Chapter Title]] to embed one, #tag for tags. Ctrl/Cmd+click a link, embed, or tag to open it."
              onWikiLinkClick={handleEditorLinkClick}
              onEmbedClick={handleEditorLinkClick}
              onTagClick={handleTagClick}
            />
            {suggestions.length > 0 && (
              <div className="absolute bottom-2 left-2 z-10 w-72 rounded bg-neutral-800 shadow-lg">
                {suggestions.map((s) => (
                  <button
                    key={s.id}
                    onMouseDown={(e) => {
                      e.preventDefault() // keep editor focus so cursor position survives
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
          <div ref={previewRef} className="h-[calc(100%-3rem)] w-full overflow-y-auto rounded bg-neutral-900 p-4">
            <ContentWithEmbeds
              content={stripFrontmatter(content)}
              resolvedLinks={resolvedLinks}
              onNavigate={handleResolvedClick}
              onUnresolvedClick={handleUnresolvedClick}
              onTagClick={handleTagClick}
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
      {showLocalGraph && (
        <LocalGraphModal
          focalId={chapterId}
          onClose={() => setShowLocalGraph(false)}
          onNavigateChapter={onNavigate}
        />
      )}
    </div>
  )
}
