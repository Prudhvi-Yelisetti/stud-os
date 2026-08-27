/**
 * Outline / heading TOC support.
 *
 * extractOutline() walks the raw markdown source (used by OutlineSidebar to
 * build the clickable list) and annotateHeadingIds() walks marked's
 * rendered HTML (used by WikiLinkText to give each <hN> a real id to jump
 * to). Both need to agree on the exact same id for the same heading, so
 * they share slugify() -- and extractOutline additionally strips inline
 * markdown syntax (**bold**, [[links]], etc.) from the heading text before
 * slugifying, since annotateHeadingIds is working from already-rendered
 * HTML where that syntax has already become tags stripped down to plain
 * text.
 */

export interface OutlineHeading {
  level: number
  text: string
  id: string
}

function slugify(text: string, seen: Map<string, number>): string {
  const base =
    text
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, '')
      .replace(/\s+/g, '-') || 'section'
  const count = seen.get(base) ?? 0
  seen.set(base, count + 1)
  return count === 0 ? base : `${base}-${count}`
}

function stripInlineMarkdown(text: string): string {
  return text
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/__([^_]+)__/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/_([^_]+)_/g, '$1')
    .replace(/!?\[\[([^\]|]+)(\|[^\]]+)?\]\]/g, (_m, t) => t)
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .trim()
}

const HEADING_LINE = /^(#{1,6})\s+(.+?)\s*#*$/

export function extractOutline(content: string): OutlineHeading[] {
  // Strip fenced code blocks first so a "# comment" inside a code sample
  // doesn't show up as a heading.
  const withoutCode = content.replace(/```[\s\S]*?```/g, '')
  const seen = new Map<string, number>()
  const headings: OutlineHeading[] = []
  for (const line of withoutCode.split('\n')) {
    const m = line.match(HEADING_LINE)
    if (!m) continue
    const level = m[1].length
    const text = stripInlineMarkdown(m[2])
    if (!text) continue
    headings.push({ level, text, id: slugify(text, seen) })
  }
  return headings
}

const HEADING_TAG = /<h([1-6])>([\s\S]*?)<\/h\1>/g

export function annotateHeadingIds(html: string): string {
  const seen = new Map<string, number>()
  return html.replace(HEADING_TAG, (_full, level: string, inner: string) => {
    const text = inner.replace(/<[^>]+>/g, '')
    if (!text.trim()) return _full
    const id = slugify(text, seen)
    return `<h${level} id="${id}">${inner}</h${level}>`
  })
}
