/**
 * Footnote support ([^id] inline refs + [^id]: definitions), since marked
 * core doesn't implement the GFM footnote extension. Implemented as a
 * two-pass text transform rather than a marked block extension: definitions
 * can appear anywhere in the source (conventionally at the bottom) but must
 * render as one ordered list at the very end, in first-reference order --
 * easier to get right with plain string manipulation than by fighting
 * marked's single-pass token stream for something that needs a global
 * reorder.
 *
 * Pass 1 (preprocessFootnotes, runs on raw markdown before wiki-link/tag
 * substitution and marked.parse): strips `[^id]: text` definitions out of
 * the body, renumbers every `[^id]` reference in first-occurrence order,
 * rewrites each as a placeholder link (`[n](footnote:id)`), and appends a
 * rendered footnotes section using matching `[n](footnoteback:id)`
 * backlinks -- reuses the existing placeholder-link trick so wiki-links and
 * tags *inside* a footnote definition still resolve normally when the
 * combined string later goes through WikiLinkText's own substitution.
 *
 * Pass 2 (annotateFootnoteAnchors, runs on marked's rendered HTML): turns
 * the placeholder anchors into real `id`/`href` pairs (`#fn-N` / `#fnref-N`)
 * so clicking a reference is a plain in-page anchor jump -- no JS click
 * handler needed, the browser's native fragment navigation already works
 * inside the scrollable preview container.
 */

const FOOTNOTE_DEF = /^\[\^([^\]\s]+)\]:[ \t]?(.*(?:\n(?:[ \t]{2,}\S.*)?)*)/gm
const FOOTNOTE_REF = /\[\^([^\]\s]+)\]/g

export function preprocessFootnotes(content: string): string {
  const defs = new Map<string, string>()
  const body = content.replace(FOOTNOTE_DEF, (_m, id: string, text: string) => {
    defs.set(id, text.trim().replace(/\n[ \t]+/g, ' '))
    return ''
  })

  if (defs.size === 0) return content

  const refOrder: string[] = []
  const withRefs = body.replace(FOOTNOTE_REF, (full, id: string) => {
    if (!defs.has(id)) return full // not a real footnote -- leave literal text alone
    if (!refOrder.includes(id)) refOrder.push(id)
    const num = refOrder.indexOf(id) + 1
    return `[${num}](footnote:${encodeURIComponent(id)})`
  })

  if (refOrder.length === 0) return withRefs.trimEnd()

  const list = refOrder
    .map((id, i) => `${i + 1}. ${defs.get(id)} [\u21a9](footnoteback:${encodeURIComponent(id)})`)
    .join('\n')

  return `${withRefs.trimEnd()}\n\n---\n\n${list}\n`
}

const REF_HTML = /<a href="footnote:[^"]*">(\d+)<\/a>/g
const DEF_LI_HTML = /<li>([\s\S]*?)<a href="footnoteback:[^"]*">[^<]*<\/a><\/li>/g

export function annotateFootnoteAnchors(html: string): string {
  html = html.replace(REF_HTML, (_m, num: string) => {
    return `<sup><a href="#fn-${num}" id="fnref-${num}" class="footnote-ref">${num}</a></sup>`
  })
  let i = 0
  html = html.replace(DEF_LI_HTML, (_m, inner: string) => {
    i += 1
    return `<li id="fn-${i}">${inner}<a href="#fnref-${i}" class="footnote-backref">\u21a9</a></li>`
  })
  return html
}
