"""
Parses [[Chapter Title]] wiki-link syntax out of chapter markdown content.

Usage: extract_wiki_links("See [[DFS]] and [[BFS]]") -> ["DFS", "BFS"]
"""
import re

WIKI_LINK_PATTERN = re.compile(r"\[\[([^\[\]]+)\]\]")


def extract_wiki_links(content: str) -> list[str]:
    """Return the unique, order-preserved list of link targets in content."""
    seen: set[str] = set()
    targets: list[str] = []
    for match in WIKI_LINK_PATTERN.finditer(content):
        title = match.group(1).strip()
        if title and title not in seen:
            seen.add(title)
            targets.append(title)
    return targets
