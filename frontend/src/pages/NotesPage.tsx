import { useState } from 'react'
import { NotebookList } from '../components/notes/NotebookList'
import { ChapterList } from '../components/notes/ChapterList'
import { ChapterEditor } from '../components/notes/ChapterEditor'

export function NotesPage() {
  const [notebookId, setNotebookId] = useState<string | null>(null)
  const [chapterId, setChapterId] = useState<string | null>(null)

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
        <ChapterEditor chapterId={chapterId} onDeleted={() => setChapterId(null)} />
      ) : (
        <div className="flex-1 p-6 text-sm text-neutral-600">Select a chapter to start writing</div>
      )}
    </div>
  )
}
