import { useMemo } from 'react'
import type { JournalEntry, Mood } from '../../lib/api'

const MOOD_SCORE: Record<Mood, number> = { terrible: 1, bad: 2, okay: 3, good: 4, great: 5 }
const SCORE_COLOR = [
  'bg-neutral-800',     // 0: no entry
  'bg-red-900',         // 1: terrible
  'bg-orange-800',      // 2: bad
  'bg-yellow-700',      // 3: okay
  'bg-lime-700',        // 4: good
  'bg-emerald-600',     // 5: great
]

const DAYS_SHOWN = 91 // ~13 weeks, GitHub-contribution-graph style

function toISODate(d: Date): string {
  return d.toISOString().slice(0, 10)
}

function buildWeeks(entries: JournalEntry[]) {
  const moodByDate = new Map<string, Mood>()
  for (const e of entries) {
    if (e.mood) moodByDate.set(e.entry_date, e.mood)
  }

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const start = new Date(today)
  start.setDate(start.getDate() - (DAYS_SHOWN - 1))
  start.setDate(start.getDate() - start.getDay()) // align to Sunday

  const weeks: { date: string; mood: Mood | null }[][] = []
  const cursor = new Date(start)
  while (cursor <= today) {
    const week: { date: string; mood: Mood | null }[] = []
    for (let d = 0; d < 7; d++) {
      const iso = toISODate(cursor)
      week.push({ date: iso, mood: moodByDate.get(iso) ?? null })
      cursor.setDate(cursor.getDate() + 1)
    }
    weeks.push(week)
  }
  return weeks
}

export function MoodHeatmap({ entries }: { entries: JournalEntry[] }) {
  const weeks = useMemo(() => buildWeeks(entries), [entries])

  const recentWithMood = entries.filter((e) => e.mood)
  const avgScore = recentWithMood.length
    ? recentWithMood.reduce((sum, e) => sum + MOOD_SCORE[e.mood!], 0) / recentWithMood.length
    : null

  return (
    <div className="rounded bg-neutral-900 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-medium text-neutral-400">Mood, last {DAYS_SHOWN} days</h2>
        {avgScore !== null && (
          <span className="text-xs text-neutral-500">avg {avgScore.toFixed(1)}/5</span>
        )}
      </div>
      <div className="flex gap-1 overflow-x-auto">
        {weeks.map((week, wi) => (
          <div key={wi} className="flex flex-col gap-1">
            {week.map((day) => (
              <div
                key={day.date}
                title={day.mood ? `${day.date}: ${day.mood}` : day.date}
                className={`h-3 w-3 rounded-sm ${SCORE_COLOR[day.mood ? MOOD_SCORE[day.mood] : 0]}`}
              />
            ))}
          </div>
        ))}
      </div>
      <div className="mt-3 flex items-center gap-2 text-xs text-neutral-500">
        <span>Less</span>
        {SCORE_COLOR.map((c, i) => (
          <div key={i} className={`h-3 w-3 rounded-sm ${c}`} />
        ))}
        <span>Great</span>
      </div>
    </div>
  )
}
