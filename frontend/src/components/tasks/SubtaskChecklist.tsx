import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { subtasksApi } from '../../lib/projects'

export function SubtaskChecklist({ taskId }: { taskId: string }) {
  const queryClient = useQueryClient()
  const [newTitle, setNewTitle] = useState('')
  const queryKey = ['subtasks', taskId]

  const { data: subtasks } = useQuery({ queryKey, queryFn: () => subtasksApi.list(taskId) })
  const invalidate = () => queryClient.invalidateQueries({ queryKey })

  const create = useMutation({
    mutationFn: (title: string) => subtasksApi.create(taskId, title),
    onSuccess: invalidate,
  })
  const toggle = useMutation({
    mutationFn: ({ id, done }: { id: string; done: boolean }) => subtasksApi.toggle(id, done),
    onSuccess: invalidate,
  })
  const remove = useMutation({
    mutationFn: (id: string) => subtasksApi.remove(id),
    onSuccess: invalidate,
  })

  const done = subtasks?.filter((s) => s.done).length ?? 0
  const total = subtasks?.length ?? 0

  return (
    <div onClick={(e) => e.stopPropagation()} className="mt-2 border-t border-neutral-700 pt-2">
      {total > 0 && (
        <p className="mb-1 text-[11px] text-neutral-500">
          {done}/{total} done
        </p>
      )}
      <div className="flex flex-col gap-1">
        {subtasks?.map((s) => (
          <div key={s.id} className="group flex items-center gap-1.5 text-xs">
            <input
              type="checkbox"
              checked={s.done}
              onChange={(e) => toggle.mutate({ id: s.id, done: e.target.checked })}
              className="shrink-0"
            />
            <span className={`flex-1 truncate ${s.done ? 'text-neutral-600 line-through' : 'text-neutral-300'}`}>
              {s.title}
            </span>
            <button
              onClick={() => remove.mutate(s.id)}
              className="hidden shrink-0 text-neutral-600 hover:text-red-400 group-hover:inline"
            >
              ✕
            </button>
          </div>
        ))}
      </div>
      <form
        className="mt-1"
        onSubmit={(e) => {
          e.preventDefault()
          if (newTitle.trim()) {
            create.mutate(newTitle.trim())
            setNewTitle('')
          }
        }}
      >
        <input
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          placeholder="+ subtask"
          className="w-full bg-transparent text-xs text-neutral-400 outline-none placeholder:text-neutral-600"
        />
      </form>
    </div>
  )
}
