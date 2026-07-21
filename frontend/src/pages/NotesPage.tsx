import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { NotebookList } from '../components/notes/NotebookList'
import { ChapterList } from '../components/notes/ChapterList'
import { ChapterEditor } from '../components/notes/ChapterEditor'
import { notebooksApi } from '../lib/notebooks'

export function NotesPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [notebookId, setNotebookId] = useState<string | null>(null)
  const [chapterId, setChapterId] = useState<string | null>(null)

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

  return (
    <div className="flex h-full">
      <NotebookList
        selectedId={notebookId}
        onSelect={(id) => {
          setNotebookId(id)
          setChapterId(null)
        }}
      />
      {notebookId ? (
        <ChapterList notebookId={notebookId} selectedId={chapterId} onSelect={setChapterId} />
      ) : (
        <div className="w-64 shrink-0 border-r border-neutral-800 p-6 text-sm text-neutral-600">
          Select a notebook
        </div>
      )}
      {chapterId ? (
        <ChapterEditor
          chapterId={chapterId}
          onDeleted={() => setChapterId(null)}
          onNavigate={(targetNotebookId, targetChapterId) => {
            setNotebookId(targetNotebookId)
            setChapterId(targetChapterId)
          }}
        />
      ) : (
        <div className="flex-1 p-6 text-sm text-neutral-600">Select a chapter to start writing</div>
      )}
    </div>
  )
}
