import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { dailyNotesApi } from '../../lib/dailyNotes'

interface Command {
  id: string
  label: string
  run: (navigate: ReturnType<typeof useNavigate>) => void | Promise<void>
}

const NAV_COMMANDS: Command[] = [
  { id: 'nav-dashboard', label: 'Go to Dashboard', run: (nav) => nav('/') },
  { id: 'nav-notes', label: 'Go to Notes', run: (nav) => nav('/notes') },
  { id: 'nav-tasks', label: 'Go to Tasks', run: (nav) => nav('/tasks') },
  { id: 'nav-journal', label: 'Go to Journal', run: (nav) => nav('/journal') },
  { id: 'nav-projects', label: 'Go to Projects', run: (nav) => nav('/projects') },
  { id: 'nav-graph', label: 'Go to Graph', run: (nav) => nav('/graph') },
  { id: 'nav-tags', label: 'Go to Tags', run: (nav) => nav('/tags') },
  { id: 'nav-canvas', label: 'Go to Canvas', run: (nav) => nav('/canvas') },
  { id: 'nav-timeline', label: 'Go to Timeline', run: (nav) => nav('/timeline') },
  { id: 'nav-trash', label: 'Go to Trash', run: (nav) => nav('/trash') },
  { id: 'nav-ask', label: 'Go to Ask', run: (nav) => nav('/ask') },
  { id: 'nav-settings', label: 'Go to Settings', run: (nav) => nav('/settings') },
  {
    id: 'today',
    label: "Open today's daily note",
    run: async (nav) => {
      const chapter = await dailyNotesApi.today()
      nav(`/notes?chapter=${chapter.id}`)
    },
  },
]

/**
 * Global command palette (Cmd/Ctrl+K), scoped to navigation for v1: jump
 * to any of the app's 12 pages or open today's daily note. Deliberately
 * doesn't include "create new X" actions -- those live inside each
 * page's own "+ New" modal state, and wiring the palette into that
 * would mean lifting create-modal state to a global store just for this,
 * which is a bigger change than a navigation launcher needs to justify.
 *
 * Distinct from GlobalSearch (the always-visible header search bar,
 * which finds *content* -- chapters, tasks, journal entries, notebooks):
 * this finds *destinations*. Its own overlay, own keyboard handling, no
 * shared state with GlobalSearch.
 */
export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return NAV_COMMANDS
    return NAV_COMMANDS.filter((c) => c.label.toLowerCase().includes(q))
  }, [query])

  useEffect(() => {
    function onGlobalKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setOpen((prev) => !prev)
      }
    }
    document.addEventListener('keydown', onGlobalKeyDown)
    return () => document.removeEventListener('keydown', onGlobalKeyDown)
  }, [])

  useEffect(() => {
    if (open) {
      setQuery('')
      setSelected(0)
      // Let the overlay mount before focusing.
      requestAnimationFrame(() => inputRef.current?.focus())
    }
  }, [open])

  useEffect(() => setSelected(0), [query])

  function runCommand(cmd: Command) {
    setOpen(false)
    cmd.run(navigate)
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Escape') {
      setOpen(false)
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelected((i) => Math.min(i + 1, filtered.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelected((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      const cmd = filtered[selected]
      if (cmd) runCommand(cmd)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 pt-[15vh]">
      <div className="absolute inset-0" onClick={() => setOpen(false)} />
      <div className="relative w-full max-w-lg overflow-hidden rounded-lg border border-neutral-800 bg-neutral-900 shadow-2xl">
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Type a command or search…"
          className="w-full border-b border-neutral-800 bg-transparent px-4 py-3 text-sm text-neutral-100 outline-none placeholder:text-neutral-600"
        />
        <ul className="max-h-80 overflow-y-auto py-1">
          {filtered.length === 0 && (
            <li className="px-4 py-3 text-sm text-neutral-600">No matching commands.</li>
          )}
          {filtered.map((cmd, i) => (
            <li key={cmd.id}>
              <button
                onClick={() => runCommand(cmd)}
                onMouseEnter={() => setSelected(i)}
                className={`w-full px-4 py-2 text-left text-sm ${
                  i === selected ? 'bg-neutral-800 text-white' : 'text-neutral-300'
                }`}
              >
                {cmd.label}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
