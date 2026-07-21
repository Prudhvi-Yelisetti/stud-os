import { useMemo } from 'react'
import { useQueries } from '@tanstack/react-query'
import { notebooksApi } from './notebooks'
import { extractWikiLinkTitles } from './wikiLinks'

export interface ResolvedChapterLink {
  id: string
  notebook_id: string
}

/**
 * Resolves every [[Title]] found in `content` to a real chapter (or null
 * if none exists yet). Shared between Notes and Journal so both render
 * wiki-links the same way instead of Journal treating them as plain text.
 */
export function useResolvedWikiLinks(content: string, enabled: boolean) {
  const linkTitles = useMemo(() => extractWikiLinkTitles(content), [content])

  const titleQueries = useQueries({
    queries: linkTitles.map((title) => ({
      queryKey: ['chapter-title-match', title],
      queryFn: () => notebooksApi.searchChapterTitles(title),
      enabled,
      staleTime: 10_000,
    })),
  })

  return useMemo(() => {
    const map = new Map<string, ResolvedChapterLink | null>()
    linkTitles.forEach((title, i) => {
      const matches = titleQueries[i]?.data
      const exact = matches?.find((m) => m.title.toLowerCase() === title.toLowerCase())
      map.set(title, exact ? { id: exact.id, notebook_id: exact.notebook_id } : null)
    })
    return map
  }, [linkTitles, titleQueries])
}
