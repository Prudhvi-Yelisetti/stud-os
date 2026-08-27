import { useEffect, useMemo, useRef } from 'react'
import { marked } from 'marked'
import '../../lib/markdownExtensions' // side effect: registers callout block extension
import { preprocessFootnotes, annotateFootnoteAnchors } from '../../lib/footnotes'
import { annotateHeadingIds } from '../../lib/outline'
import type { ResolvedChapterLink } from '../../lib/useResolvedWikiLinks'

const WIKI_LINK_PATTERN = /\[\[([^\[\]]+)\]\]/g
// Mirrors backend/utils/tags.py's TAG_PATTERN -- a tag starts with a
// letter (so markdown headers, "# Heading", never match, since those are
// always "#" followed by a space) and allows nesting with "/".
const TAG_PATTERN = /(?<!\w)#([A-Za-z][A-Za-z0-9_/-]*)/g

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
  onTagClick,
  emptyPlaceholder,
}: {
  content: string
  resolvedLinks: Map<string, ResolvedChapterLink | null>
  onResolvedClick: (resolved: ResolvedChapterLink) => void
  onUnresolvedClick?: (title: string) => void
  onTagClick?: (tag: string) => void
  emptyPlaceholder?: string
}) {
  const containerRef = useRef<HTMLDivElement>(null)

  const html = useMemo(() => {
    if (content.trim() === '') return ''
    // Footnotes first -- extracts [^id]: definitions and appends a
    // rendered footnotes list, so wiki-links/tags inside a footnote's own
    // text still get substituted normally by the two passes below.
    let withPlaceholders = preprocessFootnotes(content)
    // Swap [[Title]] for a placeholder markdown link so `marked` renders a
    // normal <a> for it (getting all its escaping for free), encoding
    // resolution status into the URL scheme so we can style + intercept
    // clicks after render without re-parsing the markdown ourselves.
    withPlaceholders = withPlaceholders.replace(WIKI_LINK_PATTERN, (_match, rawTitle) => {
      const title = rawTitle.trim()
      const scheme = resolvedLinks.get(title) ? 'wikilink-resolved' : 'wikilink-unresolved'
      return `[${title}](${scheme}:${encodeURIComponent(title)})`
    })
    // Same trick for #tags -- always "resolvable" (a tag page exists for
    // any tag name), so they always render clickable when onTagClick is
    // provided, or as inert-but-styled pills otherwise.
    withPlaceholders = withPlaceholders.replace(TAG_PATTERN, (_match, name: string) => {
      return `[#${name}](tag:${encodeURIComponent(name.toLowerCase())})`
    })
    const rendered = marked.parse(withPlaceholders, { breaks: true, async: false }) as string
    return annotateHeadingIds(annotateFootnoteAnchors(rendered))
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
      const isTag = href.startsWith('tag:')
      if (!isResolved && !isUnresolved && !isTag) return

      e.preventDefault()
      const value = decodeURIComponent(href.split(':').slice(1).join(':'))
      if (isResolved) {
        const resolved = resolvedLinks.get(value)
        if (resolved) onResolvedClick(resolved)
      } else if (isUnresolved) {
        onUnresolvedClick?.(value)
      } else if (isTag) {
        onTagClick?.(value)
      }
    }

    container.addEventListener('click', handleClick)
    return () => container.removeEventListener('click', handleClick)
  }, [resolvedLinks, onResolvedClick, onUnresolvedClick, onTagClick])

  if (content.trim() === '' && emptyPlaceholder) {
    return <span className="text-neutral-600">{emptyPlaceholder}</span>
  }

  return (
    <div
      ref={containerRef}
      className="prose prose-invert prose-sm max-w-none prose-a:no-underline
        [&_a[href^='wikilink-resolved']]:text-emerald-400 [&_a[href^='wikilink-resolved']]:underline [&_a[href^='wikilink-resolved']]:decoration-emerald-700 [&_a[href^='wikilink-resolved']]:cursor-pointer
        [&_a[href^='wikilink-unresolved']]:text-neutral-500 [&_a[href^='wikilink-unresolved']]:underline [&_a[href^='wikilink-unresolved']]:decoration-dashed [&_a[href^='wikilink-unresolved']]:decoration-neutral-600
        [&_a[href^='tag']]:rounded [&_a[href^='tag']]:bg-indigo-950 [&_a[href^='tag']]:px-1.5 [&_a[href^='tag']]:py-0.5 [&_a[href^='tag']]:text-indigo-300 [&_a[href^='tag']]:no-underline [&_a[href^='tag']]:cursor-pointer"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
