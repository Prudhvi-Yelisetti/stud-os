/**
 * Client-side mirror of backend/utils/wiki_parser.py -- used for rendering
 * and autocomplete, not as the source of truth (the backend re-derives
 * links from content on every save regardless of what the client sends).
 */
const WIKI_LINK_PATTERN = /\[\[([^[\]]+)\]\]/g

export interface WikiLinkPart {
  type: 'text' | 'link'
  content: string
}

export function splitByWikiLinks(content: string): WikiLinkPart[] {
  const parts: WikiLinkPart[] = []
  let lastIndex = 0
  for (const match of content.matchAll(WIKI_LINK_PATTERN)) {
    const index = match.index ?? 0
    if (index > lastIndex) parts.push({ type: 'text', content: content.slice(lastIndex, index) })
    parts.push({ type: 'link', content: match[1].trim() })
    lastIndex = index + match[0].length
  }
  if (lastIndex < content.length) parts.push({ type: 'text', content: content.slice(lastIndex) })
  return parts
}

export function extractWikiLinkTitles(content: string): string[] {
  const seen = new Set<string>()
  for (const part of splitByWikiLinks(content)) {
    if (part.type === 'link') seen.add(part.content)
  }
  return Array.from(seen)
}

/**
 * Detects an in-progress "[[query" at the cursor (no closing "]]" yet).
 * Returns the query text and the index where "[[" starts, or null.
 */
export function detectActiveWikiLinkQuery(
  textBeforeCursor: string,
): { query: string; startIndex: number } | null {
  const match = textBeforeCursor.match(/\[\[([^[\]]*)$/)
  if (!match) return null
  return { query: match[1], startIndex: match.index ?? 0 }
}
