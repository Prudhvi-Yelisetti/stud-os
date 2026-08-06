import { useMemo } from 'react'
import { marked } from 'marked'

/**
 * Renders markdown for AI-generated text (task suggestions, ask-your-notes
 * answers, quiz explanations). Models routinely reply with lists/bold/code
 * even when asked for plain prose, and without this it shows up as literal
 * "- " and "**" characters in the chat bubble instead of formatting.
 *
 * Deliberately simpler than WikiLinkText: AI replies don't contain
 * [[wiki-links]], so there's no resolution map or click-interception to
 * wire up here, just `marked`. Same no-sanitizer reasoning as WikiLinkText
 * applies (single-user local app, own content only) -- revisit if this
 * app ever renders another person's content.
 */
export function MarkdownText({ content, className = '' }: { content: string; className?: string }) {
  const html = useMemo(() => {
    if (!content.trim()) return ''
    return marked.parse(content, { breaks: true, async: false }) as string
  }, [content])

  if (!content.trim()) return null

  return (
    <div
      className={`prose prose-invert prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-ol:my-1 ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
