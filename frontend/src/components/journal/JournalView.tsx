import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { journalApi } from '../../lib/journal'
import type { Mood } from '../../lib/api'
import { WikiLinkText } from '../shared/WikiLinkText'
import { useResolvedWikiLinks } from '../../lib/useResolvedWikiLinks'
import { MoodHeatmap } from './MoodHeatmap'

const MOOD_EMOJI: Record<Mood, string> = {
  great: '🤩',
  good: '🙂',
  okay: '😐',
  bad: '🙁',
  terrible: '😞',
}

const MOODS: Mood[] = ['great', 'good', 'okay', 'bad', 'terrible']

// Journal entries have no notebook of their own, so unresolved [[links]]
// can't be created in-context the way they can from a chapter -- they
// render distinctly but stay inert (WikiLinkText's default when no
// onUnresolvedClick is passed). Resolved links navigate into Notes.
function JournalEntryContent({ content }: { content: string }) {
  const navigate = useNavigate()
  const resolvedLinks = useResolvedWikiLinks(content, true)

  return (
    <WikiLinkText
      content={content}
      resolvedLinks={resolvedLinks}
      onResolvedClick={(resolved) => navigate(`/notes?chapter=${resolved.id}`)}
    />
  )
}

export function JournalView() {
  const queryClient = useQueryClient()
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [mood, setMood] = useState<Mood>('okay')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [editContent, setEditContent] = useState('')
  const [editMood, setEditMood] = useState<Mood>('okay')

  const { data: entries } = useQuery({ queryKey: ['journal'], queryFn: journalApi.list })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['journal'] })

  const createEntry = useMutation({
    mutationFn: () =>
      journalApi.create({
        title: title.trim(),
        content,
        mood,
        entry_date: new Date().toISOString().slice(0, 10),
      }),
    onSuccess: () => {
      invalidate()
      setTitle('')
      setContent('')
      setMood('okay')
    },
  })

  const updateEntry = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { title: string; content: string; mood: Mood } }) =>
      journalApi.update(id, data),
    onSuccess: () => {
      invalidate()
      setEditingId(null)
    },
  })

  const deleteEntry = useMutation({
    mutationFn: (id: string) => journalApi.remove(id),
    onSuccess: invalidate,
  })

  function startEdit(entry: NonNullable<typeof entries>[number]) {
    setEditingId(entry.id)
    setEditTitle(entry.title)
    setEditContent(entry.content)
    setEditMood(entry.mood ?? 'okay')
  }

  return (
    <div className="flex h-full flex-col overflow-y-auto md:flex-row md:overflow-hidden">
      <div className="w-full shrink-0 border-b border-neutral-800 p-6 md:w-96 md:border-b-0 md:border-r">
        <h1 className="mb-4 text-xl font-semibold">New entry</h1>
        <form
          className="flex flex-col gap-3"
          onSubmit={(e) => {
            e.preventDefault()
            if (title.trim()) createEntry.mutate()
          }}
        >
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Title..."
            className="rounded bg-neutral-900 px-3 py-2 text-sm outline-none placeholder:text-neutral-600"
          />
          <div className="flex gap-1.5">
            {MOODS.map((m) => (
              <button
                type="button"
                key={m}
                onClick={() => setMood(m)}
                className={`rounded px-2 py-1.5 text-lg ${mood === m ? 'bg-neutral-700' : 'bg-neutral-900'}`}
                title={m}
              >
                {MOOD_EMOJI[m]}
              </button>
            ))}
          </div>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="What happened today? Use [[Chapter Title]] to link notes."
            className="h-40 resize-none rounded bg-neutral-900 p-3 text-sm outline-none placeholder:text-neutral-600"
          />
          <button
            type="submit"
            className="rounded bg-neutral-700 px-3 py-2 text-sm font-medium hover:bg-neutral-600"
          >
            Save entry
          </button>
        </form>
      </div>

      <div className="flex-1 p-6 md:overflow-y-auto">
        {entries && entries.length > 0 && <MoodHeatmap entries={entries} />}
        <h2 className="mb-3 mt-6 text-sm font-medium text-neutral-400">Past entries</h2>
        <div className="flex flex-col gap-3">
          {entries?.map((entry) =>
            editingId === entry.id ? (
              <div key={entry.id} className="rounded bg-neutral-900 p-4">
                <input
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="mb-2 w-full bg-transparent font-medium outline-none"
                />
                <div className="mb-2 flex gap-1">
                  {MOODS.map((m) => (
                    <button
                      key={m}
                      onClick={() => setEditMood(m)}
                      className={`rounded px-1.5 py-1 text-base ${editMood === m ? 'bg-neutral-700' : 'bg-neutral-800'}`}
                    >
                      {MOOD_EMOJI[m]}
                    </button>
                  ))}
                </div>
                <textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  className="mb-2 h-28 w-full resize-none rounded bg-neutral-800 p-2 text-sm outline-none"
                />
                <div className="flex gap-2">
                  <button
                    onClick={() =>
                      updateEntry.mutate({
                        id: entry.id,
                        data: { title: editTitle, content: editContent, mood: editMood },
                      })
                    }
                    className="rounded bg-emerald-800 px-2 py-1 text-xs text-emerald-100 hover:bg-emerald-700"
                  >
                    Save
                  </button>
                  <button
                    onClick={() => setEditingId(null)}
                    className="rounded bg-neutral-800 px-2 py-1 text-xs text-neutral-400 hover:bg-neutral-700"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div key={entry.id} className="group rounded bg-neutral-900 p-4">
                <div className="mb-1 flex items-center justify-between">
                  <h3 className="font-medium">{entry.title}</h3>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-neutral-500">
                      {entry.mood && MOOD_EMOJI[entry.mood]} {entry.entry_date}
                    </span>
                    <button
                      onClick={() => startEdit(entry)}
                      className="hidden text-neutral-600 hover:text-neutral-300 group-hover:inline"
                      title="Edit"
                    >
                      ✏️
                    </button>
                    <button
                      onClick={() => {
                        if (confirm(`Delete entry "${entry.title}"?`)) deleteEntry.mutate(entry.id)
                      }}
                      className="hidden text-neutral-600 hover:text-red-400 group-hover:inline"
                      title="Delete"
                    >
                      ✕
                    </button>
                  </div>
                </div>
                <JournalEntryContent content={entry.content} />
              </div>
            ),
          )}
          {entries?.length === 0 && <p className="text-sm text-neutral-600">No entries yet.</p>}
        </div>
      </div>
    </div>
  )
}
