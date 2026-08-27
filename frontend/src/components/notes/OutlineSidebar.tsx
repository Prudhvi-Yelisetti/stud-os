import { extractOutline } from '../../lib/outline'

/**
 * Heading TOC for the current note's preview pane. Clicking an entry
 * scrolls the preview container to that heading's real DOM id (assigned
 * by lib/outline.ts's annotateHeadingIds, via WikiLinkText) -- a plain
 * scrollIntoView rather than a router navigation, so it doesn't touch the
 * URL or history.
 *
 * Only meaningful in Preview mode: Edit mode's CodeMirror content isn't
 * this component's rendered HTML, so there's nothing here to scroll to.
 * ChapterEditor only renders this when mode === 'preview'.
 */
export function OutlineSidebar({
  content,
  scrollContainerRef,
}: {
  content: string
  scrollContainerRef: React.RefObject<HTMLElement | null>
}) {
  const headings = extractOutline(content)

  if (headings.length === 0) return null

  function handleClick(id: string) {
    const container = scrollContainerRef.current
    if (!container) return
    const target = container.querySelector(`#${CSS.escape(id)}`)
    target?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const minLevel = Math.min(...headings.map((h) => h.level))

  return (
    <div className="mb-4 border-b border-neutral-800 pb-3">
      <h2 className="mb-2 text-sm font-medium text-neutral-400">Outline</h2>
      <ul className="flex flex-col gap-0.5">
        {headings.map((h, i) => (
          <li key={`${h.id}-${i}`} style={{ paddingLeft: `${(h.level - minLevel) * 0.75}rem` }}>
            <button
              onClick={() => handleClick(h.id)}
              className="w-full truncate rounded px-1 py-0.5 text-left text-xs text-neutral-400 hover:bg-neutral-900 hover:text-neutral-200"
              title={h.text}
            >
              {h.text}
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
