import { useEffect, useState } from 'react'
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

  if (isMobile) {
    if (chapterId) {
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
    if (notebookId) {
      return (
        <div className="flex h-full flex-col">
          <button
            onClick={() => setNotebookId(null)}
            className="shrink-0 border-b border-neutral-800 px-4 py-2 text-left text-sm text-neutral-400"
          >
            ← Notebooks
          </button>
          <div className="flex-1 overflow-y-auto">
            <ChapterList notebookId={notebookId} selectedId={chapterId} onSelect={setChapterId} fullWidth />
          </div>
        </div>
      )
    }
    return (
      <NotebookList
        selectedId={notebookId}
        onSelect={(id) => {
          setNotebookId(id)
          setChapterId(null)
        }}
        fullWidth
      />
    )
  }

  if (!notebookId) {
    // Nothing selected yet -- showing the full 3-column skeleton (two of
    // them just saying "select something") is noisy for no reason. Just
    // show the notebook list, given more room to breathe.
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

  return (
    <div className="flex h-full">
      <NotebookList
        selectedId={notebookId}
        onSelect={(id) => {
          setNotebookId(id)
          setChapterId(null)
        }}
      />
      <ChapterList notebookId={notebookId} selectedId={chapterId} onSelect={setChapterId} />
      {chapterId ? (
        <ChapterEditor chapterId={chapterId} onDeleted={() => setChapterId(null)} onNavigate={handleNavigate} />
      ) : (
        <div className="flex-1 p-6 text-sm text-neutral-600">Select a chapter to start writing</div>
      )}
    </div>
  )
}
