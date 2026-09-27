/**
 * Block references: `[[Note#^block-id]]` links to (or, as `![[...]]`,
 * embeds) one specific block of a note rather than the whole thing. A
 * block is marked by appending `^block-id` to the end of its last line
 * -- either on its own line or trailing the same line, both of which
 * Obsidian accepts and both of which BLOCK_ID_MARKER matches.
 *
 * Scope note: this resolves the *content* of a specific block (used for
 * embeds, where slicing to one block is the actual point) and strips the
 * `#^id` suffix before any title lookup (used for both links and
 * embeds, so `[[Note#^id]]` actually finds a chapter titled "Note"
 * instead of failing to match "Note#^id" verbatim). It deliberately does
 * NOT scroll a *link* click to the exact block once the target note
 * opens -- that would need mapping each raw-markdown paragraph to its
 * rendered DOM node, which is reliable for headings (always one <hN> per
 * heading line, see lib/outline.ts) but not for arbitrary block types
 * (list items, blockquote lines, table rows all render very differently
 * from their source), so a link just opens the target note like any
 * other wiki-link.
 */

const BLOCK_ID_MARKER = /\s\^([a-zA-Z0-9-]+)\s*$/

export function parseLinkTarget(raw: string): { title: string; blockId: string | null } {
  const idx = raw.indexOf('#^')
  if (idx === -1) return { title: raw, blockId: null }
  return { title: raw.slice(0, idx).trim(), blockId: raw.slice(idx + 2).trim() }
}

/** Returns the text of the block carrying `^blockId`, with the marker
 * itself stripped -- or null if no block in `content` carries it. */
export function getBlockText(content: string, blockId: string): string | null {
  const paragraphs = content.split(/\n{2,}/)
  for (const para of paragraphs) {
    const m = para.match(BLOCK_ID_MARKER)
    if (m && m[1] === blockId) {
      return para.slice(0, m.index).trim()
    }
  }
  return null
}
