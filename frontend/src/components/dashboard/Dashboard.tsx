import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { tasksApi } from '../../lib/tasks'
import { journalApi } from '../../lib/journal'
import { notebooksApi } from '../../lib/notebooks'
import { gamificationApi } from '../../lib/gamification'
import { graphApi } from '../../lib/search'

function Widget({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded bg-neutral-900 p-4">
      <h2 className="mb-3 text-sm font-medium text-neutral-400">{title}</h2>
      {children}
    </div>
  )
}

export function Dashboard() {
  const { data: tasks } = useQuery({ queryKey: ['tasks'], queryFn: () => tasksApi.list() })
  const { data: entries } = useQuery({ queryKey: ['journal'], queryFn: journalApi.list })
  const { data: recentChapters } = useQuery({
    queryKey: ['recent-chapters'],
    queryFn: () => notebooksApi.listRecentChapters(5),
  })
  const { data: profile } = useQuery({
    queryKey: ['gamification-profile'],
    queryFn: gamificationApi.profile,
  })
  const { data: graph } = useQuery({ queryKey: ['graph'], queryFn: graphApi.get })

  // tasksApi.list() already comes back sorted by real urgency (priority
  // weight, then soonest due date) from the backend -- this widget just
  // needs to surface that order and flag anything actually overdue.
  const pendingTasks = tasks?.filter((t) => t.status !== 'done') ?? []

  const allLoaded = tasks && entries && recentChapters
  const isFreshWorkspace = allLoaded && tasks.length === 0 && entries.length === 0 && recentChapters.length === 0

  return (
    <div className="h-full overflow-y-auto p-6">
      <h1 className="mb-6 text-xl font-semibold">Dashboard</h1>

      {isFreshWorkspace && (
        <div className="mb-6 rounded border border-neutral-800 bg-neutral-900 p-6">
          <h2 className="mb-1 text-lg font-medium">Welcome to Stud-OS 👋</h2>
          <p className="mb-4 text-sm text-neutral-400">
            Nothing here yet — this dashboard fills in as you use the app. A few places to start:
          </p>
          <div className="flex flex-wrap gap-3">
            <Link to="/notes" className="rounded bg-neutral-800 px-3 py-2 text-sm hover:bg-neutral-700">
              📓 Write your first note
            </Link>
            <Link to="/tasks" className="rounded bg-neutral-800 px-3 py-2 text-sm hover:bg-neutral-700">
              ✅ Add a task
            </Link>
            <Link to="/journal" className="rounded bg-neutral-800 px-3 py-2 text-sm hover:bg-neutral-700">
              📔 Journal today
            </Link>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Widget title="Tasks Due">
          <ul className="flex flex-col gap-1.5 text-sm">
            {pendingTasks.slice(0, 6).map((t) => {
              const isOverdue = t.due_at && new Date(t.due_at) < new Date()
              return (
                <li key={t.id} className="flex items-center justify-between gap-2">
                  <span className="truncate">{t.title}</span>
                  <span className={`shrink-0 text-xs ${isOverdue ? 'font-medium text-red-400' : 'text-neutral-500'}`}>
                    {t.due_at
                      ? `${isOverdue ? 'Overdue ' : ''}${new Date(t.due_at).toLocaleDateString()}`
                      : t.status}
                  </span>
                </li>
              )
            })}
            {pendingTasks.length === 0 && <li className="text-neutral-600">Nothing pending 🎉</li>}
          </ul>
        </Widget>

        <Widget title="Recent Notes">
          <ul className="flex flex-col gap-1.5 text-sm">
            {recentChapters?.map((c) => <li key={c.id} className="truncate">{c.title}</li>)}
            {recentChapters?.length === 0 && <li className="text-neutral-600">No notes yet</li>}
          </ul>
        </Widget>

        <Widget title="Journal Activity">
          <ul className="flex flex-col gap-1.5 text-sm">
            {entries?.slice(0, 5).map((e) => (
              <li key={e.id} className="flex items-center justify-between">
                <span className="truncate">{e.title}</span>
                <span className="text-xs text-neutral-500">{e.entry_date}</span>
              </li>
            ))}
            {entries?.length === 0 && <li className="text-neutral-600">No entries yet</li>}
          </ul>
        </Widget>

        <Widget title="Learning Progress">
          {profile && (
            <div className="text-sm">
              <p className="mb-1">Level {profile.level.current_level}</p>
              <p className="mb-1 text-neutral-400">{profile.level.current_xp} total XP</p>
              <p className="text-neutral-400">{profile.badges.length} badges earned</p>
            </div>
          )}
        </Widget>

        <Widget title="Graph Activity">
          {graph && (
            <div className="text-sm text-neutral-400">
              <p>{graph.nodes.length} nodes</p>
              <p>{graph.edges.length} connections</p>
            </div>
          )}
        </Widget>
      </div>
    </div>
  )
}
