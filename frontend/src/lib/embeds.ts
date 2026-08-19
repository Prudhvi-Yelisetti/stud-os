/**
 * Splits content on `![[Title]]` embed/transclusion syntax so a caller
 * can render embed segments as expanded note content and everything
 * else as normal markdown -- WikiLinkText must never see raw `![[...]]`
 * text, since its `[[Title]]` handling would otherwise treat the `[[`
 * part as a plain link and `marked` would render the leading `!` as a
 * broken image tag.
 */
const EMBED_PATTERN = /!\[\[([^[\]]+)\]\]/g

export interface EmbedPart {
  type: 'text' | 'embed'
  content: string
}

export function splitByEmbeds(content: string): EmbedPart[] {
  const parts: EmbedPart[] = []
  let lastIndex = 0
  for (const match of content.matchAll(EMBED_PATTERN)) {
    const index = match.index ?? 0
    if (index > lastIndex) parts.push({ type: 'text', content: content.slice(lastIndex, index) })
    parts.push({ type: 'embed', content: match[1].trim() })
    lastIndex = index + match[0].length
  }
  if (lastIndex < content.length) parts.push({ type: 'text', content: content.slice(lastIndex) })
  return parts
}
