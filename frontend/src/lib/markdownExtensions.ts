import { marked, type Tokens, type TokenizerAndRendererExtension } from 'marked'

/**
 * Registers a marked block extension for Obsidian-style callouts:
 *
 *   > [!note] Optional Title
 *   > Body line one
 *   > Body line two
 *
 * Recognized types get a label + color class; unknown types fall back to
 * a generic style with the raw type capitalized as the label, so a typo'd
 * or novel type still renders as *something* rather than silently
 * degrading to a plain blockquote.
 *
 * Foldable callouts use Obsidian's `[!type]+` (default open) / `[!type]-`
 * (default closed) suffix, rendered as <details>/<summary>. No suffix is
 * a plain, always-visible <div> -- matches Obsidian's own default.
 *
 * This module has a side effect on import (marked.use(...)) -- import it
 * once, anywhere before the first marked.parse() call that might contain
 * a callout. WikiLinkText imports it for this reason.
 */

const CALLOUT_TYPES: Record<string, { label: string; className: string }> = {
  note: { label: 'Note', className: 'callout-note' },
  info: { label: 'Info', className: 'callout-info' },
  tip: { label: 'Tip', className: 'callout-tip' },
  hint: { label: 'Tip', className: 'callout-tip' },
  important: { label: 'Important', className: 'callout-important' },
  warning: { label: 'Warning', className: 'callout-warning' },
  caution: { label: 'Warning', className: 'callout-warning' },
  danger: { label: 'Danger', className: 'callout-danger' },
  error: { label: 'Error', className: 'callout-danger' },
  bug: { label: 'Bug', className: 'callout-danger' },
  success: { label: 'Success', className: 'callout-success' },
  check: { label: 'Success', className: 'callout-success' },
  done: { label: 'Success', className: 'callout-success' },
  question: { label: 'Question', className: 'callout-question' },
  faq: { label: 'FAQ', className: 'callout-question' },
  help: { label: 'Help', className: 'callout-question' },
  quote: { label: 'Quote', className: 'callout-quote' },
  cite: { label: 'Quote', className: 'callout-quote' },
  example: { label: 'Example', className: 'callout-example' },
  todo: { label: 'To-do', className: 'callout-todo' },
  abstract: { label: 'Summary', className: 'callout-info' },
  summary: { label: 'Summary', className: 'callout-info' },
  tldr: { label: 'TL;DR', className: 'callout-info' },
}

const CALLOUT_HEADER = /^ {0,3}> ?\[!(\w+)\]([+-]?)([^\n]*)\n?/

interface CalloutToken extends Tokens.Generic {
  type: 'callout'
  calloutType: string
  className: string
  fold: string
  title: string
  tokens: Tokens.Generic[]
}

const calloutExtension: TokenizerAndRendererExtension = {
  name: 'callout',
  level: 'block',
  start(src: string) {
    const m = src.match(/^ {0,3}> ?\[!\w+\]/m)
    return m?.index
  },
  tokenizer(src: string) {
    const headerMatch = src.match(CALLOUT_HEADER)
    if (!headerMatch || headerMatch.index !== 0) return undefined

    const [full, rawType, fold, rawTitle] = headerMatch
    let rest = src.slice(full.length)
    const bodyLines: string[] = []
    const lineRe = /^ {0,3}>( ?)([^\n]*)\n?/
    for (;;) {
      const lm = rest.match(lineRe)
      if (!lm || lm.index !== 0) break
      bodyLines.push(lm[2])
      rest = rest.slice(lm[0].length)
    }

    const raw = full + bodyLines.map((l) => `> ${l}`).join('\n')
    const bodyText = bodyLines.join('\n').trim()
    const type = rawType.toLowerCase()
    const meta = CALLOUT_TYPES[type] ?? {
      label: rawType.charAt(0).toUpperCase() + rawType.slice(1),
      className: 'callout-default',
    }
    const title = rawTitle.trim() || meta.label

    const token: CalloutToken = {
      type: 'callout',
      raw,
      calloutType: type,
      className: meta.className,
      fold,
      title,
      tokens: [],
    }
    token.tokens = this.lexer.blockTokens(bodyText, [])
    return token
  },
  renderer(token) {
    const t = token as CalloutToken
    const inner = this.parser.parse(t.tokens)
    if (t.fold) {
      const openAttr = t.fold === '+' ? ' open' : ''
      return `<details class="callout ${t.className}"${openAttr}><summary class="callout-title">${t.title}</summary><div class="callout-body">${inner}</div></details>\n`
    }
    return `<div class="callout ${t.className}"><div class="callout-title">${t.title}</div><div class="callout-body">${inner}</div></div>\n`
  },
}

marked.use({ extensions: [calloutExtension] })
