import { splitByWikiLinks } from '../../lib/wikiLinks'
import type { ResolvedChapterLink } from '../../lib/useResolvedWikiLinks'

/**
 * Renders text with [[wiki-links]] highlighted. Resolved links (a real
 * chapter exists) are clickable; unresolved links render distinctly but
 * only become clickable if the caller provides onUnresolvedClick (Notes
 * can create the chapter in-context; Journal has no notebook to create
 * into, so it leaves them inert with a title tooltip explaining why).
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
  if (content.trim() === '' && emptyPlaceholder) {
    return <span className="text-neutral-600">{emptyPlaceholder}</span>
  }

  return (
    <>
      {splitByWikiLinks(content).map((part, i) => {
        if (part.type === 'text') return <span key={i}>{part.content}</span>

        const resolved = resolvedLinks.get(part.content)
        if (resolved) {
          return (
            <button
              key={i}
              onClick={() => onResolvedClick(resolved)}
              className="text-emerald-400 underline decoration-emerald-700 hover:text-emerald-300"
              title="Go to chapter"
            >
              {part.content}
            </button>
          )
        }

        if (onUnresolvedClick) {
          return (
            <button
              key={i}
              onClick={() => onUnresolvedClick(part.content)}
              className="text-neutral-500 underline decoration-dashed decoration-neutral-600 hover:text-neutral-300"
              title="Create this chapter"
            >
              {part.content}
            </button>
          )
        }

        return (
          <span
            key={i}
            className="text-neutral-500 underline decoration-dashed decoration-neutral-700"
            title="No chapter with this title yet"
          >
            {part.content}
          </span>
        )
      })}
    </>
  )
}
