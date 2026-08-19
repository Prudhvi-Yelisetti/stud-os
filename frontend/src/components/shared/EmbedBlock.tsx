import { useQuery } from '@tanstack/react-query'
import { notebooksApi } from '../../lib/notebooks'
import { stripFrontmatter } from '../../lib/frontmatter'
import { ContentWithEmbeds } from './ContentWithEmbeds'
import type { ResolvedChapterLink } from '../../lib/useResolvedWikiLinks'

const MAX_EMBED_DEPTH = 3

/**
 * Renders one `![[Title]]` embed as an expanded, bordered block showing
 * the referenced note's actual content -- recurses through
 * ContentWithEmbeds so an embedded note can itself embed others, capped
 * at MAX_EMBED_DEPTH so a circular embed (A embeds B embeds A) can't
 * recurse forever; past the cap it falls back to a plain link instead
 * of expanding further.
 */
export function EmbedBlock({
  title,
  depth,
  onNavigate,
  onTagClick,
}: {
  title: string
  depth: number
  onNavigate: (resolved: ResolvedChapterLink) => void
  onTagClick?: (tag: string) => void
}) {
  const { data: matches, isLoading } = useQuery({
    queryKey: ['chapter-title-match', title],
    queryFn: () => notebooksApi.searchChapterTitles(title),
    staleTime: 10_000,
  })
  const match = matches?.find((m) => m.title.toLowerCase() === title.toLowerCase())

  const { data: chapter } = useQuery({
    queryKey: ['chapter', match?.id],
    queryFn: () => notebooksApi.getChapter(match!.id),
    enabled: !!match,
  })

  if (isLoading) {
    return <div className="my-2 rounded border border-neutral-800 bg-neutral-950 px-3 py-2 text-xs text-neutral-600">Loading embed…</div>
  }

  if (!match) {
    return (
      <div className="my-2 rounded border border-dashed border-neutral-700 px-3 py-2 text-sm text-neutral-500">
        ![[{title}]] — no note titled "{title}" yet.
      </div>
    )
  }

  if (depth >= MAX_EMBED_DEPTH) {
    return (
      <button
        onClick={() => onNavigate({ id: match.id, notebook_id: match.notebook_id })}
        className="my-2 block rounded border border-neutral-800 px-3 py-2 text-left text-sm text-emerald-400 hover:bg-neutral-900"
      >
        ↳ {title} (embed nesting too deep to expand further — click to open)
      </button>
    )
  }

  return (
    <div className="my-2 rounded border border-neutral-800 bg-neutral-950 px-3 py-2">
      <button
        onClick={() => onNavigate({ id: match.id, notebook_id: match.notebook_id })}
        className="mb-1 text-xs font-medium text-neutral-500 hover:text-emerald-400"
        title="Open this note"
      >
        {title}
      </button>
      {chapter ? (
        <ContentWithEmbeds
          content={stripFrontmatter(chapter.content)}
          depth={depth + 1}
          onNavigate={onNavigate}
          onTagClick={onTagClick}
          emptyPlaceholder="(empty note)"
        />
      ) : (
        <p className="text-xs text-neutral-600">Loading…</p>
      )}
    </div>
  )
}
