import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { NotebookList } from '../components/notes/NotebookList'
import { ChapterList } from '../components/notes/ChapterList'
import { ChapterEditor } from '../components/notes/ChapterEditor'
import { notebooksApi } from '../lib/notebooks'
import { useIsMobile } from '../lib/useIsMobile'

export function NotesPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [notebookId, setNotebookId] = useState<string | null>(null)
  const [chapterId, setChapterId] = useState<string | null>(null)
  const isMobile = useIsMobile()

  const { data: notebook } = useQuery({
    queryKey: ['notebook', notebookId],
    queryFn: () => notebooksApi.get(notebookId!),
    enabled: !!notebookId,
  })

  // Deep-link support: /notes?chapter=<id> (Journal wiki-links, Search) and
  // /notes?notebook=<id> (Search) resolve and select the target on load.
  useEffect(() => {
    const targetChapterId = searchParams.get('chapter')
    const targetNotebookId = searchParams.get('notebook')

    if (targetChapterId && targetChapterId !== chapterId) {
      notebooksApi.getChapter(targetChapterId).then((ch) => {
        setNotebookId(ch.notebook_id)
        setChapterId(ch.id)
      })
      setSearchParams({}, { replace: true })
    } else if (targetNotebookId && targetNotebookId !== notebookId) {
      setNotebookId(targetNotebookId)
      setChapterId(null)
      setSearchParams({}, { replace: true })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams])

  const handleNavigate = (targetNotebookId: string, targetChapterId: string) => {
    setNotebookId(targetNotebookId)
    setChapterId(targetChapterId)
  }

  if (!notebookId) {
    // Nothing selected yet -- just show the notebook list, centered, with
    // room to breathe rather than a skeleton of empty columns.
    return (
      <div className="flex h-full justify-center overflow-y-auto">
        <div className="w-full max-w-md p-6">
          <NotebookList
            selectedId={notebookId}
            onSelect={(id) => {
              setNotebookId(id)
              setChapterId(null)
            }}
            fullWidth
          />
        </div>
      </div>
    )
  }

  if (!chapterId) {
    // Notebook chosen, no chapter yet -- a 3rd column that just says
    // "select a chapter" added nothing. One focused view: back button,
    // notebook name, chapter list. Same shape on mobile and desktop.
    return (
      <div className="flex h-full justify-center overflow-y-auto">
        <div className="w-full max-w-md p-6">
          <button
            onClick={() => setNotebookId(null)}
            className="mb-3 text-sm text-neutral-400 hover:text-neutral-200"
          >
            ← Notebooks
          </button>
          <h1 className="mb-4 text-lg font-semibold">{notebook?.title}</h1>
          <ChapterList notebookId={notebookId} selectedId={chapterId} onSelect={setChapterId} fullWidth />
        </div>
      </div>
    )
  }

  if (isMobile) {
    return (
      <div className="flex h-full flex-col">
        <button
          onClick={() => setChapterId(null)}
          className="shrink-0 border-b border-neutral-800 px-4 py-2 text-left text-sm text-neutral-400"
        >
          ← Chapters
        </button>
        <div className="flex-1 overflow-hidden">
          <ChapterEditor chapterId={chapterId} onDeleted={() => setChapterId(null)} onNavigate={handleNavigate} />
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full">
      <div className="flex w-64 shrink-0 flex-col border-r border-neutral-800">
        <div className="border-b border-neutral-800 p-3">
          <button
            onClick={() => setNotebookId(null)}
            className="mb-1 text-xs text-neutral-500 hover:text-neutral-300"
          >
            ← Notebooks
          </button>
          <h1 className="truncate text-sm font-medium">{notebook?.title}</h1>
        </div>
        <div className="flex-1 overflow-y-auto">
          <ChapterList notebookId={notebookId} selectedId={chapterId} onSelect={setChapterId} fullWidth />
        </div>
      </div>
      <ChapterEditor chapterId={chapterId} onDeleted={() => setChapterId(null)} onNavigate={handleNavigate} />
    </div>
  )
}
