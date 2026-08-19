import { splitByEmbeds } from '../../lib/embeds'
import { useResolvedWikiLinks, type ResolvedChapterLink } from '../../lib/useResolvedWikiLinks'
import { WikiLinkText } from './WikiLinkText'
import { EmbedBlock } from './EmbedBlock'

/**
 * Top-level entry point for rendering note/journal content read-only:
 * splits out `![[Title]]` embeds and expands them via EmbedBlock,
 * rendering everything else through WikiLinkText as before. Replaces
 * direct WikiLinkText usage everywhere content is displayed (not
 * edited) so embeds actually transclude instead of rendering as a
 * broken image tag (marked reads `![[X]]` as image syntax otherwise).
 */
export function ContentWithEmbeds({
  content,
  resolvedLinks,
  onNavigate,
  onUnresolvedClick,
  onTagClick,
  emptyPlaceholder,
  depth = 0,
}: {
  content: string
  /** Precomputed resolution map -- pass this from a top-level caller that
   * already has one (avoids a redundant resolve). Omit it and this
   * component resolves its own content's links instead -- used when
   * EmbedBlock recurses into an embedded note's content. */
  resolvedLinks?: Map<string, ResolvedChapterLink | null>
  onNavigate: (resolved: ResolvedChapterLink) => void
  onUnresolvedClick?: (title: string) => void
  onTagClick?: (tag: string) => void
  emptyPlaceholder?: string
  depth?: number
}) {
  const selfResolved = useResolvedWikiLinks(content, resolvedLinks === undefined)
  const links = resolvedLinks ?? selfResolved

  if (content.trim() === '' && emptyPlaceholder) {
    return <span className="text-neutral-600">{emptyPlaceholder}</span>
  }

  const parts = splitByEmbeds(content)

  return (
    <>
      {parts.map((part, i) =>
        part.type === 'embed' ? (
          <EmbedBlock key={i} title={part.content} depth={depth} onNavigate={onNavigate} onTagClick={onTagClick} />
        ) : (
          <WikiLinkText
            key={i}
            content={part.content}
            resolvedLinks={links}
            onResolvedClick={onNavigate}
            onUnresolvedClick={onUnresolvedClick}
            onTagClick={onTagClick}
          />
        ),
      )}
    </>
  )
}
