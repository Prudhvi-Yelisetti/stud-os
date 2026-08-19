import { forwardRef, useImperativeHandle, useMemo, useRef } from 'react'
import CodeMirror, { type ReactCodeMirrorRef } from '@uiw/react-codemirror'
import { markdown } from '@codemirror/lang-markdown'
import { EditorView, Decoration, type DecorationSet, ViewPlugin, type ViewUpdate } from '@codemirror/view'
import { RangeSetBuilder } from '@codemirror/state'

/**
 * A CodeMirror-based markdown editor with Obsidian-style "live preview":
 * formatting marks (**bold**, # headers, `code`) hide themselves on
 * every line except the one the cursor is currently on, so the document
 * reads close to its rendered form while still being plain editable
 * text underneath. Wiki-links, tags, and embed markers are styled as
 * colored pills (not hidden, nothing to reveal) with Ctrl/Cmd+click
 * navigation.
 *
 * Deliberately NOT in scope here (see HANDOFF.md for the reasoning):
 * expanding an embed's actual nested content while editing (shows as a
 * styled placeholder instead, fully expanded in Preview mode), and
 * hiding list/blockquote markers.
 */

const HEADER_PATTERN = /^(#{1,6})(\s+)(.*)$/
const BOLD_PATTERN = /(\*\*|__)([^*_\n]+)\1/g
const ITALIC_PATTERN = /(?<![*_])(\*|_)(?!\1)([^*_\n]+)\1(?!\1)/g
const INLINE_CODE_PATTERN = /`([^`\n]+)`/g
const WIKI_LINK_PATTERN = /(!)?\[\[([^[\]]+)\]\]/g
const TAG_PATTERN = /(?<!\w)#([A-Za-z][A-Za-z0-9_/-]*)/g

const HEADER_SIZE: Record<number, string> = {
  1: '1.5em',
  2: '1.3em',
  3: '1.15em',
  4: '1.05em',
  5: '1em',
  6: '1em',
}

function buildDecorations(view: EditorView): DecorationSet {
  const cursorLine = view.state.doc.lineAt(view.state.selection.main.head).number
  // Collected across the WHOLE document, not built incrementally per
  // line, then sorted once -- RangeSetBuilder requires strictly
  // increasing `from` (ties broken by `to`), and Decoration.line must be
  // a zero-width point at the line's start, not a range spanning it (an
  // earlier version got both of these wrong and crashed CodeMirror with
  // "Ranges must be added sorted by from position and startSide").
  const marks: { from: number; to: number; deco: Decoration }[] = []

  for (let lineNo = 1; lineNo <= view.state.doc.lines; lineNo++) {
    const line = view.state.doc.line(lineNo)
    const text = line.text
    const isActiveLine = lineNo === cursorLine

    // Headers: hide "# " prefix and enlarge the rest, unless this is the
    // line being edited (then show the raw "# Heading" text).
    const headerMatch = text.match(HEADER_PATTERN)
    if (headerMatch) {
      const level = headerMatch[1].length
      if (!isActiveLine) {
        const prefixEnd = line.from + headerMatch[1].length + headerMatch[2].length
        marks.push({ from: line.from, to: prefixEnd, deco: Decoration.replace({}) })
      }
      marks.push({
        from: line.from,
        to: line.from,
        deco: Decoration.line({ attributes: { style: `font-weight: 600; font-size: ${HEADER_SIZE[level]};` } }),
      })
    }

    // Bold, italic, inline code: hide the marker characters and style the
    // inner text, unless the cursor is on this line.
    for (const [pattern, className] of [
      [BOLD_PATTERN, 'cm-live-bold'],
      [ITALIC_PATTERN, 'cm-live-italic'],
      [INLINE_CODE_PATTERN, 'cm-live-code'],
    ] as const) {
      pattern.lastIndex = 0
      let m: RegExpExecArray | null
      while ((m = pattern.exec(text))) {
        const fullFrom = line.from + m.index
        const fullTo = fullFrom + m[0].length
        if (pattern === INLINE_CODE_PATTERN) {
          if (!isActiveLine) {
            marks.push({ from: fullFrom, to: fullFrom + 1, deco: Decoration.replace({}) })
            marks.push({ from: fullTo - 1, to: fullTo, deco: Decoration.replace({}) })
          }
          marks.push({ from: fullFrom + 1, to: fullTo - 1, deco: Decoration.mark({ class: className }) })
        } else {
          const markerLen = m[1].length
          if (!isActiveLine) {
            marks.push({ from: fullFrom, to: fullFrom + markerLen, deco: Decoration.replace({}) })
            marks.push({ from: fullTo - markerLen, to: fullTo, deco: Decoration.replace({}) })
          }
          marks.push({
            from: fullFrom + markerLen,
            to: fullTo - markerLen,
            deco: Decoration.mark({ class: className }),
          })
        }
      }
    }

    // Wiki-links, embeds, tags: always styled, never hidden -- there's no
    // "raw form" to reveal since nothing is hidden.
    WIKI_LINK_PATTERN.lastIndex = 0
    let wm: RegExpExecArray | null
    while ((wm = WIKI_LINK_PATTERN.exec(text))) {
      const isEmbed = !!wm[1]
      const from = line.from + wm.index
      const to = from + wm[0].length
      marks.push({
        from,
        to,
        deco: Decoration.mark({ class: isEmbed ? 'cm-live-embed' : 'cm-live-wikilink' }),
      })
    }
    TAG_PATTERN.lastIndex = 0
    let tm: RegExpExecArray | null
    while ((tm = TAG_PATTERN.exec(text))) {
      const from = line.from + tm.index
      const to = from + tm[0].length
      marks.push({ from, to, deco: Decoration.mark({ class: 'cm-live-tag' }) })
    }
  }

  // Ascending `from`, then ascending `to` -- puts each line's zero-width
  // Decoration.line point before any wider range starting at the same
  // position, and keeps every other decoration type in valid order too.
  marks.sort((a, b) => a.from - b.from || a.to - b.to)
  const builder = new RangeSetBuilder<Decoration>()
  for (const mark of marks) builder.add(mark.from, mark.to, mark.deco)
  return builder.finish()
}

function findLinkOrTagAt(view: EditorView, pos: number): { type: 'wikilink' | 'embed' | 'tag'; value: string } | null {
  const line = view.state.doc.lineAt(pos)
  const text = line.text
  const offset = pos - line.from

  WIKI_LINK_PATTERN.lastIndex = 0
  let wm: RegExpExecArray | null
  while ((wm = WIKI_LINK_PATTERN.exec(text))) {
    if (offset >= wm.index && offset <= wm.index + wm[0].length) {
      return { type: wm[1] ? 'embed' : 'wikilink', value: wm[2].trim() }
    }
  }
  TAG_PATTERN.lastIndex = 0
  let tm: RegExpExecArray | null
  while ((tm = TAG_PATTERN.exec(text))) {
    if (offset >= tm.index && offset <= tm.index + tm[0].length) {
      return { type: 'tag', value: tm[1].toLowerCase() }
    }
  }
  return null
}

const liveDecorations = ViewPlugin.fromClass(
  class {
    decorations: DecorationSet
    constructor(view: EditorView) {
      this.decorations = buildDecorations(view)
    }
    update(update: ViewUpdate) {
      if (update.docChanged || update.selectionSet || update.viewportChanged) {
        this.decorations = buildDecorations(update.view)
      }
    }
  },
  { decorations: (v) => v.decorations },
)

const liveTheme = EditorView.baseTheme({
  '.cm-live-bold': { fontWeight: '700' },
  '.cm-live-italic': { fontStyle: 'italic' },
  '.cm-live-code': {
    fontFamily: 'monospace',
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: '3px',
    padding: '0 3px',
  },
  '.cm-live-wikilink': { color: '#34d399', cursor: 'pointer' },
  '.cm-live-embed': { color: '#a78bfa', cursor: 'pointer' },
  '.cm-live-tag': {
    color: '#a5b4fc',
    backgroundColor: 'rgba(99,102,241,0.15)',
    borderRadius: '3px',
    padding: '0 2px',
  },
})

export interface LiveMarkdownEditorHandle {
  /** Inserts `text` at the current cursor, replacing [from, to) if given
   * (used to swap an in-progress "[[query" for "[[Title]]" on autocomplete
   * pick). Refocuses the editor afterward. */
  insertAtCursor: (text: string, from?: number, to?: number) => void
  focus: () => void
}

export const LiveMarkdownEditor = forwardRef<
  LiveMarkdownEditorHandle,
  {
    value: string
    onChange: (value: string, cursor: number) => void
    onBlur?: () => void
    placeholder?: string
    onWikiLinkClick?: (title: string) => void
    onEmbedClick?: (title: string) => void
    onTagClick?: (tag: string) => void
  }
>(function LiveMarkdownEditor({ value, onChange, onBlur, placeholder, onWikiLinkClick, onEmbedClick, onTagClick }, ref) {
  const cmRef = useRef<ReactCodeMirrorRef>(null)

  useImperativeHandle(ref, () => ({
    insertAtCursor(text, from, to) {
      const view = cmRef.current?.view
      if (!view) return
      const cursor = view.state.selection.main.head
      const insertFrom = from ?? cursor
      const insertTo = to ?? cursor
      view.dispatch({
        changes: { from: insertFrom, to: insertTo, insert: text },
        selection: { anchor: insertFrom + text.length },
      })
      view.focus()
    },
    focus() {
      cmRef.current?.view?.focus()
    },
  }))

  const clickHandler = useMemo(
    () =>
      EditorView.domEventHandlers({
        click: (event, view) => {
          if (!event.ctrlKey && !event.metaKey) return false
          const pos = view.posAtCoords({ x: event.clientX, y: event.clientY })
          if (pos == null) return false
          const hit = findLinkOrTagAt(view, pos)
          if (!hit) return false
          event.preventDefault()
          if (hit.type === 'wikilink') onWikiLinkClick?.(hit.value)
          else if (hit.type === 'embed') onEmbedClick?.(hit.value)
          else onTagClick?.(hit.value)
          return true
        },
      }),
    [onWikiLinkClick, onEmbedClick, onTagClick],
  )

  const extensions = useMemo(
    () => [markdown(), liveDecorations, liveTheme, clickHandler, EditorView.lineWrapping],
    [clickHandler],
  )

  return (
    <CodeMirror
      ref={cmRef}
      value={value}
      onChange={(v, viewUpdate) => onChange(v, viewUpdate.state.selection.main.head)}
      onBlur={onBlur}
      placeholder={placeholder}
      theme="dark"
      height="100%"
      extensions={extensions}
      basicSetup={{ lineNumbers: false, foldGutter: false, highlightActiveLine: false }}
      style={{ height: '100%', fontSize: '0.875rem' }}
    />
  )
})
