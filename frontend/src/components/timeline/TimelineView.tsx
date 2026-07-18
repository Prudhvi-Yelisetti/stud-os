import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { notebooksApi } from '../../lib/notebooks'
import { tasksApi } from '../../lib/tasks'
import { journalApi } from '../../lib/journal'

interface TimelineEvent {
  id: string
  date: string // ISO
  type: 'chapter' | 'task' | 'journal'
  label: string
}

const TYPE_ICON: Record<TimelineEvent['type'], string> = {
  chapter: '📄',
  task: '✅',
  journal: '📔',
}

function monthKey(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
}

export function TimelineView() {
  const { data: chapters } = useQuery({
    queryKey: ['recent-chapters', 200],
    queryFn: () => notebooksApi.listRecentChapters(200),
  })
  const { data: tasks } = useQuery({ queryKey: ['tasks'], queryFn: () => tasksApi.list() })
  const { data: entries } = useQuery({ queryKey: ['journal'], queryFn: journalApi.list })

  const grouped = useMemo(() => {
    const events: TimelineEvent[] = []
    chapters?.forEach((c) => events.push({ id: c.id, date: c.created_at, type: 'chapter', label: c.title }))
    tasks
      ?.filter((t) => t.completed_at)
      .forEach((t) => events.push({ id: t.id, date: t.completed_at!, type: 'task', label: t.title }))
    entries?.forEach((e) => events.push({ id: e.id, date: e.created_at, type: 'journal', label: e.title }))

    events.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())

    const byMonth = new Map<string, TimelineEvent[]>()
    for (const ev of events) {
      const key = monthKey(ev.date)
      if (!byMonth.has(key)) byMonth.set(key, [])
      byMonth.get(key)!.push(ev)
    }
    return byMonth
  }, [chapters, tasks, entries])

  return (
    <div className="h-full overflow-y-auto p-6">
      <h1 className="mb-6 text-xl font-semibold">Timeline</h1>
      <div className="flex flex-col gap-6">
        {Array.from(grouped.entries()).map(([month, events]) => (
          <div key={month}>
            <h2 className="mb-2 text-sm font-medium text-neutral-400">{month}</h2>
            <div className="flex flex-col gap-1.5 border-l border-neutral-800 pl-4">
              {events.map((ev) => (
                <div key={`${ev.type}-${ev.id}`} className="flex items-center gap-2 text-sm">
                  <span>{TYPE_ICON[ev.type]}</span>
                  <span className="truncate">{ev.label}</span>
                  <span className="ml-auto text-xs text-neutral-600">
                    {new Date(ev.date).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
        {grouped.size === 0 && <p className="text-sm text-neutral-600">Nothing to show yet.</p>}
      </div>
    </div>
  )
}
