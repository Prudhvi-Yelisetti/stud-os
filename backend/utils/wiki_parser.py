"""
Parses [[Chapter Title]] wiki-link syntax out of chapter markdown content.

Usage: extract_wiki_links("See [[DFS]] and [[BFS]]") -> ["DFS", "BFS"]
"""
import re

WIKI_LINK_PATTERN = re.compile(r"\[\[([^\[\]]+)\]\]")


def extract_wiki_links(content: str) -> list[str]:
    """Return the unique, order-preserved list of link targets in content.

    Strips a "#^block-id" block-reference suffix (see
    frontend/src/lib/blockRefs.ts for the matching frontend-side logic)
    before treating the bracketed text as a chapter title -- otherwise
    `[[Note#^abc123]]` would be parsed as linking to a chapter literally
    titled "Note#^abc123", which never exists, so the link would never
    resolve and no ChapterLink/graph edge/backlink would ever be created
    for it."""
    seen: set[str] = set()
    targets: list[str] = []
    for match in WIKI_LINK_PATTERN.finditer(content):
        title = match.group(1).strip()
        block_ref_index = title.find("#^")
        if block_ref_index != -1:
            title = title[:block_ref_index].strip()
        if title and title not in seen:
            seen.add(title)
            targets.append(title)
    return targets
