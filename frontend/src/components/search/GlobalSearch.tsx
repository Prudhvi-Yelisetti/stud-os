import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { searchApi } from '../../lib/search'

const TYPE_ICON: Record<string, string> = {
  notebook: '📓',
  chapter: '📄',
  task: '✅',
  journal: '📔',
}

export function GlobalSearch() {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const { data: results } = useQuery({
    queryKey: ['search', query],
    queryFn: () => searchApi.query(query),
    enabled: query.trim().length >= 2,
  })

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  return (
    <div ref={containerRef} className="relative">
      <input
        value={query}
        onChange={(e) => {
          setQuery(e.target.value)
          setOpen(true)
        }}
        onFocus={() => setOpen(true)}
        placeholder="Search everything... (⌘K)"
        className="w-80 rounded bg-neutral-900 px-3 py-1.5 text-sm outline-none placeholder:text-neutral-600"
      />
      {open && query.trim().length >= 2 && (
        <div className="absolute top-full z-10 mt-1 w-80 rounded bg-neutral-900 shadow-lg">
          {results && results.length > 0 ? (
            results.map((r) => (
              <div
                key={`${r.type}-${r.id}`}
                className="border-b border-neutral-800 px-3 py-2 text-sm last:border-0 hover:bg-neutral-800"
              >
                <div className="flex items-center gap-2">
                  <span>{TYPE_ICON[r.type]}</span>
                  <span className="flex-1 truncate">{r.title}</span>
                  <span className="text-xs text-neutral-500">{r.type}</span>
                </div>
                {r.snippet && <p className="mt-0.5 truncate text-xs text-neutral-500">{r.snippet}</p>}
              </div>
            ))
          ) : (
            <div className="px-3 py-2 text-sm text-neutral-600">No results</div>
          )}
        </div>
      )}
    </div>
  )
}
