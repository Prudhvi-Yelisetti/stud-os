import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { searchApi } from '../../lib/search'
import { useDebouncedValue } from '../../lib/useDebouncedValue'
import type { SearchResult, SemanticSearchResult } from '../../lib/api'

const TYPE_ICON: Record<string, string> = {
  notebook: '📓',
  chapter: '📄',
  task: '✅',
  journal: '📔',
}

type Mode = 'keyword' | 'semantic'

export function GlobalSearch() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState<Mode>('keyword')
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const debouncedQuery = useDebouncedValue(query, 300)

  const { data: keywordResults } = useQuery({
    queryKey: ['search', debouncedQuery],
    queryFn: () => searchApi.query(debouncedQuery),
    enabled: mode === 'keyword' && debouncedQuery.trim().length >= 2,
  })

  const { data: semanticResults } = useQuery({
    queryKey: ['search-semantic', debouncedQuery],
    queryFn: () => searchApi.semantic(debouncedQuery),
    enabled: mode === 'semantic' && debouncedQuery.trim().length >= 2,
  })

  const results: (SearchResult | SemanticSearchResult)[] | undefined =
    mode === 'keyword' ? keywordResults : semanticResults

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  function goToResult(r: SearchResult | SemanticSearchResult) {
    setOpen(false)
    setQuery('')
    if (r.type === 'chapter') navigate(`/notes?chapter=${r.id}`)
    else if (r.type === 'notebook') navigate(`/notes?notebook=${r.id}`)
    else if (r.type === 'task') navigate('/tasks')
    else if (r.type === 'journal') navigate('/journal')
  }

  return (
    <div ref={containerRef} className="relative">
      <input
        value={query}
        onChange={(e) => {
          setQuery(e.target.value)
          setOpen(true)
        }}
        onFocus={() => setOpen(true)}
        placeholder="Search everything..."
        title="Operators: tag:x, -tag:x, notebook:x, -notebook:x, -word"
        className="w-80 rounded bg-neutral-900 px-3 py-1.5 text-sm outline-none placeholder:text-neutral-600"
      />
      {open && debouncedQuery.trim().length >= 2 && (
        <div className="absolute top-full z-10 mt-1 w-80 rounded bg-neutral-900 shadow-lg">
          <div className="flex border-b border-neutral-800 text-xs">
            <button
              onClick={() => setMode('keyword')}
              className={`flex-1 px-3 py-1.5 ${mode === 'keyword' ? 'text-neutral-100' : 'text-neutral-600 hover:text-neutral-400'}`}
            >
              Keyword
            </button>
            <button
              onClick={() => setMode('semantic')}
              className={`flex-1 px-3 py-1.5 ${mode === 'semantic' ? 'text-neutral-100' : 'text-neutral-600 hover:text-neutral-400'}`}
              title="Meaning-based search over notes and journal content"
            >
              Semantic
            </button>
          </div>
          {results && results.length > 0 ? (
            results.map((r) => (
              <button
                key={`${r.type}-${r.id}`}
                onClick={() => goToResult(r)}
                className="block w-full border-b border-neutral-800 px-3 py-2 text-left text-sm last:border-0 hover:bg-neutral-800"
              >
                <div className="flex items-center gap-2">
                  <span>{TYPE_ICON[r.type]}</span>
                  <span className="flex-1 truncate">{r.title}</span>
                  <span className="text-xs text-neutral-500">{r.type}</span>
                </div>
                {r.snippet && <p className="mt-0.5 truncate text-xs text-neutral-500">{r.snippet}</p>}
              </button>
            ))
          ) : (
            <div className="px-3 py-2 text-sm text-neutral-600">
              {mode === 'semantic' ? 'No conceptually related content' : 'No results'}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
