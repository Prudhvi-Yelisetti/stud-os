import { useEffect, useMemo, useRef } from 'react'
import { marked } from 'marked'
import type { ResolvedChapterLink } from '../../lib/useResolvedWikiLinks'

const WIKI_LINK_PATTERN = /\[\[([^\[\]]+)\]\]/g

/**
 * Renders full markdown (headers, bold/italic, code, lists, etc. via
 * `marked`) with [[wiki-links]] treated specially: resolved links (a real
 * chapter exists) are clickable, unresolved ones render distinctly and
 * only become clickable if the caller provides onUnresolvedClick (Notes
 * can create the chapter in-context; Journal has no notebook to create
 * into, so it leaves them inert with a title tooltip explaining why).
 *
 * This is a single-user local app -- there's no other person's content
 * ever rendered here, so dangerouslySetInnerHTML carries no real XSS
 * boundary to defend (you'd only ever be injecting into your own session).
 * Skipping a sanitizer (e.g. DOMPurify) is a deliberate, scoped tradeoff,
 * not an oversight -- revisit if this app ever gains multi-user content.
 */
export function WikiLinkText({
  content,
  resolvedLinks,
  onResolvedClick,
  onUnresolvedClick,
  emptyPlaceholder,
}: {
  content: string
  resolvedLinks: Map<string, ResolvedChapterLink | null>
  onResolvedClick: (resolved: ResolvedChapterLink) => void
  onUnresolvedClick?: (title: string) => void
  emptyPlaceholder?: string
}) {
  const containerRef = useRef<HTMLDivElement>(null)

  const html = useMemo(() => {
    if (content.trim() === '') return ''
    // Swap [[Title]] for a placeholder markdown link so `marked` renders a
    // normal <a> for it (getting all its escaping for free), encoding
    // resolution status into the URL scheme so we can style + intercept
    // clicks after render without re-parsing the markdown ourselves.
    const withPlaceholders = content.replace(WIKI_LINK_PATTERN, (_match, rawTitle) => {
      const title = rawTitle.trim()
      const scheme = resolvedLinks.get(title) ? 'wikilink-resolved' : 'wikilink-unresolved'
      return `[${title}](${scheme}:${encodeURIComponent(title)})`
    })
    return marked.parse(withPlaceholders, { breaks: true, async: false }) as string
  }, [content, resolvedLinks])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    function handleClick(e: MouseEvent) {
      const target = (e.target as HTMLElement).closest('a')
      if (!target) return
      const href = target.getAttribute('href') ?? ''
      const isResolved = href.startsWith('wikilink-resolved:')
      const isUnresolved = href.startsWith('wikilink-unresolved:')
      if (!isResolved && !isUnresolved) return

      e.preventDefault()
      const title = decodeURIComponent(href.split(':').slice(1).join(':'))
      if (isResolved) {
        const resolved = resolvedLinks.get(title)
        if (resolved) onResolvedClick(resolved)
      } else {
        onUnresolvedClick?.(title)
      }
    }

    container.addEventListener('click', handleClick)
    return () => container.removeEventListener('click', handleClick)
  }, [resolvedLinks, onResolvedClick, onUnresolvedClick])

  if (content.trim() === '' && emptyPlaceholder) {
    return <span className="text-neutral-600">{emptyPlaceholder}</span>
  }

  return (
    <div
      ref={containerRef}
      className="prose prose-invert prose-sm max-w-none prose-a:no-underline
        [&_a[href^='wikilink-resolved']]:text-emerald-400 [&_a[href^='wikilink-resolved']]:underline [&_a[href^='wikilink-resolved']]:decoration-emerald-700 [&_a[href^='wikilink-resolved']]:cursor-pointer
        [&_a[href^='wikilink-unresolved']]:text-neutral-500 [&_a[href^='wikilink-unresolved']]:underline [&_a[href^='wikilink-unresolved']]:decoration-dashed [&_a[href^='wikilink-unresolved']]:decoration-neutral-600"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
