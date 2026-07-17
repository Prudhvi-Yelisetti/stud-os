import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { journalApi } from '../../lib/journal'
import type { Mood } from '../../lib/api'

const MOOD_EMOJI: Record<Mood, string> = {
  great: '🤩',
  good: '🙂',
  okay: '😐',
  bad: '🙁',
  terrible: '😞',
}

const MOODS: Mood[] = ['great', 'good', 'okay', 'bad', 'terrible']

export function JournalView() {
  const queryClient = useQueryClient()
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [mood, setMood] = useState<Mood>('okay')

  const { data: entries } = useQuery({ queryKey: ['journal'], queryFn: journalApi.list })

  const createEntry = useMutation({
    mutationFn: () =>
      journalApi.create({
        title: title.trim(),
        content,
        mood,
        entry_date: new Date().toISOString().slice(0, 10),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journal'] })
      setTitle('')
      setContent('')
      setMood('okay')
    },
  })

  return (
    <div className="flex h-full">
      <div className="w-96 shrink-0 border-r border-neutral-800 p-6">
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

      <div className="flex-1 overflow-y-auto p-6">
        <h2 className="mb-3 text-sm font-medium text-neutral-400">Past entries</h2>
        <div className="flex flex-col gap-3">
          {entries?.map((entry) => (
            <div key={entry.id} className="rounded bg-neutral-900 p-4">
              <div className="mb-1 flex items-center justify-between">
                <h3 className="font-medium">{entry.title}</h3>
                <span className="text-xs text-neutral-500">
                  {entry.mood && MOOD_EMOJI[entry.mood]} {entry.entry_date}
                </span>
              </div>
              <p className="whitespace-pre-wrap text-sm text-neutral-300">{entry.content}</p>
            </div>
          ))}
          {entries?.length === 0 && <p className="text-sm text-neutral-600">No entries yet.</p>}
        </div>
      </div>
    </div>
  )
}
