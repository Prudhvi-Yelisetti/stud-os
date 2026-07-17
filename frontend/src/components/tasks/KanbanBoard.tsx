import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tasksApi } from '../../lib/tasks'
import type { Task, TaskStatus, TaskPriority } from '../../lib/api'

const COLUMNS: { status: TaskStatus; label: string }[] = [
  { status: 'backlog', label: 'Backlog' },
  { status: 'todo', label: 'Todo' },
  { status: 'in_progress', label: 'In Progress' },
  { status: 'done', label: 'Done' },
]

const PRIORITY_COLOR: Record<TaskPriority, string> = {
  low: 'bg-neutral-700',
  medium: 'bg-blue-700',
  high: 'bg-orange-700',
  urgent: 'bg-red-700',
}

export function KanbanBoard() {
  const queryClient = useQueryClient()
  const [newTitle, setNewTitle] = useState('')
  const [levelUpMessage, setLevelUpMessage] = useState<string | null>(null)

  const { data: tasks } = useQuery({ queryKey: ['tasks'], queryFn: () => tasksApi.list() })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['tasks'] })
    queryClient.invalidateQueries({ queryKey: ['gamification-profile'] })
  }

  const createTask = useMutation({
    mutationFn: (title: string) => tasksApi.create({ title }),
    onSuccess: invalidate,
  })

  const moveTask = useMutation({
    mutationFn: ({ id, status }: { id: string; status: TaskStatus }) => tasksApi.update(id, { status }),
    onSuccess: invalidate,
  })

  const completeTask = useMutation({
    mutationFn: (id: string) => tasksApi.complete(id),
    onSuccess: ({ gamification }) => {
      invalidate()
      const parts = [`+${gamification.xp_awarded} XP`]
      if (gamification.did_level_up) parts.push(`Level up! Now level ${gamification.current_level}`)
      if (gamification.newly_awarded_badges.length) {
        parts.push(`New badge: ${gamification.newly_awarded_badges.join(', ')}`)
      }
      setLevelUpMessage(parts.join(' · '))
      setTimeout(() => setLevelUpMessage(null), 4000)
    },
  })

  const byStatus = (status: TaskStatus) => tasks?.filter((t) => t.status === status) ?? []

  return (
    <div className="flex h-full flex-col p-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Tasks</h1>
        {levelUpMessage && (
          <div className="rounded bg-emerald-800 px-3 py-1.5 text-sm text-emerald-100">{levelUpMessage}</div>
        )}
      </div>
      <form
        className="mb-4 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault()
          if (newTitle.trim()) {
            createTask.mutate(newTitle.trim())
            setNewTitle('')
          }
        }}
      >
        <input
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          placeholder="New task..."
          className="w-72 rounded bg-neutral-900 px-3 py-2 text-sm outline-none placeholder:text-neutral-600"
        />
      </form>
      <div className="grid flex-1 grid-cols-4 gap-4 overflow-hidden">
        {COLUMNS.map((col) => (
          <div key={col.status} className="flex flex-col overflow-hidden rounded bg-neutral-900/50 p-3">
            <h2 className="mb-3 text-sm font-medium text-neutral-400">
              {col.label} ({byStatus(col.status).length})
            </h2>
            <div className="flex flex-1 flex-col gap-2 overflow-y-auto">
              {byStatus(col.status).map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  columns={COLUMNS}
                  onMove={(status) => moveTask.mutate({ id: task.id, status })}
                  onComplete={() => completeTask.mutate(task.id)}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function TaskCard({
  task,
  columns,
  onMove,
  onComplete,
}: {
  task: Task
  columns: { status: TaskStatus; label: string }[]
  onMove: (status: TaskStatus) => void
  onComplete: () => void
}) {
  return (
    <div className="rounded bg-neutral-800 p-2.5 text-sm">
      <div className="mb-1.5 flex items-center gap-1.5">
        <span className={`h-2 w-2 rounded-full ${PRIORITY_COLOR[task.priority]}`} />
        <span className="flex-1 truncate">{task.title}</span>
      </div>
      <div className="flex items-center justify-between gap-1">
        <select
          value={task.status}
          onChange={(e) => onMove(e.target.value as TaskStatus)}
          className="rounded bg-neutral-900 px-1.5 py-1 text-xs text-neutral-400 outline-none"
        >
          {columns.map((c) => (
            <option key={c.status} value={c.status}>
              {c.label}
            </option>
          ))}
        </select>
        {task.status !== 'done' && (
          <button
            onClick={onComplete}
            className="rounded bg-emerald-900 px-2 py-1 text-xs text-emerald-200 hover:bg-emerald-800"
          >
            Complete ✓
          </button>
        )}
      </div>
    </div>
  )
}
