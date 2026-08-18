"""
Parses/serializes Obsidian-style YAML frontmatter blocks
(`---\n...\n---`) at the top of chapter/journal markdown content.

Frontmatter lives IN the content string, same as Obsidian's plain-file
model -- there's no separate `properties` column. This keeps content as
the single source of truth (consistent with how wiki-links and semantic
search already treat it) and means raw edit mode always shows exactly
what's stored, frontmatter included.

Usage:
    properties, body = parse_frontmatter(content)
    new_content = serialize_frontmatter(properties, body)
"""
import re

import yaml

FRONTMATTER_PATTERN = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n)*", re.DOTALL)


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Returns (properties, body). If there's no frontmatter block, or it
    doesn't parse as a YAML mapping, properties is {} and body is the
    original content unchanged -- a malformed block is left alone rather
    than silently discarded."""
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return {}, content
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return {}, content
    if not isinstance(data, dict):
        return {}, content
    return data, content[match.end():]


def serialize_frontmatter(properties: dict, body: str) -> str:
    """Rebuilds content with a frontmatter block from `properties`, plus
    `body` unchanged. Empty properties means no block at all -- a chapter
    with no properties should round-trip as plain content, not grow a
    stray `---\n---\n`."""
    if not properties:
        return body
    yaml_block = yaml.safe_dump(properties, sort_keys=False, default_flow_style=False, allow_unicode=True).strip()
    return f"---\n{yaml_block}\n---\n\n{body}"
