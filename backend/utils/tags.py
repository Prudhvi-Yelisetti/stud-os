"""
Extracts tags from chapter/journal content, combining two sources the
same way Obsidian does: inline `#tag` markup in the body, and a `tags:`
list (or comma-separated string) in frontmatter properties.

Usage: extract_tags(body, properties) -> {"algorithms", "todo"}
Call parse_frontmatter() first to get (properties, body) -- this module
only extracts, it doesn't parse frontmatter itself.
"""
import re

# A tag starts with a letter (excludes bare "#123" and markdown headers,
# which are always "#" followed by a space) and continues with word
# characters, hyphens, or "/" for Obsidian-style nesting (#parent/child).
# The lookbehind stops mid-word "#" (e.g. inside a URL fragment ref like
# "foo#bar") -- doesn't fully cover a "#" in http://x.com/#section since
# "/" isn't a word char, but that's a minor false-positive shared with
# Obsidian's own tag parser and not worth over-engineering around.
TAG_PATTERN = re.compile(r"(?<!\w)#([A-Za-z][A-Za-z0-9_/-]*)")
CODE_FENCE_PATTERN = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_PATTERN = re.compile(r"`[^`\n]*`")


def extract_inline_tags(body: str) -> set[str]:
    """#tags in the body, skipped inside fenced or inline code so a
    shell-script snippet showing `#!/bin/bash` doesn't register a tag."""
    stripped = CODE_FENCE_PATTERN.sub("", body)
    stripped = INLINE_CODE_PATTERN.sub("", stripped)
    return {m.group(1).lower() for m in TAG_PATTERN.finditer(stripped)}


def extract_frontmatter_tags(properties: dict) -> set[str]:
    raw = properties.get("tags")
    if isinstance(raw, list):
        return {str(t).strip().lower() for t in raw if str(t).strip()}
    if isinstance(raw, str):
        return {t.strip().lower() for t in raw.split(",") if t.strip()}
    return set()


def extract_tags(body: str, properties: dict) -> set[str]:
    """Union of both sources. Tags are lowercased for dedup -- Obsidian
    treats #Project and #project as the same tag under the hood too."""
    return extract_inline_tags(body) | extract_frontmatter_tags(properties)
