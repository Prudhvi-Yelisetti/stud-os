/**
 * Strips a leading YAML frontmatter block (---\n...\n---) so markdown
 * preview only renders the body -- properties are already surfaced via
 * PropertiesPanel, and without this `marked` misparses the block's own
 * "---" lines as a setext heading separator. Mirrors
 * backend/utils/frontmatter.py's FRONTMATTER_PATTERN; this is a display
 * concern only, not a second source of truth -- raw edit mode still
 * shows the full content, frontmatter included.
 */
const FRONTMATTER_PATTERN = /^---[ \t]*\r?\n[\s\S]*?\r?\n---[ \t]*(?:\r?\n)*/

export function stripFrontmatter(content: string): string {
  return content.replace(FRONTMATTER_PATTERN, '')
}
